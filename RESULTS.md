# Results

## Kaggle — Google Quantum AI: Verifiable Quantum Circuit Compilation

Submission ref `57566416` (2026-10-23): **public leaderboard score 1.54586**
(rank ≈260 of 365 at submission time; top score 12.44962).

The zip contained our invsqrt circuit plus the reference `dqi` and `dfthcsos`
artifacts, so the leaderboard score equals `3.694^(1/3) = 1.5457` — matching
the local prediction and validating the local verifier ↔ leaderboard pipeline.

### invsqrt task (Benchmark I) — best attempt

`results/vqcc_invsqrt/b0_a1/` (one attempt of a 2×2 smoke round with
deepseek-flash at low effort):

| Metric | Reference (`sample_submission`) | b0_a1 | Improvement |
|---|---|---|---|
| Qubits | 260 | **166** | −36% |
| Mean Toffolis/shot | 7,735 | **3,141** | −59% |
| Rotation count | 37 | 36 | |
| Cost `Q*(T+T/4)` | 2,076,774.23 | **562,141.6** | **3.694×** |
| Worst error / tolerance | 0.477 | 0.471 | safe |

Verified on all 200,540,928 shots (64 × every x ∈ [1, 3,133,452]) with a fresh
random salt; circuit sha256 `38d90b45…2e02b`; cost breakdown in
`eval/score.json`. `proposal.md` records the agent's mechanism description.

## Sample run — workflow validation (2026-10-24)

Continued the existing `invsqrt` campaign under the pinned-upstream harness
(`tasks/vqcc_invsqrt/launch.sh dream_rsi`, DeepSeek-V4.1-Flash via the official
API, provider-default reasoning effort, 2 branches × 2 attempts, agent cap
5400 s):

- `b1_a0` re-run: 36 turns, $4.01, 11 min; the agent's new circuit failed
  verification (`x=2` phase error 0.5 turns) — a genuine attempt outcome.
- `b0_a0` re-run: failed at the 32k output-token cap (config raised to 128k
  afterwards).
- Offline learning: 3 policy rewrites + incumbent replay; `r0003` selected and
  promoted to `runs/vqcc_invsqrt/policy/method.py`.
- Round archived (`history/iter000`), best score 3.694×, exit 0.
- Agent accounting: **$15.91** total (4 successful calls).
- Permission red-team: own branch ALLOWED; sibling branch and workspace policy
  both DENIED (read scoping enforced by the SDK, not just the prompt).
