#!/usr/bin/env bash
# Launch one DREAM-RSI evolve invocation for a competition task.
#
#   TASK        task directory under tasks/ (default: vqcc_invsqrt)
#   ROUNDS, BRANCHES, REFINE, MAX_WORKERS, RESUME   run shape (see run_offpeak.py)
#   WORKSPACE   override the workspace dir (default: workspaces/<task minus vqcc_>)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source .env

TASK="${TASK:-vqcc_invsqrt}"
TASK_DIR="tasks/$TASK"
SHORT="${TASK#vqcc_}"
PROBLEM="${PROBLEM:-$TASK_DIR/$TASK.txt}"
EVALUATOR="${EVALUATOR:-$TASK_DIR/evaluator.py}"
INIT_PROGRAM="${INIT_PROGRAM:-$TASK_DIR/init_program.py}"

ROUNDS="${ROUNDS:-5}"
BRANCHES="${BRANCHES:-10}"
REFINE="${REFINE:-10}"
MAX_WORKERS="${MAX_WORKERS:-10}"
WORKSPACE="${WORKSPACE:-workspaces/$SHORT}"
RESUME="${RESUME:-0}"

for f in "$PROBLEM" "$EVALUATOR" "$INIT_PROGRAM"; do
  [ -f "$f" ] || { echo "[run_task] missing task file: $f" >&2; exit 2; }
done

start_cycle=0
from_stage=explore
if [ "$RESUME" = 1 ] && [ -d "$WORKSPACE" ]; then
  start_cycle="$(.venv/bin/python - "$WORKSPACE" <<'PY'
import sys
from pathlib import Path
ws = Path(sys.argv[1])
iters = sorted(p.name for p in (ws / 'history').glob('iter[0-9][0-9][0-9]') if p.is_dir())
print(len(iters))
PY
)"
  if [ -f "$WORKSPACE/live_cycle_manifest.json" ]; then
    from_stage=learning
  fi
  echo "[run_task] resuming $WORKSPACE at round $((start_cycle + 1)) ($from_stage)"
elif [ -e "$WORKSPACE" ]; then
  echo "[run_task] $WORKSPACE already exists; use RESUME=1" >&2
  exit 2
fi

.venv/bin/python -m dream_rsi evolve -w "$WORKSPACE" -a claude \
  --cycles "$ROUNDS" --start-cycle "$start_cycle" --from "$from_stage" \
  --branches "$BRANCHES" --refine "$REFINE" --max-workers "$MAX_WORKERS" \
  --explore-eval-timeout "$DRSI_EVAL_TIMEOUT_SEC" --no-explore-shell \
  --direction-mode off --discover-rounds 3 --eval-timeout 3600 \
  --target run_best --no-update-baseline-champion \
  --problem "$PROBLEM" --evaluator "$EVALUATOR" --init-program "$INIT_PROGRAM"
rc=$?
# evolve exits 1 when the FINAL learning step selects no policy; that is fine
# once every round is archived.
if [ "$rc" -eq 1 ] && [ -d "$WORKSPACE/history/$(printf 'iter%03d' $((ROUNDS - 1)))" ]; then
  echo "[run_task] final learning step selected no policy; all rounds complete"
  exit 0
fi
exit "$rc"
