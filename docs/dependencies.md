# Pinned sources

| Component | Revision / source |
|---|---|
| Dream-RSI | `8ec35bd2538220517ce1bfca4282db21b8c518db` (github.com/google-research/dream-rsi) |
| kickmix (Qualtran) | tree `638777fac4379bc62e2a1e4a52cf1a1753895d48` (github.com/quantumlib/Qualtran `kickmix/`) |
| claude-agent-sdk | `0.1.50` (wrapper API used by `scripts/backend_settings.py`) |
| psutil | `7.0.0` |
| Competition data | Kaggle `google-verifiable-quantum-circuit-compilation` dataset, downloaded by `scripts/fetch_data.sh` |
| invsqrt reference circuit | `data/sample_submission/invsqrt.kmb`, sha256 `e2bf8eb6…3ca321e1`; reproduced bit-for-bit by the reference builder |
| invsqrt reference cost | `2076774.233715282` (Q=260, C=7987.59; measured with the official verifier) |
| DeepSeek official endpoint | `https://api.deepseek.com/anthropic`, model `deepseek-flash` (DeepSeek-V4.1-Flash, default effort `high`) |
| Paratera endpoint (optional) | `https://llmapi.paratera.com`, model `DeepSeek-V4.1-Flash-1017` |

`scripts/bootstrap.sh` fetches the two upstream checkouts into ignored
`upstream/` directories and verifies Dream-RSI is clean at its pin. The engine
runs from a uv `.venv`; the task worker runs either in a local uv venv
(`.worker-venv`) or in the Docker image built from
`tasks/vqcc_invsqrt/Dockerfile.worker`. Docker base tags and conda toolchains
can change: retain locally generated image IDs / wheel hashes with a campaign
if exact reproducibility is needed.
