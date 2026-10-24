# Provenance

| Component | Source | Pin |
|---|---|---|
| Dream-RSI | github.com/google-research/dream-rsi (Apache-2.0) | `8ec35bd2538220517ce1bfca4282db21b8c518db`, unmodified; local policy lives in `scripts/` runtime wrappers |
| kickmix source | github.com/quantumlib/Qualtran `kickmix/` (Apache-2.0) | tree `638777fac4379bc62e2a1e4a52cf1a1753895d48` |
| kickmix build | local worker: conda-forge g++ 13 (`/tmp/opencode/gxx13`) or system C++20 compiler; Docker worker: Ubuntu 24.04 + g++ 13 | rebuilt by `tasks/vqcc_invsqrt/setup.sh` |
| invsqrt verifier + reference | Kaggle `google-verifiable-quantum-circuit-compilation` dataset, downloaded by `scripts/fetch_data.sh` | 2026-10-23 |
| reference circuit | `data/sample_submission/invsqrt.kmb`, sha256 `e2bf8eb64350a4460a271fc7f1d591ef125b1e276377e9a0f64b96ab3ca321e1` — reproduced bit-for-bit by `tasks/vqcc_invsqrt/init_program.py` | |
| reference score | `2076774.233715282` (Q=260, C=7987.59, 200,540,928 shots) measured with the official verifier | |
| Kaggle submission | ref `57566416`, public score `1.54586` (invsqrt 3.694× + reference dqi/dfthcsos), see `RESULTS.md` | |
| Workflow | pinned-upstream bootstrap, launcher injection, per-call accounting and SDK read scoping, as implemented in this repository | |

Ignored, machine-local state: `.credentials/`, `configs/hosts/<hostname>.json`,
`upstream/`, `data/`, `runs/`, `.venv/`, `.worker-venv/`, `dist/`, `*.zip`.
