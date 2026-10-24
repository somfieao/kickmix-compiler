"""Invoke upstream CLI with per-invocation agent accounting and an access guard.

Runtime wrapper for the pinned upstream engine: per-invocation accounting, an
access guard and rate-limit retries, plus one local policy on top of the engine:
pruned history seeding (proposals + measured scores of earlier attempts, never
their code) when DRSI_HISTORY_SEED_MODE=pruned.
"""
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sys
import time

import backend_settings  # SDK configuration and exploration tool limits, not engine modification.
from key_pool import KeyPool, load_keys

from dream_rsi.agents.claude import ClaudeAgent
from dream_rsi.cli.main import main


# --------------------------------------------------------------------------
# Pruned history seeding (runtime override; upstream checkout stays clean).
# --------------------------------------------------------------------------
if os.environ.get("DRSI_HISTORY_SEED_MODE", "").strip().lower() == "pruned":
    from dream_rsi.exploration import history_seed as _hs

    _PRUNED_ATTEMPT_FILES = ("proposal.md", "meta.json", "error.txt")

    def _pruned_copy(archive, dst):
        dst.mkdir(parents=True, exist_ok=True)
        raw = archive / "raw_scores.json"
        if raw.is_file():
            shutil.copy2(raw, dst / raw.name)
        for attempt in sorted(archive.glob("explore_b*/attempt_*")):
            out = dst / attempt.relative_to(archive)
            out.mkdir(parents=True, exist_ok=True)
            for name in _PRUNED_ATTEMPT_FILES:
                src = attempt / name
                if src.is_file():
                    shutil.copy2(src, out / name)
            score = attempt / "eval" / "score.json"
            if score.is_file():
                (out / "eval").mkdir(exist_ok=True)
                shutil.copy2(score, out / "eval" / "score.json")

    def _seed_pruned(workspace, *, max_width=None, max_refine=None):
        archives = _hs.list_workspace_archives(workspace)
        if not archives:
            return []
        ws = Path(workspace).resolve()
        branches, _ = _hs.grid_limits(max_width=max_width, max_refine=max_refine)
        touched = []
        for branch in range(branches):
            branch_dir = ws / f"explore_b{branch}"
            dst_root = branch_dir / _hs.HISTORY_DIRNAME
            dst_root.mkdir(parents=True, exist_ok=True)
            for archive in archives:
                dst = dst_root / archive.name
                if dst.exists() or dst.is_symlink():
                    continue
                _pruned_copy(archive, dst)
            touched.append(str(branch_dir))
        print(f"[history_seed] pruned {len(archives)} archive(s) -> {len(touched)} branch(es) "
              f"(proposals + scores only)", flush=True)
        return touched

    _hs.seed_history_to_branches = _seed_pruned


# --------------------------------------------------------------------------
# Per-call accounting, provider-refusal guard, rate-limit retries.
# --------------------------------------------------------------------------
original_run = ClaudeAgent.run
# Provider refusals (credentials, model access, exhausted quota or balance) are
# not attempt outcomes. Rate limits and server errors are transient and excluded.
ACCESS_ERROR = re.compile(
    r"API Error: 40[123]\b|Failed to authenticate|team_model_access_denied|not allowed to access model"
    r"|invalid[ _-]?api[ _-]?key|insufficient[ _-]?(quota|balance)|quota[ _-]?exceeded|余额不足",
    re.IGNORECASE)
# A session that still fails on the provider's rate limit after the CLI's own
# retries is rerun on the same attempt after a growing pause, so throttling is
# never recorded as an attempt outcome.
RATE_LIMIT = re.compile(r"API Error: 429|\(429\)|rate[ _-]?limit|\[1302\]", re.IGNORECASE)
RATE_LIMIT_PAUSES = [120, 240, 360, 480, 600]
POOL_KEYS = load_keys()
# DRSI_KEY_POOL_STATE lets runs with separate accounting share one key's session cap.
POOL_STATE = Path(os.environ.get("DRSI_KEY_POOL_STATE")
                  or Path(os.environ["DRSI_AGENT_BUDGET_FILE"]).parent / "key-pool.json")
POOL = (KeyPool(POOL_KEYS, POOL_STATE, int(os.environ.get("DRSI_KEY_MAX_SESSIONS", "3")))
        if POOL_KEYS else None)


def stop_run(marker, reason):
    """Stop this run before upstream records a refused call as a failed attempt.

    Killing the launcher's process group leaves every unfinished attempt
    unmarked, so RESUME=1 retries exactly those attempts once access works.
    The marker also stops any other run sharing this accounting directory.
    """
    if not marker.exists():
        marker.write_text(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                      "pid": os.getpid(), "reason": reason[:2000]}, indent=2))
    print(f"[access-guard] provider refused the agent: {reason[:300]}\n"
          f"[access-guard] stopping this run; see {marker}. Restore access, then rerun with RESUME=1.",
          file=sys.stderr, flush=True)
    os.killpg(os.getpgid(0), signal.SIGKILL)


def counted_run(self, kwargs):
    budget = Path(os.environ["DRSI_AGENT_BUDGET_FILE"])
    budget.parent.mkdir(parents=True, exist_ok=True)
    marker = budget.parent / "ACCESS_ERROR.json"
    if marker.exists():
        stop_run(marker, "an earlier call was refused: " + marker.read_text())
    with budget.open("a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        state = json.loads(f.read() or '{"calls": 0}')
        state["calls"] += 1
        call = state["calls"]
        f.seek(0)
        f.truncate()
        json.dump(state, f)
    key_index = POOL.acquire() if POOL else None
    if POOL and key_index is None:
        stop_run(marker, "every key in the pool was refused")
    started = time.time()
    backend_settings.current.stage = kwargs.get("stage")
    backend_settings.current.node_dir = kwargs.get("node_dir")
    backend_settings.current.auth_token = POOL_KEYS[key_index] if POOL else None
    try:
        result = original_run(self, **kwargs)
    finally:
        backend_settings.current.stage = None
        backend_settings.current.node_dir = None
        backend_settings.current.auth_token = None
        if POOL:
            POOL.release(key_index)
    refused = result.status != "ok" and ACCESS_ERROR.search(result.message or "")
    logs = Path(kwargs["log_dir"])
    metrics = logs / "claude_messages.json"
    reported = json.loads(metrics.read_text()) if metrics.exists() else {}
    record = {"call": call, "backend": os.environ.get("DRSI_BACKEND", "deepseek_cli"),
              "model": os.environ.get("ANTHROPIC_MODEL"), "stage": kwargs.get("stage"),
              "status": result.status, "elapsed_seconds": time.time() - started,
              "log_dir": str(logs), "sdk_reported_cost_usd": reported.get("total_cost_usd"),
              "num_turns": reported.get("num_turns"), "key_index": key_index,
              "message": None if result.status == "ok" else (result.message or "")[:500],
              "note": "SDK cost estimates are not verified provider billing."}
    (budget.parent / f"agent-call-{call:02d}.json").write_text(json.dumps(record, indent=2))
    if refused and POOL:
        remaining = POOL.refuse(key_index, result.message)
        print(f"[access-guard] key {key_index} refused: {result.message[:200]}; {remaining} key(s) left",
              file=sys.stderr, flush=True)
        if remaining == 0:
            stop_run(marker, "every key in the pool was refused; last: " + result.message)
    elif refused:
        stop_run(marker, result.message)
    return result, bool(refused)


def bounded_run(self, **kwargs):
    if kwargs.get("stage") == "learning" and "OptimalPolicy" in kwargs.get("prompt", ""):
        project = Path(__file__).resolve().parents[1]
        kwargs["prompt"] += (
            "\n\nRuntime compatibility: the learning workspace contains a partial framework copy. "
            f"The complete read-only upstream framework is at {project / 'upstream/dream-rsi'}, "
            f"and the active Python executable is {sys.executable}. "
            "For an actual import check, run outside the partial package directory with PYTHONPATH "
            "pointing to the full upstream checkout and call dream_rsi.policy.load.load_policy_class "
            "on the absolute path of your method.py. Do not mock missing framework dependencies. "
            "The pinned dynamic policy loader cannot import dataclasses with postponed annotations; "
            "use ordinary classes with explicit __init__ instead. This is a runtime compatibility "
            "constraint; preserve the requested policy API and prefix-only behavior.\n"
        )
    pauses = iter(RATE_LIMIT_PAUSES)
    while True:
        result, refused = counted_run(self, kwargs)
        if refused:
            continue  # rerun the same attempt on another pool key
        if result.status == "ok" or not RATE_LIMIT.search(result.message or ""):
            return result
        pause = next(pauses, None)
        if pause is None:
            return result
        print(f"[rate-limit] {kwargs.get('stage')} session hit the provider rate limit; "
              f"rerunning the same attempt in {pause} s", file=sys.stderr, flush=True)
        time.sleep(pause)


ClaudeAgent.run = bounded_run
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
