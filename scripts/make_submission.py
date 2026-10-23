"""Assemble a Kaggle submission zip for google-verifiable-quantum-circuit-compilation.

Takes the best-scoring invsqrt attempt across all rounds (by combined_score in
eval/score.json), rebuilds its circuit, re-verifies it with fresh salts, and
zips it together with the reference dqi / dfthcsos artifacts (which score 1.0
until we optimize those tasks).

Usage:
    python scripts/make_submission.py [--out submission.zip] [--salts 3]
                                       [--task invsqrt] [--skip-verify]
"""

from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO / 'workspaces' / 'invsqrt'
VERIFIER = REPO / 'data' / 'verifiers' / 'invsqrt' / 'verify_submission_invsqrt.py'
DATA = REPO / 'data'
PYTHON = REPO / '.venv' / 'bin' / 'python-km'
COMP = 'google-verifiable-quantum-circuit-compilation'


def best_attempt() -> tuple[float, Path] | None:
    best: tuple[float, Path] | None = None
    for score_file in sorted(WORKSPACE.rglob('eval/score.json')):
        if '.baseline' in score_file.parts:
            continue
        try:
            data = json.loads(score_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        score = data.get('combined_score', 0)
        if not isinstance(score, (int, float)) or score <= 0:
            continue
        node_dir = score_file.parent.parent
        if not (node_dir / 'artifact' / 'program.py').is_file():
            continue
        if best is None or score > best[0]:
            best = (float(score), node_dir)
    return best


def run(cmd: list[str], timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='submission.zip')
    parser.add_argument('--salts', type=int, default=3)
    parser.add_argument('--skip-verify', action='store_true')
    args = parser.parse_args()

    best = best_attempt()
    if best is None:
        print('no scored attempt found yet')
        return 1
    score, node_dir = best
    print(f'best attempt: {node_dir.relative_to(REPO)} (combined_score {score:.4f})')

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        circuit = tmp / 'invsqrt.kmb'
        proc = run([str(PYTHON), str(node_dir / 'artifact' / 'program.py'), str(circuit)], 1800)
        if proc.returncode != 0 or not circuit.is_file():
            print('circuit build failed:', proc.stdout[-500:], proc.stderr[-500:])
            return 1

        if not args.skip_verify:
            for i in range(args.salts):
                proc = run([str(PYTHON), str(VERIFIER), str(circuit),
                            '--salt', secrets.token_hex(16), '--max-workers', '16'], 5400)
                verdict = json.loads(proc.stdout[proc.stdout.find('{'):]) if '{' in proc.stdout else {}
                if verdict.get('status') != 'PASS':
                    print(f'salt {i}: FAIL {verdict.get("error")}')
                    return 1
                print(f'salt {i}: PASS score={verdict["score"]:.1f} '
                      f'(improvement {2076774.233715282 / verdict["score"]:.4f})')

        out = Path(args.out)
        sample_root = (DATA / 'sample_submission').resolve()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as zf:
            zf.write(circuit, 'invsqrt.kmb')
            for f in sorted(sample_root.rglob('*')):
                if f.is_file() and f.name != 'invsqrt.kmb':
                    zf.write(f, f.relative_to(sample_root))
    print(f'wrote {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
