"""
Study 09 - daily-horizon signals.

At this horizon a round trip costs ~0.2-0.5 bp against a mean absolute daily
move of ~35-47 bp. Cost is ~1% of the move, so ANY real effect would be
tradeable. If nothing is here, it is because nothing is here.

Signals, all computed from completed sessions only:
  * cumulative order flow imbalance for the day
  * close position within the day's range
  * prior-day return (momentum / reversal)
  * volume relative to trailing average
"""
import os
import numpy as np, pandas as pd
from common import dense, RTH

import os
DATA = os.environ.get("SCID_DIR", "../data")

def daily(name):
    d = dense(DATA + "/" + name + ".scid")
    x = d.set_index("ts").sort_index()
    rows = []
    for day, g in x.groupby(x.index.date):
        r = g.between_time(*RTH)
        if len(r) < 500:
            continue
        o, c = r.price.iloc[0], r.price.iloc[-1]
        hi, lo = r.price.max(), r.price.min()
        vol = r.volume.sum()
        rows.append(dict(
            date=day, open=o, close=c, ret=np.log(c / o) * 1e4,
            ofi=(r.ask_vol.sum() - r.bid_vol.sum()) / max(vol, 1),
            clpos=(c - lo) / (hi - lo) if hi > lo else 0.5,
            rng=(hi - lo) / o * 1e4, volume=vol,
        ))
    s = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    # next-day return, and trailing-only features
    s["fwd"] = s.ret.shift(-1)
    s["prev_ret"] = s.ret
    s["vol_ratio"] = s.volume / s.volume.shift(1).rolling(10, min_periods=5).mean()
    return s.dropna()


def report(s, label, cost):
    n = len(s)
    split = int(n * 2 / 3)
    IS, OS = s.iloc[:split], s.iloc[split:]
    print(f"\n{'='*70}\n{label}   n={n}  IS={len(IS)}  OOS={len(OS)}  "
          f"cost={cost:.3f} bp\n{'='*70}")
    print(f"  mean |next-day move| = {s.fwd.abs().mean():.1f} bp "
          f"(cost is {100*cost/s.fwd.abs().mean():.1f}% of it)")
    print(f"\n  {'signal':>22} {'IS r':>8} {'OOS r':>8} {'OOS bp':>9} {'OOS t':>7}")
    for lab, col, sign in [
        ("daily OFI (follow)",      "ofi",       +1),
        ("daily OFI (fade)",        "ofi",       -1),
        ("close position (follow)", "clpos",     +1),
        ("prior return (momentum)", "prev_ret",  +1),
        ("prior return (reversal)", "prev_ret",  -1),
        ("volume ratio",            "vol_ratio", +1),
    ]:
        x_is = IS[col] - (0.5 if col == "clpos" else 0)
        x_os = OS[col] - (0.5 if col == "clpos" else 0)
        r_is = x_is.corr(IS.fwd) * sign
        r_os = x_os.corr(OS.fwd) * sign
        pnl = sign * np.sign(x_os) * OS.fwd
        t = pnl.mean() / (pnl.std(ddof=1) / np.sqrt(len(pnl)))
        print(f"  {lab:>22} {r_is:>8.3f} {r_os:>8.3f} {pnl.mean():>9.2f} {t:>7.2f}")

    print("\n  -- daily OFI quintile -> next-day return (all sample) --")
    try:
        s2 = s.copy()
        s2["q"] = pd.qcut(s2.ofi, 5, labels=False, duplicates="drop")
        tab = s2.groupby("q").fwd.agg(["mean", "size"])
        for i, row in tab.iterrows():
            print(f"     Q{int(i)+1}  n={int(row['size']):>3}  next-day {row['mean']:>8.2f} bp")
    except Exception as e:
        print(f"     (quintiles unavailable: {e})")


for name, cost in [("MESU26-CME", 0.464), ("YMU26-CBOT", 0.220)]:
    report(daily(name), name, cost)
