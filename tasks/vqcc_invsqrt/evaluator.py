"""Dream-RSI evaluator for the Kaggle VQCC `invsqrt` benchmark (Benchmark I).

Runs the candidate builder in the task worker (local venv or docker image),
then the official competition verifier under a fresh random salt, and returns

    combined_score = REFERENCE_SCORE / verifier_score

so the official reference circuit scores exactly 1.0 and improvements score
higher. Any failure (build error, verifier reject, timeout) scores 0.0.

The verifier checks every x in [1, 3133452] 64 times (200.5M shots): there is
no sampled test set to overfit. Salts only re-roll measurement outcomes.
"""

from __future__ import annotations

import json
import secrets
import sys
import tempfile
from pathlib import Path

from worker import (ARTIFACT, REFERENCE_SCORE, build_circuit, verify_circuit)

KEEP = ('score', 'toffoli_equivalent', 'toffoli_count', 'max_toffoli_count', 't_count',
        'rotation_count', 'rotation_eps', 'num_qubits', 'reaction_depth', 'num_ops',
        'verified_shots', 'worst_error_over_tolerance', 'worst_x', 'circuit_sha256')


def _json_tail(text: str) -> dict | None:
    """Parse the verifier's (pretty-printed) JSON verdict from stdout."""
    text = (text or '').strip()
    if not text:
        return None
    decoder = json.JSONDecoder()
    idx = text.find('{')
    while idx != -1:
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        idx = text.find('{', idx + 1)
    return None


def evaluate(program_path: str | Path) -> dict:
    program_path = Path(program_path).resolve()
    if not program_path.is_file():
        return {'combined_score': 0.0, 'error': f'program not found: {program_path}'}

    with tempfile.TemporaryDirectory(prefix='vqcc_invsqrt_') as tmp:
        work = Path(tmp)
        local_program = work / 'program.py'
        local_program.write_bytes(program_path.read_bytes())

        try:
            proc = build_circuit(local_program, work)
        except Exception as exc:  # including build timeout
            return {'combined_score': 0.0, 'error': f'build failed: {exc}'}
        if proc.returncode != 0 or not (work / ARTIFACT).is_file():
            tail = (proc.stdout + '\n' + proc.stderr).strip()[-2000:]
            return {'combined_score': 0.0,
                    'error': f'build failed (exit {proc.returncode}): {tail}'}

        result = {'build_stdout_tail': proc.stdout.strip()[-500:],
                  'circuit_bytes': (work / ARTIFACT).stat().st_size}
        salt = secrets.token_hex(16)
        try:
            proc = verify_circuit(work, salt)
        except Exception as exc:  # including verify timeout
            return {**result, 'combined_score': 0.0, 'error': f'verification failed: {exc}'}

    verdict = _json_tail(proc.stdout)
    if verdict is None:
        tail = (proc.stdout + '\n' + proc.stderr).strip()[-2000:]
        return {**result, 'combined_score': 0.0,
                'error': f'verifier produced no verdict (exit {proc.returncode}): {tail}'}
    if verdict.get('status') != 'PASS':
        return {**result, 'combined_score': 0.0,
                'error': f"verifier FAIL: {verdict.get('error', 'unknown error')}"}

    score = float(verdict['score'])
    combined = REFERENCE_SCORE / score
    return {**result, 'combined_score': combined,
            'improvement_over_reference': combined,
            **{k: verdict[k] for k in KEEP if k in verdict}}


if __name__ == '__main__':
    print(json.dumps(evaluate(sys.argv[1]), indent=2, default=str))
