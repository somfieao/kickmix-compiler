#!/usr/bin/env bash
# bwrap sandbox around the Claude Code CLI for dream-rsi agent runs.
#
# Invoked by claude-agent-sdk as the CLI (DRSI_CLAUDE_CLI). The SDK spawns this
# script with cwd = the agent's working directory:
#
#   exploration:  <workspace>/explore_bN       -> rw-bind ONLY that branch dir
#   learning:     <workspace>/learning/...     -> rw-bind the learning dir,
#                                                 ro-bind the whole workspace
#
# Everything else — other branches, history/, the task verifiers, evaluator,
# credentials (.env, kaggle token), the dream-rsi repo config — simply does not
# exist inside the mount namespace, so no tool (Read, Bash, ...) can reach it.
#
# Shared read-only resources (identical paths inside and outside):
#   $REPO/.venv          python + kickmix + numpy (use .venv/bin/python-km)
#   $REPO/sandbox_share  selfcheck.py, API notes, the benchmark paper
#   $REPO/dream-rsi      dream-rsi source (learning profile only)

set -euo pipefail

CWD="$(pwd)"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI_PATH="$(readlink -f "$(command -v claude)")"
CLI_DIR="$(dirname "$CLI_PATH")"
# The venv python is a symlink into uv's managed interpreter directory.
PY_REAL="$(readlink -f "$REPO/.venv/bin/python")"
PY_ROOT="$(dirname "$(dirname "$(dirname "$PY_REAL")")")"  # strip bin/python3.12
[ -d "$PY_ROOT" ] || PY_ROOT="/nonexistent"

HOME_DIR="$CWD/.agent_home"
mkdir -p "$HOME_DIR/.claude"

COMMON_BINDS=(
  --ro-bind /usr /usr
  --ro-bind-try /lib /lib
  --ro-bind-try /lib64 /lib64
  --symlink usr/bin /bin
  --symlink usr/sbin /sbin
  --ro-bind /etc /etc
  --ro-bind-try /run /run
  --ro-bind-try "$CLI_DIR" "$CLI_DIR"
  --ro-bind-try "$PY_ROOT" "$PY_ROOT"
  --ro-bind "$REPO/.venv" "$REPO/.venv"
  --ro-bind "$REPO/sandbox_share" "$REPO/sandbox_share"
  --ro-bind "$REPO/vendor/kickmix" "$REPO/vendor/kickmix"
  --proc /proc
  --dev /dev
  --tmpfs /tmp
  --tmpfs /run/user
  --die-with-parent
)

if [[ "$CWD" == */learning/* ]]; then
  # Offline policy learning: read-only view of the whole workspace (replay
  # worlds, scores, policies) plus a writable learning dir.
  WS="$CWD"
  while [[ "$(basename "$WS")" != "learning" && "$WS" != "/" ]]; do WS="$(dirname "$WS")"; done
  [[ "$WS" != "/" ]] || { echo "claude_sandbox: cannot locate workspace root from $CWD" >&2; exit 2; }
  WS="$(dirname "$WS")"
  PROFILE_BINDS=(
    --ro-bind "$WS" "$WS"
    --bind "$CWD" "$CWD"
    --ro-bind "$REPO/dream-rsi" "$REPO/dream-rsi"
  )
else
  # Exploration: only this branch's directory (its own attempts, the pruned
  # history/, baseline and problem.txt) is writable and visible.
  PROFILE_BINDS=( --bind "$CWD" "$CWD" )
fi

exec bwrap \
  "${COMMON_BINDS[@]}" \
  "${PROFILE_BINDS[@]}" \
  --setenv HOME "$HOME_DIR" \
  --setenv CLAUDE_CONFIG_DIR "$HOME_DIR/.claude" \
  --setenv PATH "/usr/bin:/bin:$REPO/.venv/bin" \
  "${CLAUDE_SANDBOX_CMD:-$CLI_PATH}" "$@"
