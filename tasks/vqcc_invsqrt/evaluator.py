"""Dream-RSI evaluator for the Kaggle VQCC `invsqrt` benchmark (Benchmark I).

Wraps the official competition verifier (data/verifiers/invsqrt/
verify_submission_invsqrt.py) behind the dream-rsi evaluator contract:

    evaluate(program_path) -> dict   # `combined_score`, higher is better

The candidate `program_path` must be a python script that writes the submission
circuit to a given output path (see tasks/vqcc_invsqrt/init_program.py).

Scoring:
  * The verifier runs every x in [1, 3133452] 64 times (200.5M shots) and
    reports cost `score = Q * (Toffolis + T/4)`; lower is better.
  * combined_score = REFERENCE_SCORE / verifier_score, so the official
    reference circuit scores exactly 1.0 and improvements score higher.
  * Any failure (build error, verifier reject, timeout) scores 0.0.

Anti-overfit: every evaluation passes a fresh cryptographically random
--salt to the verifier, so measurement-outcome seeds change between attempts
(the leaderboard uses its own secret salt).

All invocations use the `python-km` interpreter (LD_PRELOAD of the bundled
libstdc++) so the locally built kickmix extension loads in every subprocess.
"""

from __future__ import annotations

import json
import os
import resource
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_DIR.parents[1]
VERIFIER = REPO_ROOT / 'data' / 'verifiers' / 'invsqrt' / 'verify_submission_invsqrt.py'

# Measured with this exact verifier on sample_submission/invsqrt.kmb (which the
# reference builder reproduces bit-for-bit): Q=260, C=7987.59, 200,540,928
# verified shots. Deterministic for the data-independent reference circuit.
REFERENCE_SCORE = 2076774.233715282

BUILD_TIMEOUT_SEC = float(os.environ.get('VQCC_BUILD_TIMEOUT', '900'))
VERIFY_TIMEOUT_SEC = float(os.environ.get('VQCC_VERIFY_TIMEOUT', '1800'))
VERIFY_WORKERS = os.environ.get('VQCC_VERIFY_WORKERS', '8')
MEM_LIMIT_BYTES = 32 * 1024**3


def _limit_mem() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (MEM_LIMIT_BYTES, MEM_LIMIT_BYTES))


def _run(cmd: list[str], *, cwd: Path, timeout: float) -> subprocess.CompletedProcess:
    """Run cmd in its own process group; on timeout kill the whole group (the
    verifier forks worker processes that must not survive as orphans)."""
    import signal
    proc = subprocess.Popen(
        cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True, preexec_fn=_limit_mem,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass
        proc.wait()
        raise


def evaluate(program_path: str | Path) -> dict:
    program_path = Path(program_path).resolve()
    if not program_path.is_file():
        return {'combined_score': 0.0, 'error': f'program not found: {program_path}'}

    result: dict = {'program': str(program_path)}
    with tempfile.TemporaryDirectory(prefix='vqcc_invsqrt_') as tmp:
        tmp_dir = Path(tmp)
        circuit_file = tmp_dir / 'invsqrt.kmb'

        # 1. Build the candidate circuit from the agent's program.
        try:
            proc = _run([sys.executable, str(program_path), str(circuit_file)],
                        cwd=tmp_dir, timeout=BUILD_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            return {**result, 'combined_score': 0.0,
                    'error': f'build timed out after {BUILD_TIMEOUT_SEC:.0f}s'}
        if proc.returncode != 0 or not circuit_file.is_file():
            tail = (proc.stdout + '\n' + proc.stderr).strip()[-2000:]
            return {**result, 'combined_score': 0.0,
                    'error': f'build failed (exit {proc.returncode}): {tail}'}
        result['build_stdout_tail'] = proc.stdout.strip()[-500:]
        result['circuit_bytes'] = circuit_file.stat().st_size

        # 2. Verify with the official verifier under a fresh random salt.
        salt = secrets.token_hex(16)
        cmd = [sys.executable, str(VERIFIER), str(circuit_file),
               '--salt', salt, '--max-workers', VERIFY_WORKERS]
        try:
            proc = _run(cmd, cwd=tmp_dir, timeout=VERIFY_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            return {**result, 'combined_score': 0.0,
                    'error': f'verification timed out after {VERIFY_TIMEOUT_SEC:.0f}s'}

    # 3. Parse the verifier's JSON verdict (pretty-printed on stdout, PASS/FAIL).
    verdict = None
    text = (proc.stdout or '').strip()
    start = text.find('{')
    if start != -1:
        decoder = json.JSONDecoder()
        idx = start
        while idx != -1:
            try:
                obj, _ = decoder.raw_decode(text[idx:])
                if isinstance(obj, dict):
                    verdict = obj
                    break
            except json.JSONDecodeError:
                pass
            idx = text.find('{', idx + 1)
    if verdict is None:
        tail = (proc.stdout + '\n' + proc.stderr).strip()[-2000:]
        return {**result, 'combined_score': 0.0,
                'error': f'verifier produced no verdict (exit {proc.returncode}): {tail}'}

    if verdict.get('status') != 'PASS':
        return {**result, 'combined_score': 0.0,
                'error': f"verifier FAIL: {verdict.get('error', 'unknown error')}"}

    verifier_score = float(verdict['score'])
    combined = REFERENCE_SCORE / verifier_score
    keep = ('score', 'toffoli_equivalent', 'toffoli_count', 'max_toffoli_count', 't_count',
            'rotation_count', 'rotation_eps', 'num_qubits', 'reaction_depth', 'num_ops',
            'verified_shots', 'worst_error_over_tolerance', 'worst_x', 'circuit_sha256')
    return {
        **result,
        'combined_score': combined,
        'improvement_over_reference': combined,
        **{k: verdict[k] for k in keep if k in verdict},
    }


if __name__ == '__main__':
    print(json.dumps(evaluate(sys.argv[1]), indent=2, default=str))
