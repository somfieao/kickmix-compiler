# shellcheck shell=bash
# Upstream launch-script settings with vqcc_invsqrt added as a task.
# launch.sh places this file next to verbatim copies of the pinned upstream
# run_*.sh scripts, which source it instead of upstream's common.sh.
source "$DRSI_UPSTREAM/scripts/common.sh"

select_task() {
  TASK="$1"
  [ "$TASK" = vqcc_invsqrt ] || die "this launcher runs vqcc_invsqrt only (got '$TASK')"
  TASK_KIND=vqcc ROUNDS_DEFAULT=5 EVAL_TIMEOUT_DEFAULT=3000
  TASK_DIR="$DRSI_VQCC_TASK"
  PROBLEM="$TASK_DIR/vqcc_invsqrt.txt"
  INIT_PROGRAM="$TASK_DIR/init_program.py"
  EVALUATOR="$TASK_DIR/evaluator.py"
  EXPLORE_PROMPT="$REPO_ROOT/dream_rsi/prompts/explore.txt"
}

preflight() {
  local f
  for f in "$PROBLEM" "$EVALUATOR" "$INIT_PROGRAM" "$EXPLORE_PROMPT"; do
    [ -f "$f" ] || die "missing file: $f"
  done
  [ "$AGENT" = claude ] || die "the vqcc backends run through AGENT=claude (got '$AGENT')"
  "$PYTHON" -c "import claude_agent_sdk" 2>/dev/null || die "claude-agent-sdk is not installed"
  [ -x "$DRSI_CLAUDE_CLI" ] || die "Claude CLI not found: $DRSI_CLAUDE_CLI"
  [ -d "$DRSI_PROJECT/data/verifiers/invsqrt" ] || die "competition data missing; run scripts/fetch_data.sh"
  [ -f "$DRSI_PROJECT/data/sample_submission/invsqrt.kmb" ] || die "missing reference circuit"
  case "${VQCC_WORKER_MODE:-local}" in
    local)
      [ -x "$DRSI_PROJECT/.worker-venv/bin/python-km" ] || \
        die "missing .worker-venv; run bash tasks/vqcc_invsqrt/setup.sh"
      ;;
    docker)
      [ -n "${VQCC_WORKER_IMAGE:-}" ] || die "no vqcc_worker_image in the host profile"
      docker image inspect "$VQCC_WORKER_IMAGE" >/dev/null 2>&1 || \
        die "worker image missing: $VQCC_WORKER_IMAGE (run setup.sh --docker)"
      ;;
    *) die "VQCC_WORKER_MODE must be local or docker (got '$VQCC_WORKER_MODE')" ;;
  esac
  "$DRSI_REAL_PYTHON" - "$TASK_DIR" <<'PY' || die "task protocol check failed"
import json, sys
from pathlib import Path
protocol = json.loads((Path(sys.argv[1]) / "protocol.json").read_text())
assert protocol["reference_score"] > 0, "missing reference_score"
print(f"[preflight] reference_score={protocol['reference_score']:.3f}")
PY
}
