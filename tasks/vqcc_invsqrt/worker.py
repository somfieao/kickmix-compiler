"""Task worker: build a candidate circuit and run the official verifier.

Two isolated execution modes, selected by VQCC_WORKER_MODE (host profile or
configs/vqcc.env):

  local  - `.worker-venv/bin/python-km` built by tasks/vqcc_invsqrt/setup.sh
  docker - the image built from Dockerfile.worker (glibc 2.39 + g++ 13 + kickmix)

The candidate program and the verifier always run in a throwaway directory
outside the repository. Timeouts kill the whole process group (the verifier
forks workers).
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
REPO = TASK_DIR.parents[1]
PROTOCOL = json.loads((TASK_DIR / "protocol.json").read_text())

REFERENCE_SCORE = float(PROTOCOL["reference_score"])
BUILD_TIMEOUT = float(PROTOCOL["timeouts"]["build_seconds"])
VERIFY_TIMEOUT = float(PROTOCOL["timeouts"]["verify_seconds"])
VERIFY_WORKERS = os.environ.get("VQCC_VERIFY_WORKERS", "8")
WORKER_MODE = os.environ.get("VQCC_WORKER_MODE", "local").strip().lower()

LOCAL_PYTHON = REPO / PROTOCOL["worker"]["local_venv"] / "bin" / "python-km"
VERIFIER = REPO / PROTOCOL["verifier"]
IMAGE = os.environ.get("VQCC_WORKER_IMAGE", "").strip()
ARTIFACT = PROTOCOL["artifact"]


def _run(cmd: list[str], *, cwd: Path, timeout: float) -> subprocess.CompletedProcess:
    proc = subprocess.Popen(
        cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass
        proc.wait()
        raise


def _docker_prefix(workdir: Path) -> list[str]:
    if not IMAGE:
        raise RuntimeError("VQCC_WORKER_MODE=docker but VQCC_WORKER_IMAGE is empty "
                           "(run tasks/vqcc_invsqrt/setup.sh --docker)")
    uid, gid = os.getuid(), os.getgid()
    return ["docker", "run", "--rm", "--network", "none", "--user", f"{uid}:{gid}",
            "-v", f"{workdir.resolve()}:/work", "-w", "/work", IMAGE]


def build_circuit(program: Path, workdir: Path) -> subprocess.CompletedProcess:
    """Run the candidate program; it must write <workdir>/<artifact>."""
    if WORKER_MODE == "docker":
        cmd = _docker_prefix(workdir) + ["/work/" + program.name, "/work/" + ARTIFACT]
    else:
        cmd = [str(LOCAL_PYTHON), str(program), str(workdir / ARTIFACT)]
    return _run(cmd, cwd=workdir, timeout=BUILD_TIMEOUT)


def verify_circuit(workdir: Path, salt: str) -> subprocess.CompletedProcess:
    """Run the official verifier on <workdir>/<artifact> with a fresh salt."""
    if WORKER_MODE == "docker":
        cmd = _docker_prefix(workdir) + [
            f"/verifier/invsqrt/{VERIFIER.name}", f"/work/{ARTIFACT}",
            "--salt", salt, "--max-workers", VERIFY_WORKERS,
        ]
    else:
        cmd = [str(LOCAL_PYTHON), str(VERIFIER), str(workdir / ARTIFACT),
               "--salt", salt, "--max-workers", VERIFY_WORKERS]
    return _run(cmd, cwd=workdir, timeout=VERIFY_TIMEOUT)
