"""invsqrt circuit builder — QROM + Taylor phasing circuit.

For every x in [1, 2^22) the circuit applies the phase exp(2*pi*i/sqrt(x)) to
the 22-qubit register `x` and returns every scratch qubit to |0>.

Algorithm
---------
1. Normalise.  With s = number of leading zero *pairs* of x, m = x << 2s lies in
   [2^20, 2^22), so with M = m / 2^20 in [1,4)

        1/sqrt(x) = 2^(s-10) * M^(-1/2).

   s is produced as a 4-bit binary number straight from the leading-zero-pair
   flags: the flags are plain ANDs (20 Toffolis) and the thermometer -> binary
   conversion is a set of free CNOT parity trees.

2. Grid split.  m = i*2^w + delta, with i the top k=9 bits (a QROM address) and
   nu = delta/2^w in [0,1).  On cell i, M = (i+nu)*2^(2-k), hence

        M^(-1/2) = sum_j a_j(i) nu^j,
        a_j(i)   = (-1)^j (2j-1)!!/(2^j j!) i^(-(2j+1)/2) 2^((k-2)/2).

   A single QROM indexed by i fetches all four magnitudes at once: a QROM costs
   2^k Toffolis *independently of the target width*, so the whole coefficient
   set is one 510-Toffoli lookup, and the reverse lookup that clears it is
   nearly free.

3. Horner evaluation in the sign-safe (all-positive) form

        f = |a0| - nu (|a1| - nu (|a2| - nu |a3|))

   at fixed point 2^-Fp, with truncated schoolbook multiplications: for each bit
   of nu a row `nu_m & (top bits of the multiplicand)` is ANDed into a clean
   scratch, subtracted from the accumulator, and cleared again with the free
   measurement-based del_and.  The subtract has to span the *whole* accumulator
   (a narrow slice would swallow the borrow).

4. Phase.  The phase register P = f << s (F = Fp + 10 fractional bits) is
   denormalised with a 4-level barrel shift and phased bit by bit with
   Z_POW(2^(j-F+1)); 36 rotations, 3 of them Clifford.

5. Uncompute.  Everything is run backwards (the AND flags and the QROM come out
   with measurement-based del_and / del_lookup), which restores x and leaves
   every scratch qubit at |0>.  Plain `reset` is *not* usable here: the
   simulator's R instruction dephases, i.e. it multiplies the state by a random
   global phase, so only del_and-style measurement uncomputation is phase-safe.
"""

from __future__ import annotations

import argparse
import math
from fractions import Fraction

import kickmix as km

# EVOLVE-BLOCK-START

WIDTH = 22          # x register width
NP = 10             # benchmark instance (n_p)
K = 9               # QROM address bits (top bits of the normalised mantissa)
DEGREE = 3          # Taylor degree (truncation ~2^-30 relative)
FP = 29             # fixed-point scale of the polynomial evaluation
F = FP + NP         # phase register fractional bits
W = WIDTH - K       # in-cell offset bits (nu)


def _coefficient_magnitudes() -> list[list[int]]:
    """|a_j(i)| * 2^FP for every reachable grid index i (rows = j)."""
    g = 2.0 ** (2 - K)
    lo, hi = 1 << (K - 2), 1 << K
    mags = [[] for _ in range(DEGREE + 1)]
    for i in range(lo, hi):
        for j in range(DEGREE + 1):
            cj = math.factorial(2 * j) / (4.0**j * math.factorial(j) ** 2)
            mags[j].append(int(round(cj * i ** (-(2 * j + 1) / 2.0) * g**-0.5 * 2.0**FP)))
    return mags


def _qrom_table(mags: list[list[int]], widths: list[int]) -> list[int]:
    """Pack |a0| | |a1|<<w0 | |a2|<<(w0+w1) | ... into one QROM."""
    offsets, acc = [], 0
    for wd in widths:
        offsets.append(acc)
        acc += wd
    table = [0] * (1 << K)
    lo = 1 << (K - 2)
    for idx in range(len(mags[0])):
        v = 0
        for j in range(DEGREE + 1):
            v |= mags[j][idx] << offsets[j]
        table[lo + idx] = v
    return table


def _mul_rows(builder, inverse: bool, mul_bits, mult: km.array, acc: km.array,
              scratch: km.array) -> None:
    """acc -= nu*mult (forward) / acc += nu*mult (inverse), fixed point 2^-FP.

    nu = sum_m mul_bits[m] 2^-(m+1).  Row m ANDs mul_bits[m] with the
    multiplicand bits that land at or above the fixed-point unit, subtracts the
    row from `acc` over its full width (so the borrow propagates), then clears
    the scratch with the free del_and.
    """
    p = len(mult)
    order = range(len(mul_bits) - 1, -1, -1) if inverse else range(len(mul_bits))
    for m in order:
        lo = W - m
        if lo >= p:
            continue
        width = p - lo
        builder.init_and(mul_bits[m], mult[lo:p], scratch[:width])
        if inverse:
            builder.iadd(scratch[:len(acc)], target=acc)
        else:
            builder.isub(scratch[:len(acc)], target=acc)
        builder.del_and(mul_bits[m], mult[lo:p], scratch[:width])


def _xor_leading_zero_pairs(builder, x: km.array, s: km.array) -> None:
    """XOR s with the number of leading zero *pairs* of x.

    z[k] = "pair k of x is 00", t[k] = "s >= k".  The thermometer -> binary map
    is bit_j(s) = parity of {k : bit_j(k) set} of (t[k] - t[k+1]), which for
    monotone t collapses to a few CNOTs.  All flags are ANDs and are cleared
    with the free del_and.  The CNOT tree is its own inverse, so calling this
    twice returns s to zero.
    """
    z = builder.alloc_qubits(11)
    t = builder.alloc_qubits(11)
    for k in range(11):
        pair = x[2 * k:2 * k + 2]
        builder.x(pair)
        builder.init_and(pair[0], pair[1], z[k])
        builder.x(pair)
    builder.cx(z[10], t[1])
    for k in range(2, 11):
        builder.init_and(t[k - 1], z[11 - k], t[k])
    for k in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
        builder.cx(t[k], s[0])
    for k in (2, 4, 6, 8, 10):
        builder.cx(t[k], s[1])
    for k in (4, 8):
        builder.cx(t[k], s[2])
    builder.cx(t[8], s[3])
    for k in range(10, 1, -1):
        builder.del_and(t[k - 1], z[11 - k], t[k])
    builder.cx(z[10], t[1])
    for k in range(11):
        pair = x[2 * k:2 * k + 2]
        builder.x(pair)
        builder.del_and(pair[0], pair[1], z[k])
        builder.x(pair)
    builder.free(z)
    builder.free(t)


def build_circuit() -> km.Circuit:
    mags = _coefficient_magnitudes()
    widths = [max(1, max(v).bit_length()) for v in mags]
    w_a0, w_a1, w_a2, w_a3 = widths
    table = _qrom_table(mags, widths)

    builder = km.CircuitBuilder()
    x = builder.create_quantum_register(WIDTH, name='x')
    s = builder.alloc_qubits(4)

    # ---- forward ---------------------------------------------------------
    _xor_leading_zero_pairs(builder, x, s)           # s = leading zero pairs
    builder.left_rotate(x, 2, control=s[0])          # m = x << 2s
    builder.left_rotate(x, 4, control=s[1])
    builder.left_rotate(x, 8, control=s[2])
    builder.left_rotate(x, 16, control=s[3])

    P = builder.alloc_qubits(F)                      # phase register, f in low bits
    a1r = builder.alloc_qubits(w_a1)                 # |a1| -> u1
    a2r = builder.alloc_qubits(w_a2)                 # |a2| -> u2
    a3r = builder.alloc_qubits(w_a3)                 # |a3|
    target = km.array(list(P[:w_a0]) + list(a1r) + list(a2r) + list(a3r))
    builder.init_lookup(table=table, address=x[W:], target=target)
    nu = x[:W]

    scratch = builder.alloc_qubits(max(w_a0, w_a1, w_a2))
    _mul_rows(builder, False, nu, a3r, a2r, scratch)     # u2 = |a2| - nu|a3|
    _mul_rows(builder, False, nu, a2r, a1r, scratch)     # u1 = |a1| - nu u2
    _mul_rows(builder, False, nu, a1r, P[:w_a0], scratch)  # f  = |a0| - nu u1
    builder.free(scratch)

    builder.left_rotate(P, 1, control=s[0])           # P = f << s
    builder.left_rotate(P, 2, control=s[1])
    builder.left_rotate(P, 4, control=s[2])
    builder.left_rotate(P, 8, control=s[3])
    for j in range(F):
        builder.z_pow(P[j], Fraction(2) ** (j - F + 1))

    # ---- uncompute -------------------------------------------------------
    builder.right_rotate(P, 8, control=s[3])
    builder.right_rotate(P, 4, control=s[2])
    builder.right_rotate(P, 2, control=s[1])
    builder.right_rotate(P, 1, control=s[0])
    scratch = builder.alloc_qubits(max(w_a0, w_a1, w_a2))
    _mul_rows(builder, True, nu, a1r, P[:w_a0], scratch)
    _mul_rows(builder, True, nu, a2r, a1r, scratch)
    _mul_rows(builder, True, nu, a3r, a2r, scratch)
    builder.free(scratch)
    builder.del_lookup(table=table, address=x[W:], target=target)
    for reg in (P, a1r, a2r, a3r):
        builder.free(reg)
    builder.right_rotate(x, 16, control=s[3])
    builder.right_rotate(x, 8, control=s[2])
    builder.right_rotate(x, 4, control=s[1])
    builder.right_rotate(x, 2, control=s[0])
    _xor_leading_zero_pairs(builder, x, s)           # s -> 0
    builder.free(s)
    return builder.finish_circuit()


# EVOLVE-BLOCK-END


def main() -> None:
    parser = argparse.ArgumentParser(description='Build the invsqrt benchmark circuit.')
    parser.add_argument('output', help='Path of the .kmb (or .kmx) file to write.')
    parser.add_argument('--format', choices=('kmb', 'kmx'), default='kmb',
                        help="Output circuit format: 'kmb' (binary, default) or 'kmx' (text).")
    args = parser.parse_args()

    circuit = build_circuit()
    circuit.to_file(args.output, format=args.format)
    toffolis = circuit.operation_statistics().num_toffoli_like
    print(f'Wrote {args.output} ({args.format}): {toffolis:,} Toffolis, {circuit.num_qubits} qubits.')


if __name__ == '__main__':
    main()
