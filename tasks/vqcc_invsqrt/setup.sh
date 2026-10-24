#!/usr/bin/env bash
# Build the task worker environment.
#
#   bash tasks/vqcc_invsqrt/setup.sh            # auto: docker image if usable, else local venv
#   bash tasks/vqcc_invsqrt/setup.sh --local    # force local .worker-venv
#   bash tasks/vqcc_invsqrt/setup.sh --docker   # force a task worker image
#
# Local mode needs a C++20 compiler. If the system g++ is too old (e.g. 9.4),
# a conda-forge g++ toolchain is fetched without root into VQCC_GXX_ENV
# (default /tmp/opencode/gxx13) and its libstdc++ is bundled next to kickmix.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASK="$ROOT/tasks/vqcc_invsqrt"
source "$ROOT/configs/vqcc.env"

MODE="${1:-}"; MODE="${MODE#--}"
[ -n "$MODE" ] || MODE="${VQCC_WORKER_MODE:-auto}"
command -v uv >/dev/null || { echo 'Install uv first: https://docs.astral.sh/uv/' >&2; exit 1; }

docker_ok() { docker info >/dev/null 2>&1; }
if [ "$MODE" = auto ]; then
  if docker_ok; then MODE=docker; else MODE=local; fi
fi
echo "[setup] worker mode: $MODE"

# Data sanity (verifier + reference circuit + paper inputs).
[ -f "$ROOT/data/verifiers/invsqrt/verify_submission_invsqrt.py" ] || {
  echo '[setup] competition data missing; run scripts/fetch_data.sh first' >&2; exit 2; }
[ -f "$ROOT/data/sample_submission/invsqrt.kmb" ] || {
  echo '[setup] missing data/sample_submission/invsqrt.kmb' >&2; exit 2; }

if [ "$MODE" = docker ]; then
  docker_ok || { echo '[setup] docker is not usable by this account (daemon/permissions)' >&2; exit 2; }
  TAG="$(date -u +%Y%m%d)"
  IMAGE="kickmix-vqcc-invsqrt:$TAG"
  docker build -f "$TASK/Dockerfile.worker" -t "$IMAGE" "$ROOT"
  ID="$(docker image inspect --format '{{.Id}}' "$IMAGE")"
  "$ROOT/.venv/bin/python" - "$ID" "$IMAGE" <<'PY'
import json, socket, sys
from pathlib import Path
p = Path('configs/hosts') / (socket.gethostname().split('.')[0] + '.json')
p.parent.mkdir(parents=True, exist_ok=True)
profile = json.loads(p.read_text()) if p.exists() else {}
profile.update({'worker_mode': 'docker', 'vqcc_worker_image': sys.argv[1]})
p.write_text(json.dumps(profile, indent=2) + '\n')
print(f'[setup] worker image {sys.argv[2]} -> {sys.argv[1]}')
PY
  echo '[setup] docker worker ready'
  exit 0
fi

# ---------------------------------------------------------------- local mode
VENV="$ROOT/.worker-venv"
[ -x "$VENV/bin/python" ] || uv venv --seed --python 3.12 "$VENV"
uv pip install -q --python "$VENV/bin/python" numpy "pybind11==2.12.0" setuptools wheel

SITE="$("$VENV/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
if [ ! -f "$SITE/kickmix.cpython-312-x86_64-linux-gnu.so" ]; then
  # Pick a C++20 compiler: system g++ if it passes a concepts probe, else conda.
  CXX=""
  if printf '#include <concepts>\ntemplate<class T> concept C = true;\nint main(){}\n' \
       | g++ -std=c++20 -x c++ - -o /tmp/kickmix_probe.out >/dev/null 2>&1; then
    CXX=g++
  fi
  GXX_ENV="${VQCC_GXX_ENV:-/tmp/opencode/gxx13}"
  if [ -z "$CXX" ] || [ ! -x "$GXX_ENV/bin/x86_64-conda-linux-gnu-g++" ]; then
    if [ ! -x "$GXX_ENV/bin/x86_64-conda-linux-gnu-g++" ]; then
      echo "[setup] fetching conda-forge g++ 13 into $GXX_ENV (no root)"
      mkdir -p /tmp/kickmix-mm
      curl -sL https://micro.mamba.pm/api/micromamba/linux-64/latest -o /tmp/kickmix-mm/mm.tar.bz2
      tar -xjf /tmp/kickmix-mm/mm.tar.bz2 -C /tmp/kickmix-mm
      MAMBA_ROOT_PREFIX=/tmp/kickmix-mm/root /tmp/kickmix-mm/bin/micromamba create -y \
        -p "$GXX_ENV" -c conda-forge "gxx_linux-64=13"
    fi
    CXX="$GXX_ENV/bin/x86_64-conda-linux-gnu-g++"
  fi
  CC="${CXX%g++}gcc"
  BUILD=/tmp/opencode/kickmix-build
  rm -rf "$BUILD"; cp -r "$ROOT/upstream/kickmix" "$BUILD"
  echo "[setup] building kickmix with $CXX"
  CC="$CC" CXX="$CXX" CXXFLAGS="-O2" LDFLAGS='-Wl,-rpath,$ORIGIN' \
    uv pip install -q --python "$VENV/bin/python" --no-build-isolation "$BUILD"
  # Bundle the toolchain's libstdc++ (numpy pins the old system one first).
  cp "$(dirname "$CXX")/../lib/libstdc++.so.6" "$SITE/libstdc++.so.6" 2>/dev/null || true
fi

# Interpreter wrapper: preload the bundled libstdc++ when present.
PRELOAD=""
[ -f "$SITE/libstdc++.so.6" ] && PRELOAD="LD_PRELOAD=$SITE/libstdc++.so.6"
printf '#!/bin/sh\nexec env %s "%s" "$@"\n' "$PRELOAD" "$VENV/bin/python" > "$VENV/bin/python-km"
chmod +x "$VENV/bin/python-km"

# Sanity: kickmix imports with numpy, and the reference circuit reproduces.
"$VENV/bin/python-km" - <<'PY'
import numpy, kickmix
print('[setup] kickmix OK:', kickmix.__file__)
PY
REF_SHA="$("$ROOT/.venv/bin/python" -c "import json;print(json.load(open('$TASK/protocol.json'))['reference_sha256'])")"
"$VENV/bin/python-km" "$ROOT/data/verifiers/invsqrt/nr_reference_circuit.py" /tmp/kickmix_ref.kmb >/dev/null
GOT_SHA="$(sha256sum /tmp/kickmix_ref.kmb | cut -d' ' -f1)"
if [ "$GOT_SHA" = "$REF_SHA" ]; then
  echo "[setup] reference circuit reproduces ($REF_SHA)"
else
  echo "[setup] WARNING: reference circuit sha mismatch: $GOT_SHA != $REF_SHA" >&2
fi

"$ROOT/.venv/bin/python" - <<'PY'
import json, socket
from pathlib import Path
p = Path('configs/hosts') / (socket.gethostname().split('.')[0] + '.json')
profile = json.loads(p.read_text()) if p.exists() else {}
profile.setdefault('worker_mode', 'local')
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(profile, indent=2) + '\n')
print('[setup] local worker ready (.worker-venv)')
PY
