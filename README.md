# kickmix-compiler

DREAM-RSI harness for the Kaggle competition **[Google Quantum AI — Verifiable
Quantum Circuit Compilation](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation)**.

A coding agent (Claude Code driven by **DeepSeek V4.1 Flash at low reasoning
effort**) writes quantum-circuit generator programs. Every candidate is scored
by the competition's own verifier, and **DREAM-RSI** evolves the *exploration
policy* that decides how the next attempts are spent (see
[arXiv:2609.14858](https://arxiv.org/abs/2609.14858) and
[google-research/dream-rsi](https://github.com/google-research/dream-rsi)).

**Current status (2026-10-23):**

| Task | Status | Best local score | Notes |
|---|---|---|---|
| `invsqrt` (Benchmark I) | solved once | **3.694×** over reference | Kaggle LB **1.54586** (rank ≈260/365; top 12.45) |
| `dqi` (Benchmark II) | **not started** | — | single `.kmb`; huge reference circuit |
| `dfthcsos` (Benchmark III) | **not started** | — | multi-file + classical co-design |

Details: [`RESULTS.md`](RESULTS.md), winning attempt in
[`results/vqcc_invsqrt/b0_a1/`](results/vqcc_invsqrt/b0_a1/).

> ⚠️ **Runs cost real money and CPU.** At the smoke-tested settings each agent
> attempt costs **$13–15** and its verification takes **20–30 min** of CPU on a
> loaded 56-core box. Everything is currently **paused** — see
> [Costs and cadence](#costs-cadence-and-safety) before launching anything.

---

## Contents

1. [How it works](#how-it-works)
2. [Repo layout](#repo-layout)
3. [Setup from scratch](#setup-from-scratch)
4. [Running DREAM-RSI](#running-dream-rsi)
5. [Submitting to Kaggle](#submitting-to-kaggle)
6. [Adding a new task (dqi, dfthcsos)](#adding-a-new-task)
7. [Costs, cadence, and safety](#costs-cadence-and-safety)
8. [Troubleshooting](#troubleshooting)

---

## How it works

**DREAM-RSI loop** (implemented by `dream-rsi/`, patched locally):

1. **Online rollout.** The current exploration policy (`method.py`, editable
   Python) chooses which tree nodes to explore. Each node is one agent attempt
   in its own directory; a fixed evaluator scores every attempt. A round is
   `BRANCHES × (REFINE + 1)` attempts.
2. **Offline dreaming.** After each round, an agent rewrites the policy and
   every rewrite is replayed on all recorded rounds; the best one (which may be
   the incumbent) drives the next round.

Only the policy evolves — the agent, the evaluator and the task stay fixed.

**Task contract** (`tasks/<task>/`):

| File | Role |
|---|---|
| `<task>.txt` | problem statement shown to the agent |
| `init_program.py` | starting program; design code sits between `EVOLVE-BLOCK` markers |
| `evaluator.py` | `evaluate(program_path) -> dict`; returns `combined_score` (higher = better, 0 = failed) |

The agent writes `artifact/program.py` in its attempt dir. That program must
**build the competition artifact** (e.g. `invsqrt.kmb`) when run as
`python program.py OUT.kmb`. The evaluator runs the official competition
verifier on the result and returns `REFERENCE_COST / measured_cost`, so the
reference submission scores exactly **1.0** and real improvements score >1.

**Isolation (anti-peeking / anti-cheat)** — important if you extend the
harness:

- Across rounds and branches, agents see only `proposal.md` + `eval/score.json`
  + `error.txt` of earlier attempts (`DRSI_HISTORY_SEED_MODE=pruned`), never
  their code. Within their own branch lineage they see everything (that is the
  REFINE mechanism).
- Each agent process runs inside a **bubblewrap mount namespace**
  (`scripts/claude_sandbox.sh`): read-only system/venv/`sandbox_share`/CLI;
  read-write only its branch dir. Other branches, past rounds' code, the
  verifier, evaluators, `.env` and `~/.kaggle` **do not exist** in that
  namespace. Red-team verified.
- The evaluator lives outside the workspace and passes a **fresh random
  `--salt`** to the verifier for every evaluation, so measurement outcomes
  cannot be gamed (the leaderboard uses its own secret salt).
- Every tool call is logged (`agent_log/claude/claude_messages*.jsonl`);
  `python scripts/audit_paths.py workspaces/<task>` flags escape attempts.

**Off-peak scheduling.** DeepSeek peak pricing is Mon–Fri **01:00–04:00** and
**06:00–10:00 UTC**, excluding Chinese public holidays; everything else is
off-peak. `scripts/run_offpeak.py` runs only in off-peak windows, interrupts at
a peak boundary, and resumes (`RESUME=1`) in the next window.

---

## Repo layout

```
tasks/vqcc_invsqrt/        # problem statement, initial builder, evaluator
results/vqcc_invsqrt/      # verified best attempt (program, proposal, score)
config/offpeak.json        # DeepSeek peak windows + CN holidays
patches/                   # local dream-rsi patches (applied by setup script)
scripts/
  setup_dream_rsi.sh       # clone dream-rsi @ pin + apply patches
  fetch_data.sh            # download competition dataset (resumable)
  run_task.sh              # one evolve invocation, TASK=vqcc_* (manual runs)
  run_offpeak.py           # off-peak scheduler (recommended entry point)
  offpeak.py               # peak-window logic (status helper)
  claude_sandbox.sh        # bwrap sandbox wrapper around the Claude Code CLI
  audit_paths.py           # scan agent logs for escape attempts
  make_submission.py       # rebuild best circuit + verify + zip
  kaggle_submit_lowlevel.py# start/finish Kaggle upload (IPv4-safe)
  llm_smoke.py             # one-query wiring test
dream-rsi/                 # upstream repo, patched (git-ignored)
vendor/kickmix/            # kickmix C++ source (Qualtran, Apache-2.0)
sandbox_share/             # read-only agent resources (selfcheck, API notes, paper)
data/                      # competition dataset (git-ignored)
workspaces/<task>/         # run state: history, scores, policies (git-ignored)
.env                       # your credentials/config (git-ignored — see .env.example)
.kaggle-token              # KGAT_ token (git-ignored)
```

`PROVENANCE.md` pins every third-party component and the measured reference
scores.

---

## Setup from scratch

Tested on Ubuntu 20.04, 56 cores, no root. Requirements: Linux x86-64,
Python ≥3.10 (3.12 used), `uv`, `git`, `curl`, `bwrap`, and the **Claude Code
CLI** (`claude`, e.g. `~/.local/bin/claude`) installed.

```bash
git clone git@github.com:somfieao/kickmix-compiler.git
cd kickmix-compiler

# 1. dream-rsi @ pinned commit + local patches
bash scripts/setup_dream_rsi.sh

# 2. Python env
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e "./dream-rsi[claude,tasks,dev]"
uv pip install --python .venv/bin/python kaggle requests pyyaml
```

### 3. Build kickmix (the circuit library the tasks use)

The competition ships a `kickmix.so` built for a newer glibc. On this box
(glibc 2.31) it fails with `GLIBC_2.34 not found`, so we build from source.
`vendor/kickmix` is the `kickmix/` directory of Qualtran `638777f`
(Apache-2.0).

kickmix needs **C++20**. If your system `g++` is ≥ 10/11 and your glibc is
modern, this one-liner is enough:

```bash
uv pip install --python .venv/bin/python --no-build-isolation ./vendor/kickmix
```

Otherwise (e.g. g++ 9.4 — what this box has), use a conda-forge toolchain
without root, and build on a scratch filesystem:

```bash
curl -sL https://micro.mamba.pm/api/micromamba/linux-64/latest -o /tmp/mm.tar.bz2
mkdir -p /tmp/mm && tar -xjf /tmp/mm.tar.bz2 -C /tmp/mm
MAMBA_ROOT_PREFIX=/tmp/opencode/mamba /tmp/mm/bin/micromamba create -y \
  -p /tmp/opencode/gxx13 -c conda-forge "gxx_linux-64=13"

uv pip install --python .venv/bin/python "pybind11==2.12.0" setuptools wheel
cp -r vendor/kickmix /tmp/opencode/kickmix-build
CC=/tmp/opencode/gxx13/bin/x86_64-conda-linux-gnu-cc \
CXX=/tmp/opencode/gxx13/bin/x86_64-conda-linux-gnu-g++ \
CXXFLAGS="-O2" LDFLAGS='-Wl,-rpath,$ORIGIN' \
uv pip install --python .venv/bin/python --no-build-isolation /tmp/opencode/kickmix-build
```

The wheel built by GCC 13 needs its newer `libstdc++` at runtime. We bundle it
and wrap the interpreter (`claude-agent-sdk` loads `numpy` before `kickmix`,
which otherwise pins the old system `libstdc++`):

```bash
SITE=.venv/lib/python3.12/site-packages
cp /tmp/opencode/gxx13/lib/libstdc++.so.6 "$SITE/libstdc++.so.6"
printf '#!/bin/sh\nexec env LD_PRELOAD="%s/%s/libstdc++.so.6" "%s/.venv/bin/python" "$@"\n' \
  "$PWD" "$SITE" "$PWD" > .venv/bin/python-km
chmod +x .venv/bin/python-km
.venv/bin/python-km -c "import numpy, kickmix; print('kickmix OK')"
```

`.venv/bin/python-km` is the interpreter used by `DRSI_EVAL_PYTHON` and by the
agents' self-checks. (If you built against a modern glibc/g++ you can skip the
preload, but keeping the wrapper costs nothing.)

Sanity check that your build reproduces the reference circuit bit-for-bit:

```bash
.venv/bin/python-km data/verifiers/invsqrt/nr_reference_circuit.py /tmp/nr.kmb
sha256sum /tmp/nr.kmb data/sample_submission/invsqrt.kmb   # digests must match
```

### 4. Competition data and secrets

```bash
echo 'KGAT_your_token' > .kaggle-token && chmod 600 .kaggle-token   # kaggle.com/settings/api
bash scripts/fetch_data.sh          # ~1 GB, resumable; >100MB files are moved to /tmp
cp .env.example .env && chmod 600 .env
$EDITOR .env                        # add your DeepSeek API key
```

`.env` wires the Claude agent to DeepSeek's Anthropic-compatible endpoint
(`ANTHROPIC_BASE_URL`, `DRSI_CLAUDE_MODEL=deepseek-flash`,
`DRSI_CLAUDE_EFFORT=low`) and the isolation/eval settings. If a model ID
changes, list the current IDs with:

```bash
curl -s https://api.deepseek.com/models -H "Authorization: Bearer $YOUR_KEY"
```

### 5. Verify the wiring

```bash
.venv/bin/python scripts/offpeak.py status      # off-peak window now?
.venv/bin/python scripts/llm_smoke.py           # one tiny agent turn (~$0.07)
.venv/bin/python tasks/vqcc_invsqrt/evaluator.py tasks/vqcc_invsqrt/init_program.py
#   -> combined_score must be 1.0 (reference vs reference); 4 min idle / ~25 min loaded
```

Optionally run dream-rsi's unit tests (no API calls):
`.venv/bin/python -m pytest dream-rsi/tests -q`

---

## Running DREAM-RSI

**Recommended (off-peak scheduler):**

```bash
nohup .venv/bin/python scripts/run_offpeak.py \
  --task vqcc_invsqrt --rounds 5 --branches 10 --refine 10 --max-workers 10 \
  > workspaces/console.log 2>&1 &
```

- Starts only in off-peak windows, interrupts at peak boundaries, resumes
  automatically.
- `touch workspaces/STOP` stops after the current attempt; delete to re-arm.
- Logs: `workspaces/scheduler.log`, `workspaces/console.log`.

**Manual (single invocation):**

```bash
TASK=vqcc_invsqrt ROUNDS=2 BRANCHES=4 REFINE=2 MAX_WORKERS=4 \
  bash scripts/run_task.sh
# re-entry after interruption:
TASK=vqcc_invsqrt ROUNDS=5 RESUME=1 bash scripts/run_task.sh
```

**Monitoring:**

```bash
# per-attempt status and score
for f in workspaces/invsqrt/explore_b*/attempt_*/meta.json; do
  python3 -c "import json;d=json.load(open('$f'));print(d['id'],d['status'])"; done
grep -h combined_score workspaces/invsqrt/explore_b*/attempt_*/eval/score.json

# policy learning history
ls workspaces/invsqrt/learning/iter*/heuristic_history

# isolation audit
.venv/bin/python scripts/audit_paths.py workspaces/invsqrt
```

Each attempt's directory holds `proposal.md`, `artifact/program.py`,
`eval/score.json`, and `agent_log/claude/` (streamed tool calls:
`claude_messages.partial.jsonl`, final summary `claude_messages.json`).

Expected pacing: 10 workers × (≈75 min agent + ≈25 min eval) ⇒ a
110-attempt round takes ~15 h; a weekend off-peak window (Fri 10:00 → Mon
01:00 UTC) fits ~3 paper-scale rounds.

---

## Submitting to Kaggle

```bash
.venv/bin/python scripts/make_submission.py   # best invsqrt + reference dqi/dfthcsos
```

This rebuilds the best circuit, (optionally) re-verifies it, and writes
`submission_invsqrt_<score>x.zip` (alias `submission.zip`). The upload **must**
be named `submission.zip`, and only 5 submissions/day are allowed (~45 min
scoring each).

> This host cannot reach `www.googleapis.com` (IPv6/egress blocked), which is
> where the Kaggle client sends uploads. Use the low-level path, which
> substitutes the reachable `storage.googleapis.com` host, forces IPv4, and
> uploads with curl:

```bash
ln -sf "$PWD/submission_invsqrt_3.69x.zip" /tmp/opencode/submission.zip
export KAGGLE_API_TOKEN=$(cat .kaggle-token)
.venv/bin/python scripts/kaggle_submit_lowlevel.py start /tmp/opencode/submission.zip /tmp/opencode/sess.json
python3 - <<'PY'
import json; s=json.load(open('/tmp/opencode/sess.json'))
json.dump({'url': s['url'].replace('https://www.googleapis.com/','https://storage.googleapis.com/'),
           'token': s['token']}, open('/tmp/opencode/sess_alt.json','w'))
PY
curl -4 -sS -T /tmp/opencode/submission.zip \
  "$(python3 -c "import json;print(json.load(open('/tmp/opencode/sess_alt.json'))['url'])")" \
  -o /tmp/opencode/upload.json -w 'HTTP %{http_code}\n'
.venv/bin/python scripts/kaggle_submit_lowlevel.py finish /tmp/opencode/sess.json "message"
```

Record submissions in `workspaces/submissions.log` (ref + expected score).

---

## Adding a new task

`dqi` and `dfthcsos` follow the same three-file contract. The dataset already
contains the authoritative verifiers and reference builders:

| Task | Verifier | Reference builder | Artifact(s) |
|---|---|---|---|
| `dqi` | `data/verifiers/dqi/verify_submission_dqi.py` | `dqi_reference_circuit.py` | `dqi.kmb` (886 MB reference) |
| `dfthcsos` | `data/verifiers/dfthcsos/verify.py` + `SCORING_README.md` | `example_submission/angle_k_reference_circuit.py` | `dfthcsos/angle_k_0..n-1.kmb` + `submission.npz` |

Costs (lower is better; the leaderboard uses the geometric mean of per-task
improvements): `dqi` = `R(ε₊) · Q² · T` (imperfect decoding is allowed and
traded off); `dfthcsos` = `λ_eff · T · Q`, with hard constraints: ≤128 qubits
per ANGLE circuit, Hamiltonian within 20 mHa, `Λ > 49.0`, `E_gap > 3.914898 Ha`.

**Steps (using `dqi` as the example):**

1. **Read the contract.** `sed -n '1,120p' data/verifiers/dqi/verify_submission_dqi.py`
   and `.venv/bin/python data/verifiers/dqi/verify_submission_dqi.py --help`.
   For `dfthcsos`, read `SCORING_README.md` (the authoritative spec) and the
   Kaggle *starter kit* dataset (`sohier/verifiable-circuit-compilation-starter-kit`),
   which builds a complete submission from the baseline in three steps.
2. **Measure the reference cost.** Run the verifier on
   `data/sample_submission/dqi.kmb`. That number is your `REFERENCE_SCORE`;
   by construction it makes the untouched reference score 1.0.
3. **Create the task dir.**
   ```bash
   mkdir -p tasks/vqcc_dqi
   cp data/verifiers/dqi/dqi_reference_circuit.py tasks/vqcc_dqi/init_program.py
   ```
   Adapt it like `tasks/vqcc_invsqrt/init_program.py`: keep a stable
   `build_circuit()` entry point, wrap the design code in
   `# EVOLVE-BLOCK-START/END`, and keep `main()` writing the artifact
   (`python program.py OUT.kmb`). Put a task-specific copy of the verifier
   docstring in `tasks/vqcc_dqi/vqcc_dqi.txt` and describe the artifact,
   cost formula, verification behavior, sandbox resources and the time budget
   (see the invsqrt statement as the template).
4. **Write the evaluator** by copying `tasks/vqcc_invsqrt/evaluator.py` and
   changing: `VERIFIER` path, artifact name/argv, `REFERENCE_SCORE`, and any
   verifier flags (keep a **fresh `secrets.token_hex(16)` salt per evaluation**
   if the verifier supports it). Keep the safety mechanics: build in a temp
   dir with a timeout, run the verifier in its own process group with
   `start_new_session=True` and kill the whole group on timeout
   (worker processes leak otherwise), return `REF/score` or 0.
5. **Give the sandbox what the builder legitimately needs.** Agents can only
   see `sandbox_share/` and `vendor/kickmix` (read-only) beyond their branch
   dir. For `dfthcsos`, add read-only binds in `scripts/claude_sandbox.sh`
   (e.g. a `sandbox_share/dfthcsos/` dir with the FCIDUMP and fixed shifts —
   *not* the verifier source), and mention the paths in the problem statement.
   Raise `VQCC_BUILD_TIMEOUT`/`DRSI_EVAL_TIMEOUT_SEC` if the build or
   verification is slower.
6. **Calibrate, then run small.** The untouched `init_program.py` must score
   ≈1.0 through your evaluator. Then:
   ```bash
   TASK=vqcc_dqi ROUNDS=1 BRANCHES=4 REFINE=2 MAX_WORKERS=4 bash scripts/run_task.sh
   ```
   and scale with `python scripts/run_offpeak.py --task vqcc_dqi ...`.
7. **Extend `scripts/make_submission.py`.** It currently assembles the best
   `invsqrt` circuit plus the *reference* `dqi`/`dfthcsos` placeholders
   (which is why the current LB score is just `invsqrt^(1/3)`). Once another
   task is producing candidates, take the best artifact from
   `workspaces/<task>/` instead of the placeholder. The zip layout is fixed:
   `invsqrt.kmb`, `dqi.kmb`, `dfthcsos/` — and the file must be named
   `submission.zip`.

Suggested order: **`dqi` first** (single artifact, verifier analogous to
invsqrt), then **`dfthcsos`** (multi-file, classical factorization/tree
co-design, heaviest evaluation).

---

## Costs, cadence, and safety

- **API spend:** ≈**$13–15 per successful attempt** (deepseek-flash, low
  effort, 90–100 turns). Timed-out attempts cost the same. A paper-scale round
  is 110 attempts ⇒ **$1.5k/round**. Decide a weekend ceiling *before*
  launching.
- **Off-peak only** (`config/offpeak.json`). Update `cn_public_holidays`
  (currently only 2027-01-01) when the Chinese State Council publishes the
  2027 schedule.
- **Kaggle:** 5 submissions/day, ~45 min scoring; winners must open-source
  their solution (Apache-2.0) — this repo and the harness are Apache-2.0
  compatible.
- **Disk:** runs write ~100–300 MB/round plus agent homes and a 900 MB
  submission zip. If `/home` is quota-limited, keep big files under `/tmp`
  (see `scripts/fetch_data.sh`) and watch `EDQUOT`: quota exhaustion corrupts
  in-flight attempts (the agent cannot write `proposal.md`), which still costs
  API money.
- **Secrets:** `.env` and `.kaggle-token` are git-ignored, `chmod 600`. The
  agent can see the DeepSeek key (its process env) but nothing else — never
  bind secrets into the sandbox. Rotate the Kaggle token if it leaks.
- **Audit:** `python scripts/audit_paths.py workspaces/<task>` after a night;
  repeated escape attempts fail the attempt by design, but review the report.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `ImportError: GLIBC_2.34 not found` | Use the competition `kickmix.so` only on glibc ≥2.34; otherwise build from `vendor/kickmix` (C++20). |
| `ImportError: GLIBCXX_3.4.32 not found` after `import numpy` | GCC-13 build needs its `libstdc++`; use `.venv/bin/python-km` (LD_PRELOAD) and copy the lib next to `kickmix*.so`. |
| `Claude Code not found at .../claude_sandbox.sh` | Set `DRSI_CLAUDE_CLI` (see `.env.example`) or re-run `scripts/setup_dream_rsi.sh` so the patched path resolves. |
| Agent writes fail with `EDQUOT` | Disk quota full; free space (or move large files to `/tmp`). In-flight attempts are lost and still billed. |
| Kaggle upload stuck at 0% | `www.googleapis.com` unreachable; use the low-level IPv4/`storage.googleapis.com` flow above. |
| `Submission files must be named "submission.zip"` | Rename/link the archive before uploading. |
| `evolve` exits 1 | Normal when the final learning step selects no policy but all rounds are archived. |
| `evolve` exits 2 | Learning exhausted its rewrite retries, or `WORKSPACE` exists without `RESUME=1`. Inspect `workspaces/<task>/learning/`. |
| Agent timeout (90 min) | Raise `CLAUDE_EXEC_TIMEOUT_SEC`, or tighten the "Time budget" section of the problem statement. |
| Verifier timeout | Raise `VQCC_VERIFY_TIMEOUT` / `DRSI_EVAL_TIMEOUT_SEC`, and lower `VQCC_VERIFY_WORKERS` on a loaded machine. |

---

## Licenses and provenance

Harness code: Apache-2.0. Vendored `kickmix` comes from Qualtran
(Apache-2.0) at the commit pinned in `PROVENANCE.md`. The competition dataset
and verifiers are subject to the
[competition rules](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/rules);
winning submissions must be licensed Apache-2.0.
