"""gta6-twitch-ccu-forecast-01 entry: an empirical launch-curve forecaster.

A launch day's shape, as the ratio of each hour's viewers to hour 1's, is a
property of the launch's scale: a game whose first hour drew 800k (a rolling
midnight mega launch) stays comparatively flat, while one whose first hour
drew a few hundred (a global unlock later in the UTC day) ramps by orders of
magnitude. So this entry pools the release-day curves of the case's own
comparables, weighting each by a Gaussian kernel on the distance between its
log hour-1 viewers and the target's, and reads each hour's quantiles off the
weighted empirical distribution of log-ratios, with the spread narrowed
slightly (x0.9 in log space), as cross-validation favoured. Leave-one-out CV
over the kit's 37 comparable launches (the contest's pinball loss on the log
scale): 0.425 here vs the house persistence baseline's 0.930; on launches
with hour-1 >= 50k, 0.206 vs 0.251. Deterministic; falls back to the house
persistence formula if a case carried no usable comparable curve.
"""

import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]
SIGMA = 1.0        # kernel width on log hour-1 distance
FLOOR = 0.02       # minimum weight: every comparable keeps a small voice
SPREAD = 0.9       # log-space spread calibration around the median


def round2(x: float) -> float | int:
    """x rounded to 2 decimals, half up (as the starter's round2)."""
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if value.is_integer() else value


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def release_day(comp: dict) -> dict | None:
    """The comparable's release-day curve {hour index 0..23: viewers}, or None
    if it has no usable first hour (e.g. the pre-release GTA VI category)."""
    try:
        start = parse_ts(comp["day_start"])
        day = {}
        for point in comp["hourly"]:
            t = parse_ts(point["from"])
            if start <= t < start + timedelta(hours=24):
                day[int((t - start).total_seconds() // 3600)] = point["viewers"]
    except (KeyError, TypeError, ValueError):
        return None
    if not day.get(0) or day[0] <= 0 or len(day) < 12:
        return None
    return day


def weighted_quantile(pairs: list, tau: float) -> float:
    """Weighted quantile of (value, weight) pairs, linear in cumulative weight."""
    pairs = sorted(pairs)
    total = sum(w for _, w in pairs)
    target = tau * total
    acc = 0.0
    for i, (v, w) in enumerate(pairs):
        acc += w
        if acc >= target:
            if i == 0:
                return v
            prev_v = pairs[i - 1][0]
            frac = (target - (acc - w)) / w if w > 0 else 0.0
            return prev_v + (v - prev_v) * frac
    return pairs[-1][0]


def baseline_row(p1: float, h: int) -> list:
    return [round2(min(1e9, max(0.01, p1 * math.exp(z * 0.15 * math.sqrt(h - 1))))) for z in Z]


def forecast_case(case: dict) -> dict:
    first = next((k for k in case["known"] if k["hour"] == 1), None)
    p1 = max(1, first["viewers"]) if first else 1
    log_p1 = math.log(p1)

    pool = []  # (log hour-1 viewers, day curve)
    for comp in case.get("comparables") or []:
        day = release_day(comp)
        if day is not None:
            pool.append((math.log(day[0]), day))

    rows = []
    for spec in case["forecast"]:
        h = spec["hour"]
        idx = h - 1  # forecast hour 2 is the day's second hour (index 1)
        pairs = []
        for log_c1, day in pool:
            v = day.get(idx)
            if v and v > 0:
                w = math.exp(-((log_c1 - log_p1) ** 2) / (2 * SIGMA ** 2)) + FLOOR
                pairs.append((math.log(v) - log_c1, w))
        if not pairs:
            rows.append({"hour": h, "q": baseline_row(p1, h)})
            continue
        qs = [weighted_quantile(pairs, tau) for tau in LEVELS]
        med = qs[2]
        out = []
        for q in qs:
            val = p1 * math.exp(med + (q - med) * SPREAD)
            out.append(round2(min(1e9, max(0.01, val))))
        # Rounding must never break the non-decreasing order.
        for i in range(1, len(out)):
            if out[i] < out[i - 1]:
                out[i] = out[i - 1]
        rows.append({"hour": h, "q": out})
    return {"hours": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
