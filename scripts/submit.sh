#!/usr/bin/env bash
# Submit submission.zip to Kaggle via the v1 API (Bearer token from .kaggle-token).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
TOKEN="$(cat .kaggle-token)"
FILE="${1:-submission.zip}"
MSG="${2:-"invsqrt $(date -u +%Y%m%dT%H%MZ)"}"
curl -s -m 600 -H "Authorization: Bearer $TOKEN" \
  -F "file=@${FILE}" -F "description=${MSG}" \
  "https://www.kaggle.com/api/v1/competitions/submissions/google-verifiable-quantum-circuit-compilation" \
  -w "\nHTTP %{http_code}\n"
