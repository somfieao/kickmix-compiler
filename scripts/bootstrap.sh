#!/usr/bin/env bash
# Install the engine: pin upstream checkouts, create the uv environment, record
# a host profile. Task data and the task worker are separate (see
# scripts/fetch_data.sh and tasks/vqcc_invsqrt/setup.sh).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v uv >/dev/null || { echo 'Install uv first: https://docs.astral.sh/uv/' >&2; exit 1; }
command -v git >/dev/null || { echo 'Install git first.' >&2; exit 1; }
mkdir -p upstream configs/hosts .credentials runs docs

DREAM_RSI_PIN=8ec35bd2538220517ce1bfca4282db21b8c518db

# Dream-RSI: clean, pinned upstream checkout (runtime wrappers live in scripts/).
if [ ! -e upstream/dream-rsi ]; then
  git clone https://github.com/google-research/dream-rsi.git upstream/dream-rsi
fi
if [ "$(git -C upstream/dream-rsi rev-parse HEAD)" != "$DREAM_RSI_PIN" ]; then
  test -z "$(git -C upstream/dream-rsi status --porcelain)" || {
    echo 'Refusing to modify a dirty upstream/dream-rsi; move your changes out first.' >&2; exit 1; }
  git -C upstream/dream-rsi checkout --detach "$DREAM_RSI_PIN"
fi

# kickmix: Apache-2.0 C++ source from Qualtran. The pinned tree is fetched from
# the GitHub API (git 2.25 cannot sparse-clone it) and committed to upstream/.
KICKMIX_COMMIT=638777fac4379bc62e2a1e4a52cf1a1753895d48
if [ ! -f upstream/kickmix/setup.py ]; then
  echo "Fetching kickmix source from Qualtran @ $KICKMIX_COMMIT ..."
  python3 - "$KICKMIX_COMMIT" <<'PY'
import json, subprocess, sys, urllib.request
from pathlib import Path
commit = sys.argv[1]
root = Path('upstream/kickmix')
api = f'https://api.github.com/repos/quantumlib/Qualtran/git/trees/{commit}?recursive=1'
tree = json.load(urllib.request.urlopen(api, timeout=120))['tree']
files = [t for t in tree if t['type'] == 'blob' and t['path'].startswith('kickmix/')]
for t in files:
    out = root / t['path'][len('kickmix/'):]
    out.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://raw.githubusercontent.com/quantumlib/Qualtran/{commit}/{t['path']}"
    last = None
    for _ in range(5):
        try:
            data = urllib.request.urlopen(url, timeout=120).read()
            if len(data) == t['size']:
                out.write_bytes(data)
                break
        except OSError as exc:
            last = exc
    else:
        raise SystemExit(f'failed to fetch {t["path"]}: {last}')
print(f'kickmix: {len(files)} files')
PY
fi

uv python install 3.12
[ -x .venv/bin/python ] || uv venv --seed --python 3.12 .venv
# Pin claude-agent-sdk for the wrapper API used by scripts/backend_settings.py.
uv pip install --python .venv/bin/python -e 'upstream/dream-rsi[claude,dev]' \
  claude-agent-sdk==0.1.50 psutil==7.0.0 numpy
# Submission tooling (Kaggle upload/status).
uv pip install --python .venv/bin/python kaggle

command -v claude >/dev/null || {
  echo 'Install the Claude Code CLI before launching a search (claude on PATH).' >&2
  exit 1
}
.venv/bin/python - <<'PY'
import json, shutil, socket
from pathlib import Path
p = Path('configs/hosts') / (socket.gethostname().split('.')[0] + '.json')
if not p.exists():
    p.write_text(json.dumps({
        'claude_cli': shutil.which('claude'),
        'worker_mode': 'local',
        'vqcc_worker_image': '',
    }, indent=2) + '\n')
    print(f'wrote {p}')
else:
    print(f'host profile exists: {p}')
PY

echo
echo 'Next:'
echo '  cp configs/provider.env.example .credentials/deepseek.env && chmod 600 .credentials/deepseek.env'
echo '  bash scripts/fetch_data.sh'
echo '  bash tasks/vqcc_invsqrt/setup.sh'
