#!/usr/bin/env bash
# Reconstruct the vendored dream-rsi checkout with the local patches.
# dream-rsi/ is git-ignored in this repo; the pinned upstream commit and the
# local patch set are versioned here (see PROVENANCE.md).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
PIN=8ec35bd2538220517ce1bfca4282db21b8c518db

if [ ! -d dream-rsi/.git ]; then
  git clone https://github.com/google-research/dream-rsi.git dream-rsi
fi
git -C dream-rsi checkout "$PIN"
git -C dream-rsi apply ../patches/dream-rsi-local.patch
echo "dream-rsi ready at $PIN with local patches applied"
