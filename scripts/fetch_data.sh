#!/usr/bin/env bash
# Download the competition dataset files used by the harness (resumable).
#
# Requires .kaggle-token (a KGAT_ token from kaggle.com/settings/api).
# Files >100MB are moved to /tmp and symlinked back, to protect the shared
# /home quota; re-run this script if /tmp is wiped.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

TOKEN="$(cat .kaggle-token)"
COMP="google-verifiable-quantum-circuit-compilation"
BASE="https://www.kaggle.com/api/v1/competitions/data/download/$COMP"
STORE=/tmp/opencode/kcc_data
mkdir -p "$STORE"

files=(
  kickmix/kickmix.so
  kickmix/LICENSE.txt
  verifiers/LICENSE.txt
  verifiable_circuit_compilation.pdf
  verifiers/invsqrt/__init__.py
  verifiers/invsqrt/verify_submission_invsqrt.py
  verifiers/invsqrt/nr_reference_circuit.py
  verifiers/dqi/__init__.py
  verifiers/dqi/dqi_reference_circuit.py
  verifiers/dqi/verify_submission_dqi.py
  verifiers/dfthcsos/__init__.py
  verifiers/dfthcsos/SCORING_README.md
  verifiers/dfthcsos/verify.py
  verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py
  verifiers/dfthcsos/scoreinfra/__init__.py
  verifiers/dfthcsos/scoreinfra/circuits.py
  verifiers/dfthcsos/scoreinfra/costs_prepare.py
  verifiers/dfthcsos/scoreinfra/dfthc_math.py
  verifiers/dfthcsos/scoreinfra/reference.py
  verifiers/dfthcsos/FeMoCo76o113e.fcidump
  verifiers/dfthcsos/FeMoCo76o113e.fixed_shifts.npz
  sample_submission/invsqrt.kmb
  sample_submission/dqi.kmb
  sample_submission/dfthcsos/submission.npz
)
for i in $(seq 0 9); do
  files+=("sample_submission/dfthcsos/angle_k_$i.kmb")
done

for f in "${files[@]}"; do
  dest="data/$f"
  if [ -s "$dest" ]; then
    echo "skip  $f"
    continue
  fi
  mkdir -p "$(dirname "$dest")"
  enc="${f//\//%2F}"
  if curl -sS -L -m 3600 --retry 3 -C - -H "Authorization: Bearer $TOKEN" "$BASE/$enc" -o "$dest"; then
    echo "OK    $f  $(stat -c%s "$dest") bytes"
  else
    echo "FAIL  $f" >&2
  fi
done

# Keep big inputs off the quota-limited home filesystem.
while IFS= read -r -d '' f; do
  mkdir -p "$STORE/$(dirname "${f#data/}")"
  mv "$f" "$STORE/${f#data/}"
  ln -s "$STORE/${f#data/}" "$f"
  echo "moved $f -> $STORE/${f#data/}"
done < <(find data -type f -size +100M -print0)

echo "done. (restore placeholders from $STORE if /tmp is wiped)"
