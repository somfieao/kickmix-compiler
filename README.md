# kickmix-compiler

Task adapters for the original [Dream-RSI](https://github.com/google-research/dream-rsi)
engine, applied to the Kaggle competition
**[Google Quantum AI — Verifiable Quantum Circuit Compilation](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation)**.

A coding agent (Claude Code behind **DeepSeek V4.1 Flash**, provider-default
reasoning effort) writes quantum-circuit generator programs. Every candidate is
scored by the competition's own verifier, and Dream-RSI evolves the
*exploration policy* that decides how the next attempts are spent. The upstream
engine is pinned and left **unmodified**; all local policy lives in runtime
wrappers under `scripts/`.

This is a **fresh-start source distribution**: it contains no API keys,
experiment histories, learned controllers or discovered programs. Every
campaign starts at E0.

**Status (2026-10-23):**

| Task | Status | Best local score | Kaggle |
|---|---|---|---|
| `invsqrt` (Benchmark I) | validated | **3.694×** over reference | LB **1.54586** (ref placeholders for the other tasks) |
| `dqi` (Benchmark II) | not started | — | |
| `dfthcsos` (Benchmark III) | not started | — | |

See [`RESULTS.md`](RESULTS.md) and the verified winning attempt in
[`results/vqcc_invsqrt/b0_a1/`](results/vqcc_invsqrt/b0_a1/).

> **Runs are billable and slow.** One agent attempt costs ≈$13–15 and its
> verification takes 20–30 min of CPU on a loaded 56-core box. A paper-scale
> round (110 attempts) is ≈$1.5k. Decide a ceiling before launching.

## 1. Install the engine

Prerequisites: Git, [uv](https://docs.astral.sh/uv/), the Claude Code CLI
(`claude` on PATH), Docker (optional, for the task worker image), and — for
this competition — the Kaggle API token.

```bash
git clone git@github.com:somfieao/kickmix-compiler.git
cd kickmix-compiler
bash scripts/bootstrap.sh
```

Bootstrap pins `upstream/dream-rsi` at `8ec35bd` and fetches the Qualtran
`kickmix` source into `upstream/kickmix` (both ignored by Git; see
[`docs/dependencies.md`](docs/dependencies.md)). It then creates the uv `.venv`
(engine + pinned `claude-agent-sdk==0.1.50`) and writes your ignored host
profile `configs/hosts/<hostname>.json`.

## 2. Configure your own provider

```bash
cp configs/provider.env.example .credentials/deepseek.env
chmod 600 .credentials/deepseek.env
# Edit: set DEEPSEEK_BASE_URL, DEEPSEEK_API_KEY, DEEPSEEK_MODEL.
```

Two supported configurations:

| Provider | Base URL | Model |
|---|---|---|
| DeepSeek official | `https://api.deepseek.com/anthropic` | `deepseek-flash` (= DeepSeek-V4.1-Flash) |
| Paratera | `https://llmapi.paratera.com` | `DeepSeek-V4.1-Flash-1017` |

No reasoning-effort override is sent, so the provider's default applies
(DeepSeek-V4.1-Flash defaults to `high`). Set `DRSI_CLAUDE_EFFORT=low|high|max`
only to deviate.

Keys are never committed. `BACKEND=deepseek` is the only backend wired; a
`deepseek-keys.txt` pool (one key per line, separate accounts) is picked up if
present, with at most `DRSI_KEY_MAX_SESSIONS` concurrent sessions per key.

## 3. Prepare the task

```bash
echo 'KGAT_your_token' > .kaggle-token && chmod 600 .kaggle-token  # kaggle.com/settings/api
bash scripts/fetch_data.sh          # competition dataset (~1 GB, resumable; big files go to /tmp)
bash tasks/vqcc_invsqrt/setup.sh    # build the task worker
```

`fetch_data.sh` downloads the official verifiers, reference circuits and the
benchmark paper. `setup.sh` builds the **task worker** in one of two modes:

- **docker** (container-isolated): a local image from
  `tasks/vqcc_invsqrt/Dockerfile.worker` (Ubuntu 24.04, g++ 13, kickmix,
  verifier). Selected automatically when `docker info` works; recorded in your
  host profile. Requires Docker group access.
- **local** (fallback, and what this account currently uses): a `.worker-venv`
  with numpy + a locally built kickmix. If the system g++ lacks C++20 (e.g.
  9.4), setup fetches a conda-forge g++ 13 into `/tmp/opencode/gxx13`, bundles
  its `libstdc++`, and provides `.worker-venv/bin/python-km` (the interpreter
  used for candidate builds and verification).

Setup also reproduces the reference circuit bit-for-bit (sha256 check).

## 4. Run

Fresh campaign (E0 then the Dream-RSI loop, timestamped workspaces):

```bash
BACKEND=deepseek bash scripts/run_fresh.sh vqcc_invsqrt
```

Continue / resume a stable workspace (`runs/vqcc_invsqrt`):

```bash
bash tasks/vqcc_invsqrt/launch.sh dream_rsi                  # new or continue
RESUME=1 bash tasks/vqcc_invsqrt/launch.sh dream_rsi         # after an interruption
```

Stages and settings are the upstream environment variables:

```bash
ROUNDS=2 BRANCHES=3 REFINE=1 MAX_WORKERS=3 \
  bash tasks/vqcc_invsqrt/launch.sh dream_rsi                # small integration run
bash tasks/vqcc_invsqrt/launch.sh e0                         # E0 only
E0_WORKSPACE=runs/vqcc_invsqrt bash tasks/vqcc_invsqrt/launch.sh baseline
```

Defaults match the paper: 5 total rounds, 10 branches × 11 attempts, 10
workers, three controller rewrites per dreaming phase, 12000 s agent cap.

**Off-peak scheduler** (DeepSeek peak = Mon–Fri 01:00–04:00 and 06:00–10:00
UTC, excluding Chinese public holidays; update `configs/offpeak.json` when the
2027 schedule is published):

```bash
nohup .venv/bin/python scripts/run_offpeak.py --task vqcc_invsqrt \
  --rounds 5 --branches 10 --refine 10 --max-workers 10 \
  > runs/console.log 2>&1 &
touch runs/STOP        # stop after the current attempt
```

Where things land:

```
runs/vqcc_invsqrt/                     # stable workspace (RESUME target)
├── problem.txt   .baseline/           # seed program + its measured score
├── explore_bN/attempt_MM/             # proposal.md, artifact/program.py, eval/score.json
├── history/iterNNN/                   # archived rounds (replay worlds)
├── learning/iterNNN/heuristic_history # policy rewrites + replay results
└── policy/method.py                   # latest promoted exploration policy
runs/vqcc_invsqrt.config/<stamp>/      # exact task/model/launcher snapshot per start
runs/vqcc_invsqrt-accounting/          # one agent-call-NNN.json per session + ACCESS_ERROR.json
```

Per-call accounting is written by `scripts/run_bounded.py`
(`sdk_reported_cost_usd`, turns, stage). Provider refusals stop the run before
an attempt is recorded as failed; rate limits retry the same attempt with
growing pauses.

**Monitoring**

```bash
for f in runs/vqcc_invsqrt/explore_b*/attempt_*/meta.json; do
  python3 -c "import json;d=json.load(open('$f'));print(d['id'],d['status'])"; done
grep -h combined_score runs/vqcc_invsqrt/explore_b*/attempt_*/eval/score.json
ls runs/vqcc_invsqrt/learning/iter*/heuristic_history
```

## 5. Compatibility / design notes

- **Clean upstream.** `upstream/dream-rsi` is unmodified at its pin; the
  launcher refuses to run if `scripts/` or `dream_rsi/prompts` differ.
- **Provider + accounting wrappers.** `scripts/run_bounded.py` monkey-patches
  `ClaudeAgent.run` for per-call accounting, access-error stops and rate-limit
  retries; `scripts/backend_settings.py` monkey-patches `ClaudeAgentOptions`
  for the CLI path, 16 MiB SDK message buffer, and exploration scoping.
- **Exploration contract.** Exploration agents get file tools only
  (Read/Grep/Glob/Edit/Write) with `permission_mode=dontAsk`: reads are
  allow-list-scoped to their branch and its `history/`, writes to their
  attempt folder. Learning agents keep the upstream shell interface.
- **No cross-round code peeking.** `DRSI_HISTORY_SEED_MODE=pruned` seeds each
  branch with earlier rounds' `proposal.md` + `eval/score.json` + `error.txt`
  only (implemented as a runtime override in `run_bounded.py`).
- **No sampled-test overfitting.** The official verifier is exhaustive over all
  3,133,452 inputs (200.5M shots); every evaluation passes a fresh random
  `--salt`, which only re-rolls measurement outcomes.
- **Worker isolation.** Candidates and the verifier run in a throwaway
  directory, in a dedicated venv or container, with process-group timeouts
  (the verifier forks workers).

## 6. Checks

```bash
.venv/bin/python -m pytest upstream/dream-rsi/tests -q      # engine sanity
.venv/bin/python -c "import sys; sys.path.insert(0,'tasks/vqcc_invsqrt'); import evaluator"  # imports
tasks/vqcc_invsqrt/.worker-venv/bin/python-km tasks/vqcc_invsqrt/evaluator.py \
  tasks/vqcc_invsqrt/init_program.py     # must print combined_score ≈ 1.0 (~4 min idle)
.venv/bin/python scripts/preflight_keys.py                   # one 8-token request per key
.venv/bin/python scripts/offpeak.py status                   # window helper
```

## 7. Adding a new task (dqi, dfthcsos)

The dataset already contains the authoritative verifiers and reference
builders (see `scripts/fetch_data.sh`):

| Task | Verifier | Reference builder | Artifact(s) |
|---|---|---|---|
| `dqi` | `data/verifiers/dqi/verify_submission_dqi.py` | `dqi_reference_circuit.py` | `dqi.kmb` (886 MB reference) |
| `dfthcsos` | `data/verifiers/dfthcsos/verify.py` + `SCORING_README.md` | `example_submission/angle_k_reference_circuit.py` | `dfthcsos/angle_k_0..n-1.kmb` + `submission.npz` |

Costs: `dqi = R(ε₊)·Q²·T` (imperfect decoding allowed and traded off);
`dfthcsos = λ_eff·T·Q`, with ≤128 qubits per ANGLE circuit, Hamiltonian within
20 mHa, `Λ > 49.0`, `E_gap > 3.914898 Ha`.

Use `tasks/vqcc_invsqrt/` as the template:

1. **Read the contract.** `sed -n '1,120p' data/verifiers/<task>/…` and run the
   verifier `--help`. For `dfthcsos` also read `SCORING_README.md` and the
   Kaggle starter kit (`sohier/verifiable-circuit-compilation-starter-kit`),
   which builds a complete baseline submission.
2. **Create `tasks/vqcc_<task>/protocol.json`** with verifier path, artifact
   name, metric, reference score, timeouts and worker settings.
3. **Adapt the reference builder** to `init_program.py`: stable
   `build_circuit()` entry point, design code inside `EVOLVE-BLOCK` markers,
   `main()` writes the artifact (`python program.py OUT`).
4. **Add the evaluator** by copying `tasks/vqcc_invsqrt/{evaluator,worker}.py`
   and changing the verifier path, artifact name and flag set. Keep: throwaway
   build dir, fresh random salt, process-group timeouts, and
   `combined_score = REFERENCE_SCORE / cost`, 0 on any failure.
5. **Update the sandbox inputs.** Exploration reads are scoped to the branch;
   put anything the builder must read into the branch seed or the problem
   statement (never the verifier source).
6. **Add a launch + setup.** Copy `tasks/vqcc_invsqrt/{launch.sh,drsi/}` and
   rename the task in `drsi/common.sh`; extend `setup.sh` (docker or local
   worker) with the task's dependencies/data. Wire `--task` in
   `scripts/run_offpeak.py` if you want scheduling.
7. **Calibrate**: the untouched `init_program.py` must score ≈1.0 through the
   evaluator; then run small (`ROUNDS=1 BRANCHES=4 REFINE=2 MAX_WORKERS=4`).

## 8. Submitting to Kaggle

```bash
.venv/bin/python scripts/make_submission.py   # best invsqrt + reference dqi/dfthcsos
```

The archive **must be named `submission.zip`**, contains `invsqrt.kmb`,
`dqi.kmb`, `dfthcsos/`, and only 5 submissions/day are allowed (~45 min
scoring each). On hosts where `www.googleapis.com` is unreachable (as here),
use the IPv4/`storage.googleapis.com` upload path:

```bash
export KAGGLE_API_TOKEN=$(cat .kaggle-token)
.venv/bin/python scripts/kaggle_submit_lowlevel.py start submission.zip /tmp/sess.json
python3 - <<'PY'
import json; s=json.load(open('/tmp/sess.json'))
json.dump({'url': s['url'].replace('https://www.googleapis.com/','https://storage.googleapis.com/'),
           'token': s['token']}, open('/tmp/sess_alt.json','w'))
PY
curl -4 -sS -T submission.zip \
  "$(python3 -c "import json;print(json.load(open('/tmp/sess_alt.json'))['url'])")" \
  -o /tmp/upload.json -w 'HTTP %{http_code}\n'
.venv/bin/python scripts/kaggle_submit_lowlevel.py finish /tmp/sess.json "message"
```

Record submissions (ref + expected score) in `runs/submissions.log`.

## 9. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `upstream/dream-rsi is not at the pinned commit` | Run `scripts/bootstrap.sh`; never edit the upstream checkout. |
| `missing .worker-venv` | Run `bash tasks/vqcc_invsqrt/setup.sh`. |
| Docker permission denied | Add your account to the `docker` group (root) or run local mode (`bash tasks/vqcc_invsqrt/setup.sh --local`). |
| `kickmix` import fails with GLIBC/GLIBCXX | Use `--local` setup (bundles a conda-g++ build + libstdc++), or build the Docker worker. |
| Agent writes fail with `EDQUOT` | Disk quota full; free space (runs are still billed). Keep large files on `/tmp`. |
| Kaggle upload stuck at 0% | `www.googleapis.com` unreachable; use the IPv4/`storage.googleapis.com` flow. |
| `Submission files must be named "submission.zip"` | Rename the archive before uploading. |
| `evolve` exits 1 | Normal when the final learning step selects no policy but all rounds are archived. |
| `evolve` exits 2 | Learning exhausted its rewrite retries, or the workspace exists without `RESUME=1`. |
| Provider 401/402/403 | The run stops itself and writes `runs/vqcc_invsqrt-accounting/ACCESS_ERROR.json`; fix access, then rerun with `RESUME=1`. |
| `response exceeded the N output token maximum` | Raise `CLAUDE_CODE_MAX_OUTPUT_TOKENS` (128000 is set in `configs/vqcc.env`; the model supports far more). |

## Licenses and attribution

Original harness code: Apache-2.0 (see `LICENSE`). Dream-RSI and kickmix are
pinned upstream dependencies under Apache-2.0; competition data is subject to
the competition rules. See [`NOTICE`](NOTICE) and
[`PROVENANCE.md`](PROVENANCE.md). Winning competition submissions must be
licensed Apache-2.0.
