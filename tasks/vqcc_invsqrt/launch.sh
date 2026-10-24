#!/usr/bin/env bash
# DREAM-RSI on vqcc_invsqrt: runs the pinned upstream run_e0.sh,
# run_dream_rsi.sh or run_baseline.sh verbatim, with this task injected via
# tasks/vqcc_invsqrt/drsi/common.sh, the selected backend and per-call
# accounting. Settings are the upstream environment variables (ROUNDS,
# BRANCHES, REFINE, MAX_WORKERS, E0_WORKSPACE, RESUME, DRY_RUN, ...).
#
#   bash tasks/vqcc_invsqrt/launch.sh e0
#   E0_WORKSPACE=runs/vqcc_invsqrt-e0 bash tasks/vqcc_invsqrt/launch.sh dream_rsi
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASK="$ROOT/tasks/vqcc_invsqrt"
UPSTREAM="$ROOT/upstream/dream-rsi"
DREAM_RSI_PIN=8ec35bd2538220517ce1bfca4282db21b8c518db

case "${1:-}" in
  e0 | dream_rsi | baseline) METHOD="$1" ;;
  *) echo "usage: bash tasks/vqcc_invsqrt/launch.sh e0|dream_rsi|baseline" >&2; exit 2 ;;
esac
HOST="$(hostname -s)"

test "$(git -C "$UPSTREAM" rev-parse HEAD)" = "$DREAM_RSI_PIN" || {
  echo "upstream/dream-rsi is not at the pinned commit; run scripts/bootstrap.sh" >&2; exit 2; }
test -z "$(git -C "$UPSTREAM" status --porcelain -- scripts dream_rsi/prompts)" || {
  echo "upstream/dream-rsi scripts/prompts are modified; the distribution must stay clean" >&2; exit 2; }

source "$ROOT/configs/vqcc.env"
HOST_PROFILE="$ROOT/configs/hosts/$HOST.json"
if [ -f "$HOST_PROFILE" ]; then
  export DRSI_CLAUDE_CLI="$("$ROOT/.venv/bin/python" -c \
    'import json,sys; print(json.load(open(sys.argv[1])).get("claude_cli",""))' "$HOST_PROFILE")"
  export VQCC_WORKER_IMAGE="$("$ROOT/.venv/bin/python" -c \
    'import json,sys; print(json.load(open(sys.argv[1])).get("vqcc_worker_image",""))' "$HOST_PROFILE")"
  VQCC_WORKER_MODE="$("$ROOT/.venv/bin/python" -c \
    'import json,sys; print(json.load(open(sys.argv[1])).get("worker_mode","local"))' "$HOST_PROFILE")"
  export VQCC_WORKER_MODE
fi

# BACKEND selects the coding model behind the Claude CLI. Compared runs
# (E0, dream_rsi, baseline) must all use the same one.
BACKEND="${BACKEND:-deepseek}"
case "$BACKEND" in
  deepseek)
    if [ "${DRY_RUN:-0}" != 1 ]; then
      test -f "$ROOT/.credentials/deepseek.env" || {
        echo "Copy configs/provider.env.example to .credentials/deepseek.env and set your own credentials" >&2
        exit 2; }
      source "$ROOT/.credentials/deepseek.env"
    fi
    # Official DeepSeek API by default; Paratera's 1017 snapshot via credentials.
    ANTHROPIC_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com/anthropic}"
    ANTHROPIC_AUTH_TOKEN="${DEEPSEEK_API_KEY:-}"
    ANTHROPIC_MODEL="${DEEPSEEK_MODEL:-deepseek-flash}"
    export ANTHROPIC_SMALL_FAST_MODEL="$ANTHROPIC_MODEL" ANTHROPIC_DEFAULT_HAIKU_MODEL="$ANTHROPIC_MODEL" \
      ANTHROPIC_DEFAULT_SONNET_MODEL="$ANTHROPIC_MODEL" ANTHROPIC_DEFAULT_OPUS_MODEL="$ANTHROPIC_MODEL"
    export CLAUDE_CONFIG_DIR="$ROOT/.credentials/claude-deepseek"
    (umask 077; mkdir -p "$CLAUDE_CONFIG_DIR")
    SUFFIX=-deepseek
    ;;
  *) echo "BACKEND must be deepseek (got '$BACKEND')" >&2; exit 2 ;;
esac
export ANTHROPIC_BASE_URL ANTHROPIC_MODEL ANTHROPIC_AUTH_TOKEN
export DRSI_BACKEND="${BACKEND}_cli"
# Optional extra keys, one per line, from separate provider accounts (rate limits
# are per account); each key then serves at most DRSI_KEY_MAX_SESSIONS sessions.
if [ -f "$ROOT/.credentials/$BACKEND-keys.txt" ]; then
  export DRSI_KEY_POOL_FILE="$ROOT/.credentials/$BACKEND-keys.txt"
  export DRSI_KEY_MAX_SESSIONS="${DRSI_KEY_MAX_SESSIONS:-3}"
fi
unset ANTHROPIC_API_KEY HTTP_PROXY HTTPS_PROXY ALL_PROXY
export PATH="$ROOT/.venv/bin:$PATH"
export DRSI_AGENT_BUDGET_FILE="$ROOT/runs/vqcc_invsqrt-accounting/budget.json"
export DRSI_PROJECT="$ROOT" DRSI_UPSTREAM="$UPSTREAM" DRSI_VQCC_TASK="$TASK"
export DRSI_REAL_PYTHON="$ROOT/.venv/bin/python"
export PYTHON="$TASK/drsi/python"
# A single stable workspace keeps continuation (RESUME=1) simple; run_fresh.sh
# uses timestamped paths instead.
export WORKSPACE="${WORKSPACE:-$ROOT/runs/vqcc_invsqrt}"

STAGE="$(mktemp -d "${TMPDIR:-/tmp}/vqcc-drsi-launch.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
cp "$UPSTREAM/scripts/run_$METHOD.sh" "$STAGE/"
cp "$TASK/drsi/common.sh" "$STAGE/common.sh"

if [ "${DRY_RUN:-0}" != 1 ]; then
  # One-token requests first: a refused key would otherwise only stop the run
  # at its first agent call. Once one works, an earlier access stop is resolved.
  "$ROOT/.venv/bin/python" "$ROOT/scripts/preflight_keys.py" || {
    echo "error: no usable $BACKEND key" >&2; exit 2; }
  MARKER="$(dirname "$DRSI_AGENT_BUDGET_FILE")/ACCESS_ERROR.json"
  if [ -f "$MARKER" ]; then
    mv "$MARKER" "$MARKER.resolved-$(date -u +%Y%m%dT%H%M%SZ)"
    echo "[launch] $BACKEND access works again; earlier access stop marked resolved"
  fi

  # Record the exact task, backend and launcher of every start or resume.
  CONFIG="$WORKSPACE.config/$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p "$CONFIG"
  cp "$TASK/protocol.json" "$TASK/vqcc_invsqrt.txt" "$TASK/init_program.py" \
     "$TASK/evaluator.py" "$TASK/worker.py" "$TASK/launch.sh" "$TASK/Dockerfile.worker" \
     "$TASK/setup.sh" "$TASK/drsi/common.sh" "$ROOT/configs/vqcc.env" "$CONFIG/"
  if [ -f "$HOST_PROFILE" ]; then cp "$HOST_PROFILE" "$CONFIG/host.json"; fi
  git -C "$UPSTREAM" rev-parse HEAD > "$CONFIG/dream-rsi-commit"
  printf '%s\n' "$HOST" > "$CONFIG/hostname"
  printf '%s\n' "$ANTHROPIC_MODEL" > "$CONFIG/coding-model"
  printf '%s\n' "$BACKEND" > "$CONFIG/backend"
  env | grep -E '^(ROUNDS|BRANCHES|REFINE|MAX_WORKERS|EVAL_TIMEOUT|DISCOVER_[A-Z_]+|E0_WORKSPACE|RESUME|GUIDANCE|VQCC_[A-Z_]+)=' \
    > "$CONFIG/overrides.env" || true
fi

bash "$STAGE/run_$METHOD.sh" vqcc_invsqrt
