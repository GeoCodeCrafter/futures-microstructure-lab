"""
Studies 03-05 - session-level effects.

Latency stops mattering at daily horizons and costs shrink to noise against a
typical daily range, so this is where a usable directional edge would most
plausibly live.

  03  direction  - overnight gaps, opening-range direction, day of week
  04  magnitude  - does opening-range width forecast the rest of the day?
  05  breakout   - opening-range breakout, conditioned on range width

Result: 03 is a clean null, 04 holds out-of-sample in both instruments, 05
finds no edge.
"""
import argparse

import numpy as np
import pandas as pd

from common import dense, tstat, RTH
from config import INSTRUMENTS, IS_FRACTION

OPEN_WINDOW = ("13:30", "14:00")     # first 30 minutes of the US cash session


def sessions(path):
    d = dense(path)
    x = d.set_index("ts").sort_index()
    rows = []
    for day, g in x.groupby(x.index.date):
        rth = g.between_time(*RTH)
        if len(rth) < 500:
            continue
        opn = rth.between_time(*OPEN_WINDOW)
        rest = rth.between_time(OPEN_WINDOW[1], RTH[1])
        if len(opn) < 50 or len(rest) < 100:
            continue
        pre = g.between_time("00:00", "13:29")
        o, c = rth.price.iloc[0], rth.price.iloc[-1]
        hi, lo = opn.price.max(), opn.price.min()
        rows.append(dict(
            date=day, rth_open=o, or_hi=hi, or_lo=lo,
            rth_ret=np.log(c / o) * 1e4,
            or_ret=np.log(opn.price.iloc[-1] / o) * 1e4,
            rest_ret=np.log(c / rest.price.iloc[0]) * 1e4,
            overnight=np.log(o / pre.price.iloc[-1]) * 1e4 if len(pre) else np.nan,
            dow=pd.Timestamp(day).dayofweek,
        ))
    s = pd.DataFrame(rows)
    s["or_range"] = (s.or_hi - s.or_lo) / s.rth_open * 1e4
    s["abs_rest"] = s.rest_ret.abs()
    return s


def study_03_direction(s, key):
    print(f"\n--- 03 direction: {key} ---")
    for lo, hi, lab in [(-1e9, -20, "gap dn"), (-20, 20, "flat"), (20, 1e9, "gap up")]:
        m = s[(s.overnight > lo) & (s.overnight <= hi)]
        if len(m) > 5:
            print(f"  {lab:>8} n={len(m):>3}  RTH {m.rth_ret.mean():>8.2f} bp  "
                  f"t={tstat(m.rth_ret):>5.2f}")
    for lab, m in [("OR up", s[s.or_ret > 0]), ("OR down", s[s.or_ret < 0])]:
        if len(m) > 5:
            signed = np.sign(m.or_ret) * m.rest_ret
            print(f"  {lab:>8} n={len(m):>3}  signed rest {signed.mean():>8.2f} bp  "
                  f"t={tstat(signed):>5.2f}")


def study_04_magnitude(s, key):
    n = len(s)
    split = int(n * IS_FRACTION)
    IS, OS = s.iloc[:split], s.iloc[split:]
    r_is = IS.or_range.corr(IS.abs_rest)
    r_os = OS.or_range.corr(OS.abs_rest)
    t = r_os * np.sqrt(len(OS) - 2) / np.sqrt(max(1e-9, 1 - r_os ** 2))
    print(f"\n--- 04 magnitude: {key} (n={n}, OOS={len(OS)}) ---")
    print(f"  opening range -> |rest of day|   IS r {r_is:.3f}   "
          f"OOS r {r_os:.3f}   t {t:.2f}")
    q = OS.or_range.quantile([1/3, 2/3]).values
    for lab, m in [("narrow", OS[OS.or_range <= q[0]]),
                   ("mid", OS[(OS.or_range > q[0]) & (OS.or_range <= q[1])]),
                   ("wide", OS[OS.or_range > q[1]])]:
        if len(m):
            print(f"    {lab:>7} n={len(m):>3}  |rest| {m.abs_rest.mean():>7.2f} bp")


def study_05_breakout(path, key):
    """Entry on first trade beyond the opening range, exit at the cash close."""
    d = dense(path)
    x = d.set_index("ts").sort_index()
    rows = []
    for day, g in x.groupby(x.index.date):
        rth = g.between_time(*RTH)
        if len(rth) < 500:
            continue
        opn = rth.between_time(*OPEN_WINDOW)
        rest = rth.between_time(OPEN_WINDOW[1], RTH[1])
        if len(opn) < 50 or len(rest) < 100:
            continue
        hi, lo, ref = opn.price.max(), opn.price.min(), rth.price.iloc[0]
        up, dn = rest[rest.price > hi], rest[rest.price < lo]
        t_up = up.index[0] if len(up) else None
        t_dn = dn.index[0] if len(dn) else None
        side, entry = 0, np.nan
        if t_up is not None and (t_dn is None or t_up < t_dn):
            side, entry = 1, hi
        elif t_dn is not None:
            side, entry = -1, lo
        if side:
            rows.append(dict(date=day, or_range=(hi - lo) / ref * 1e4,
                             pnl=np.log(rest.price.iloc[-1] / entry) * 1e4 * side))
    tr = pd.DataFrame(rows)
    split = int(len(tr) * IS_FRACTION)
    IS, OS = tr.iloc[:split], tr.iloc[split:]
    print(f"\n--- 05 breakout: {key} ({len(tr)} breakouts) ---")
    print(f"  all  mean {tr.pnl.mean():>8.2f} bp  t={tstat(tr.pnl):>5.2f}  "
          f"win {100*(tr.pnl>0).mean():.0f}%")
    print(f"  IS   mean {IS.pnl.mean():>8.2f} bp  t={tstat(IS.pnl):>5.2f}")
    print(f"  OOS  mean {OS.pnl.mean():>8.2f} bp  t={tstat(OS.pnl):>5.2f}")
    q = IS.or_range.quantile([1/3, 2/3]).values
    for lab, m in [("narrow", tr[tr.or_range <= q[0]]),
                   ("mid", tr[(tr.or_range > q[0]) & (tr.or_range <= q[1])]),
                   ("wide", tr[tr.or_range > q[1]])]:
        if len(m) > 3:
            print(f"    {lab:>7} n={len(m):>3}  {m.pnl.mean():>8.2f} bp  "
                  f"t={tstat(m.pnl):>5.2f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data")
    args = p.parse_args()
    for key, spec in INSTRUMENTS.items():
        path = f"{args.data_dir}/{spec['file']}"
        print(f"\n{'='*68}\n{key}  {spec['label']}\n{'='*68}")
        s = sessions(path)
        study_03_direction(s, key)
        study_04_magnitude(s, key)
        study_05_breakout(path, key)
