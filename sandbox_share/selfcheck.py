"""Fast self-check for a built invsqrt circuit (development aid; not the grader).

Simulates a circuit on a sample of inputs and reports, per input, whether `x`
is restored, scratch is clean, and the phase error is within tolerance. Also
reports static circuit statistics (qubits, Toffolis, reaction depth).

The real verifier runs EVERY x in [1, 3133452] 64 times with a random salt;
passing here is necessary but NOT sufficient — always leave margin.

Usage:
  python-km selfcheck.py circuit.kmb [--n 1024] [--xs 1,2,3133452] [--seed 0]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from fractions import Fraction

import numpy as np

import kickmix as km

WIDTH = 22
MAX_X = 3 * (2**10 - 2)**2  # 3,133,452
PRECISION_BITS = 24
MASK64 = (1 << 64) - 1


def target_and_tol(xs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    num, den, shift = 1 << 130, 1, PRECISION_BITS + 1
    rs = [math.isqrt(num // (den * x)) for x in xs.tolist()]
    target = [((r + 1) >> 1) & MASK64 for r in rs]
    tol = [min(r >> shift, 1 << 63) for r in rs]
    return np.array(target, dtype=np.uint64), np.array(tol, dtype=np.uint64)


def half_turns_to_units(half_turns) -> int:
    n, d = Fraction(half_turns).as_integer_ratio()
    return (((n << 64) // d + 1) >> 1) & MASK64


def to_bits(values: np.ndarray, width: int) -> np.ndarray:
    return (values[None, :] >> np.arange(width, dtype=np.uint64)[:, None]) & 1 == 1


def from_bits(bits: np.ndarray) -> np.ndarray:
    return (bits.astype(np.uint64) << np.arange(len(bits), dtype=np.uint64)[:, None]).sum(axis=0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('circuit')
    parser.add_argument('--n', type=int, default=1024, help='Number of sampled inputs.')
    parser.add_argument('--xs', type=str, default='', help='Comma-separated explicit inputs.')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--batch-size', type=int, default=256)
    args = parser.parse_args()

    circuit = km.Circuit.from_file(args.circuit)
    registers = circuit.register_data
    if list(registers) != ['x']:
        print(json.dumps({'status': 'ERROR', 'error': f'invalid registers: {list(registers)}'}))
        sys.exit(1)
    x_reg = km.array(list(registers['x']))
    if len(x_reg) != WIDTH:
        print(json.dumps({'status': 'ERROR', 'error': f'expected {WIDTH} x qubits, got {len(x_reg)}'}))
        sys.exit(1)
    scratch = km.array([km.q(i) for i in range(circuit.num_qubits) if km.q(i) not in set(x_reg)])

    if args.xs:
        xs = np.array([int(v) for v in args.xs.split(',')], dtype=np.uint64)
    else:
        # Stratified sample: log-spaced values + uniform random values.
        rng = np.random.default_rng(args.seed)
        logs = np.unique(np.exp(np.linspace(np.log(1), np.log(MAX_X), args.n // 2)).astype(np.uint64))
        rand = rng.integers(1, MAX_X + 1, size=args.n - len(logs)).astype(np.uint64)
        xs = np.unique(np.concatenate([logs, rand]))

    target, tol = target_and_tol(xs)
    sim = km.Simulator(batch_size=args.batch_size, seed=args.seed, counting_operations=True)
    worst_ratio, worst_x = 0.0, 0
    failures = []
    for s in range(0, len(xs), args.batch_size):
        bx = xs[s:s + args.batch_size]
        n = len(bx)
        if n < args.batch_size:  # pad the tail batch; extras ignored below
            bx = np.concatenate([bx, np.full(args.batch_size - n, bx[-1], dtype=np.uint64)])
        sim.clear_for_shot()
        sim.write_across_shots(x_reg, to_bits(bx, WIDTH))
        sim.do(circuit)
        if not np.array_equal(from_bits(sim.read_across_shots(x_reg))[:n], xs[s:s + n]):
            failures.append({'x': int(xs[s]), 'error': 'x register not restored'})
            continue
        if len(scratch) and sim.read_across_shots(scratch).any(axis=1)[:n].any():
            failures.append({'x': int(xs[s]), 'error': 'scratch qubit not |0>'})
            continue
        theta = np.array([half_turns_to_units(sim.read_shot_phase(i)) for i in range(args.batch_size)],
                         dtype=np.uint64)[:n]
        err = (theta - target[s:s + n]).view(np.int64)
        used = np.abs(err).view(np.uint64)
        allowed = tol[s:s + n]
        ratio = np.divide(used, allowed, out=np.zeros(n), where=allowed > 0)
        i = int(np.argmax(ratio))
        if float(ratio[i]) > worst_ratio:
            worst_ratio, worst_x = float(ratio[i]), int(xs[s + i])
        bad = np.flatnonzero(used > allowed)
        for b in bad[:5]:
            failures.append({'x': int(xs[s + b]),
                             'error': f'phase error {int(err[b]) / 2**64:.3e} turns '
                                      f'exceeds tolerance {int(allowed[b]) / 2**64:.3e}'})

    stats = circuit.operation_statistics()
    print(json.dumps({
        'status': 'FAIL' if failures else 'OK_ON_SAMPLE',
        'sampled_inputs': int(len(xs)),
        'worst_error_over_tolerance': worst_ratio,
        'worst_x': worst_x,
        'num_qubits': circuit.num_qubits,
        'static_toffoli_like': int(stats.num_toffoli_like),
        'reaction_depth': circuit.reaction_depth(),
        'num_ops': len(circuit),
        'failures': failures[:10],
        'note': 'sampled check only; the grader tests every x with a fresh salt',
    }, indent=2))


if __name__ == '__main__':
    main()
