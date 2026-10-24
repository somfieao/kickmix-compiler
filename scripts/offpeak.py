"""DeepSeek off-peak window logic (peak pricing hours).

Peak = Monday-Friday (excluding Chinese public holidays) inside
[01:00, 04:00) or [06:00, 10:00) UTC. Everything else is off-peak,
including whole weekends and holidays.

CLI:
    python scripts/offpeak.py status   # print current window + next boundary
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / 'configs' / 'offpeak.json'


def _load() -> tuple[list[tuple[dt.time, dt.time]], set[str]]:
    data = json.loads(CONFIG.read_text())
    windows = []
    for a, b in data['peak_weekday_windows_utc']:
        ah, am = (int(x) for x in a.split(':'))
        bh, bm = (int(x) for x in b.split(':'))
        windows.append((dt.time(ah, am), dt.time(bh, bm)))
    return windows, set(data['cn_public_holidays'])


def is_peak(now: dt.datetime) -> bool:
    windows, holidays = _load()
    if now.date().isoformat() in holidays:
        return False
    if now.weekday() >= 5:  # Sat/Sun
        return False
    t = now.time()
    return any(a <= t < b for a, b in windows)


def next_transition(now: dt.datetime) -> dt.datetime:
    """The next minute at which is_peak flips (checked minute-by-minute)."""
    cur = is_peak(now)
    t = now.replace(second=0, microsecond=0) + dt.timedelta(minutes=1)
    for _ in range(60 * 24 * 4):
        if is_peak(t) != cur:
            return t
        t += dt.timedelta(minutes=1)
    return t


def main() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    state = 'PEAK (no runs)' if is_peak(now) else 'OFF-PEAK (runs allowed)'
    nxt = next_transition(now)
    delta = nxt - now
    hours, rem = divmod(int(delta.total_seconds()), 3600)
    minutes = rem // 60
    print(f'{now:%Y-%m-%d %H:%M UTC}: {state}; flips at {nxt:%Y-%m-%d %H:%M UTC} '
          f'(in {hours}h{minutes:02d}m)')


if __name__ == '__main__':
    sys.exit(main())
