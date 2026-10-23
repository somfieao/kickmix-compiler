"""Off-peak scheduler wrapping scripts/run_task.sh.

Runs DREAM-RSI rounds only during DeepSeek off-peak hours (peak = Mon-Fri
01:00-04:00 and 06:00-10:00 UTC, excluding Chinese public holidays). At a peak
boundary the child process group gets SIGINT (DREAM-RSI checkpoints per round;
RESUME=1 continues), and the loop relaunches in the next off-peak window.

Stop: touch workspaces/STOP  (removed automatically on the next start).

Usage:
    python scripts/run_offpeak.py [--rounds 5] [--branches 10] [--refine 10]
                                  [--max-workers 10] [--max-hours 0]
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from offpeak import is_peak, next_transition  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
STOP_FILE = REPO / 'workspaces' / 'STOP'
LOG = REPO / 'workspaces' / 'scheduler.log'


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    LOG.write_text(LOG.read_text() + f'[{stamp}] {msg}\n') if LOG.exists() else \
        LOG.write_text(f'[{stamp}] {msg}\n')
    print(f'[{stamp}] {msg}', flush=True)


def run_once(env: dict[str, str], graceful_deadline: float | None) -> int:
    """Run run_task.sh in its own process group; SIGINT it at a peak boundary
    (or when graceful_deadline passes). Returns the exit code."""
    proc = subprocess.Popen(
        ['bash', str(REPO / 'scripts' / 'run_task.sh')],
        cwd=str(REPO), env=env, start_new_session=True,
    )
    interrupted = False
    try:
        while True:
            try:
                return proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                pass
            now = dt.datetime.now(dt.timezone.utc)
            deadline_hit = graceful_deadline is not None and time.time() > graceful_deadline
            if (is_peak(now) or deadline_hit or STOP_FILE.exists()) and not interrupted:
                log(f'stopping child ({"peak window" if is_peak(now) else "deadline/stop"})')
                interrupted = True
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGINT)
                except (ProcessLookupError, OSError):
                    pass
                grace = time.time() + 180
                while time.time() < grace:
                    try:
                        return proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        if time.time() > grace - 100:
                            try:
                                os.killpg(os.getpgid(proc.pid), signal.SIGINT)
                            except (ProcessLookupError, OSError):
                                pass
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
                return proc.wait()
    except BaseException:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--rounds', type=int, default=5)
    parser.add_argument('--branches', type=int, default=10)
    parser.add_argument('--refine', type=int, default=10)
    parser.add_argument('--max-workers', type=int, default=10)
    parser.add_argument('--max-hours', type=float, default=0,
                        help='stop launching new rounds after this many hours (0 = no cap)')
    args = parser.parse_args()

    if STOP_FILE.exists():
        STOP_FILE.unlink()
    env = os.environ.copy()
    env.update(ROUNDS=str(args.rounds), BRANCHES=str(args.branches),
               REFINE=str(args.refine), MAX_WORKERS=str(args.max_workers))
    t0 = time.time()

    while True:
        if STOP_FILE.exists():
            log('STOP file present; exiting')
            return 0
        now = dt.datetime.now(dt.timezone.utc)
        if is_peak(now):
            nxt = next_transition(now)
            wait_s = max(30.0, (nxt - now).total_seconds() + 30)
            log(f'peak window; sleeping {wait_s / 60:.0f} min until {nxt:%H:%M} UTC')
            time.sleep(wait_s)
            continue
        resume = '1' if (REPO / 'workspaces' / 'invsqrt').exists() else '0'
        env['RESUME'] = resume
        budget = None
        nxt = next_transition(now)
        if is_peak(nxt + dt.timedelta(minutes=1)):
            budget = (nxt - now).total_seconds()
        if args.max_hours > 0:
            remain = args.max_hours * 3600 - (time.time() - t0)
            budget = remain if budget is None else min(budget, remain)
            if remain <= 0:
                log('max-hours budget exhausted; exiting')
                return 0
        log(f'launching run_task.sh (RESUME={resume}, '
            f'budget={"none" if budget is None else f"{budget / 3600:.1f}h"})')
        rc = run_once(env, None if budget is None else time.time() + budget)
        log(f'run_task.sh exited rc={rc}')
        if rc == 0:
            log('all rounds complete')
            return 0
        time.sleep(30)


if __name__ == '__main__':
    main()
