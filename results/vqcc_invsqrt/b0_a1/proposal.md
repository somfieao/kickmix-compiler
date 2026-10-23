# Attempt 01 — QROM-indexed Taylor phasing circuit (compute + uncompute)

## Mechanism

Replace the reference Newton–Raphson pipeline with a **table-indexed Taylor
evaluation of the normalised mantissa**, and pay only three truncated
multiplications instead of six.

1. **Normalise without touching the arithmetic.** `s` = number of leading zero
   *pairs* of `x`, `m = x << 2s ∈ [2^20, 2^22)`, `M = m/2^20 ∈ [1,4)`, so
   `1/sqrt(x) = 2^(s-10) · M^(-1/2)`. `s` is generated **directly as 4 binary
   bits from the leading-zero flags**: the flags are plain ANDs (20 Toffolis)
   and the thermometer→binary map is a handful of free CNOT parity trees.
   `m` is produced by a 4-level **barrel** shift (58 Toffolis) that is undone
   later; no unary flags are kept alive.
2. **Grid split.** `m = i·2^w + δ`, `i` = top 9 bits = QROM address,
   `ν = δ/2^w`. Then `M^(-1/2) = Σ_j a_j(i) ν^j`, with coefficients that depend
   only on the grid cell. A **single QROM** fetches all four magnitudes; a QROM
   costs `2^k` Toffolis *independently of the target width* (measured: k=4 with
   a 90-bit target costs 14), so the whole 4-coefficient load is one
   510-Toffoli instruction, and the reverse (`del_lookup`) is ~50.
3. **Sign-safe Horner.** Because `a_1, a_3 < 0`, the chain is evaluated as
   `f = |a0| − ν(|a1| − ν(|a2| − ν|a3|))` — all intermediates positive, no
   two's complement. Each ν bit contributes a row `ν_m & (top bits of the
   multiplicand)` ANDed into a clean scratch, subtracted from the accumulator,
   then cleared with the free `del_and`. The subtract spans the **full
   accumulator width** (a narrow slice silently swallows the borrow — this was
   a real bug I had to find and fix), but only the accumulator's *significant*
   width: the last stage subtracts over the 30 bits of `|a0|` inside the
   39-bit phase register, not over the whole register (fixing that alone saved
   390 Toffolis and 11 qubits).
4. **Denormalise on the phase register.** `P = f << s` (F = Fp + 10 = 39
   fractional bits) via a 4-level barrel shift, then 39 `Z_POW`s
   (`2^(j-F+1)`), the three largest of which are Clifford.
5. **Uncompute in reverse** (`del_and`/`del_lookup` free-ish), restoring `x`
   and all scratch.

Parameters: `k = 9`, Taylor degree 3 (truncation ≈ 2^-30 relative), fixed point
`Fp = 29`. Measured circuit: **3,141 Toffolis, 166 qubits, 39 Z_POWs (36 T-costing)**
(654 ANDs + 1,456 adder Toffolis + 551 QROM/del_lookup + 480 CSWAP shifts).

## Evidence from history

Only two prior artefacts exist, and I read both in full:

* `baseline/proposal.md` + `baseline/eval/score.json` (identical to
  `baseline/init/`): score 1.0, Q = 260, 7,735 Toffolis, 37 rotations,
  worst error/tolerance 0.477. Its mechanism (read out of
  `baseline/artifact/program.py`) is: unary leading-zero flags, unary-lane
  controlled shifts of `x`, a hard-coded 4-interval minimax cubic whose
  coefficients are loaded by Clifford XORs, then one Newton–Raphson step
  (`y0²`, `M·y0²`, `y0·(3−My0²)`) — **six** truncated multiplications, 231
  static qubits (+29 adder ancillas).
* `attempt_00/error.txt`: `claude timeout after 3600.0s`, no `proposal.md`, no
  `eval/score.json`, no `artifact/`. Nothing to reuse; its work directory shows
  it was sweeping the same NR-family (`prog_v2/v3`, `sweep*`), i.e. exactly the
  local optimum this attempt deliberately leaves.

Measurements I made in this sandbox that shaped the design (all reproducible
with small circuits):

* `init_lookup` cost is `2^k - 2` and **independent of the target width**;
  `del_lookup` adds only ~10%. This is what makes a wide, fine-grained
  coefficient table affordable.
* `iadd` with a quantum offset costs `n-1` Toffolis with `n-2` ancillas, but
  the subtraction must span the whole target.
* **`R` dephases.** The simulator implements `R` as
  `phase ^= qubit & rng`, so resetting a dirty qubit (or `init_and` /
  `init_lookup` on a dirty target) injects a *random* global phase. I first
  built the much cheaper "compute-only, then reset all scratch" circuit
  (1,512 Toffolis, 131 qubits) and it failed with random ±0.5-turn phases; the
  cause is that line of the simulator, not the arithmetic. Consequence: any
  design must uncompute; `del_and`-style measurement uncomputation is the only
  free cleaning. This negative result is the main reason the cost is ~2× the
  forward pass.

## Why this is not a repeat

* Different approximation family: a **QROM-indexed Taylor expansion** instead
  of hard-coded cubic coefficients + a Newton step; **three** multiplications
  instead of six, and the Newton step disappears entirely (the table supplies
  the accuracy the cubic used to lack).
* Different exponent machinery: binary `s` from free CNOT parity trees on a
  thermometer, barrel shifts, instead of a unary flag register with ~10
  unary-controlled lane shifts per direction.
* Different data path: all-positive Horner form (no two's complement in the
  coefficient chain), one wide QROM load, truncated schoolbook rows over the
  full accumulator.
* 177 qubits vs 260, and the register budget is spread differently (a 73-bit
  coefficient set + 39-bit phase register instead of 68 bits of coefficients +
  a 40-bit output + 10 flags).

## Measured result (not yet graded)

| | reference | this attempt |
|---|---|---|
| qubits Q | 260 | **166** |
| Toffolis (mean = static) | 7,735 | **3,141** |
| rotations (non-Clifford) | 37 | 36 |
| worst error / tolerance | 0.477 | **0.34** (12k sampled x) |
| estimated score `Q(T + T_rot/4)` | 2.08e6 | **≈0.56e6** |

Estimate uses the reference's own rotation pricing (≈27.3 T per non-Clifford
rotation, T/4), i.e. ≈246 Toffoli-equivalents for the rotations. That is an
**estimated ≈3.1× improvement**; I have not run the grader, so I do not claim
a verified score. The estimate is 166·(3,141 + 983/4) ≈ 5.6e5.

Verification done locally: `selfcheck` on 12,000 stratified inputs
(worst ratio 0.337), explicit checks at the extremes (1, 2^20−1, 2^20, 2^20+1,
3,133,452) and at the model's worst-x candidates; x restored and scratch clean
on every sample; phases identical for six different measurement seeds (the
circuit is deterministic, so the verifier's fresh salt cannot flip it).

## Expected benefit and risk

* **Benefit:** ~2.2× fewer Toffolis and 1.5× fewer qubits than the reference,
  both multiplying. The error margin is looser than the reference's (0.34 vs
  0.48 sampled), and the physical error is *bounded*: three floor-truncations
  plus coefficient rounding give at most ~5 units of 2^-Fp ≈ 0.3 of tolerance,
  which is why Fp = 29 was chosen over the cheaper Fp = 28 (which measured 0.68
  worst on samples — too thin).
* **Risk 1 (dominant):** the QROM's `2^k` and the mandatory uncompute cap the
  remaining gain. A finer grid (k = 10/11) would allow degree 2, but I measured
  it to be strictly worse (score ≈615–666k, i.e. no better) because `2^k`
  doubles.
* **Risk 2:** sampled verification cannot cover all 3.1M inputs. The error is
  truncation-dominated and bounded, and the worst sampled value (0.34) sits
  well below 1.0; the model's exhaustive (all-x) sweep of the same integer
  algorithm tops out at 0.177 before the ~2-unit circuit/table offset.
* **Risk 3:** the rotation T-cost is modelled from the reference's
  `rotation_eps`; if the grader prices rotations more aggressively, the gain
  shrinks by a few percent (rotations are only ~6% of the cost).

## Ideas deliberately not taken (for the next attempt)

* Finer QROM (k ≥ 10) + quadratic: dominated by `2^k` at this table width.
* Compute-only + `reset`: killed by `R`'s dephasing (see above) — but note that
  a *classically-obtained* copy of a dirty qubit would make `del_and`-style
  cleaning possible; the API has no Z-basis measurement into a classical bit,
  so this road is closed.
* Reducing the 29-bit-wide final subtraction: a separate product register saves
  ~60 Toffolis per direction but costs 22 qubits, which is strictly worse in
  the `Q·T` metric (this trade-off is the main lever left: Q is the expensive
  resource here).
