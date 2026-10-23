# Provenance

| Component | Source | Pin |
|---|---|---|
| dream-rsi | github.com/google-research/dream-rsi (Apache-2.0) | 8ec35bd2538220517ce1bfca4282db21b8c518db + local patches (see `git diff` in dream-rsi/) |
| kickmix source | github.com/quantumlib/Qualtran `kickmix/` (Apache-2.0) | tree of commit 638777fac4379bc62e2a1e4a52cf1a1753895d48 (main) |
| kickmix build | g++ 13.4 (conda-forge gxx_linux-64) in /tmp/opencode/gxx13; wheel installed into .venv; libstdc++.so.6 (6.0.36) bundled next to kickmix*.so; `.venv/bin/python-km` LD_PRELOADs it | |
| invsqrt verifier + reference | Kaggle `google-verifiable-quantum-circuit-compilation` dataset (`verifiers/invsqrt/`) | downloaded 2026-10-23 |
| reference circuit | `data/sample_submission/invsqrt.kmb`, sha256 e2bf8eb64350a4460a271fc7f1d591ef125b1e276377e9a0f64b96ab3ca321e1 — reproduced bit-for-bit by `tasks/vqcc_invsqrt/init_program.py` | |
| reference score | 2076774.233715282 (Q=260, C=7987.59, 200,540,928 shots) measured with the official verifier | |
note: /tmp/opencode/sample_submission_store holds submission placeholders (re-download if /tmp is wiped)
