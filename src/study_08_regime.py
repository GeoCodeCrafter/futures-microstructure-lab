"""
Study 08 - does the lead-lag concentrate in a regime we can actually reach?

The 1-second edge is latency-infeasible. But if it is far stronger during a
specific part of the session, the 5s version - which IS reachable - might clear
costs inside that window.

Conditioners, all trailing-only:
  * time of day (30-min buckets)
  * trailing realised volatility of the leader (previous 30 bars)
  * whether the leader's move continues its own prior direction
"""
import os
import numpy as np, pandas as pd
from common import dense, day_bars

DATA = os.environ.get("SCID_DIR", "../data")

COST_YM = 0.220


def paired(freq):
    a, b = dense(DATA + "/MESU26-CME.scid"), dense(DATA + "/YMU26-CBOT.scid")
    days = sorted(set(a.date.unique()) & set(b.date.unique()))
    out = []
    for day in days:
        ba, bb = day_bars(a, day, freq), day_bars(b, day, freq)
        idx = ba.index.intersection(bb.index)
        if len(idx) < 100:
            continue
        f = pd.DataFrame({
            "lead": np.log(ba.loc[idx, "price"]).diff(),
            "follow": np.log(bb.loc[idx, "price"]).diff(),
        })
        f["date"] = day
        f["tod"] = idx.floor("30min").time
        # trailing vol of leader, current bar excluded
        f["tvol"] = f.lead.shift(1).rolling(30, min_periods=15).std()
        out.append(f.dropna())
    return pd.concat(out), days


for freq in ["1s", "5s"]:
    D, days = paired(freq)
    D["sig"] = D.lead.shift(1)
    D = D.dropna()
    D = D[D.sig != 0]
    split = days[int(len(days) * 2 / 3)]
    IS, OS = D[D.date < split], D[D.date >= split]

    print(f"\n{'='*74}\n{freq} bars   IS={len(IS):,}  OOS={len(OS):,}  "
          f"cost={COST_YM:.3f} bp\n{'='*74}")

    print("\n  -- by time of day (all signals) --")
    print(f"  {'window':>10} {'IS bp':>9} {'OOS bp':>9} {'OOS t':>7} {'n':>8} {'vs cost':>8}")
    for tod in sorted(D.tod.unique()):
        oi, oo = IS[IS.tod == tod], OS[OS.tod == tod]
        if len(oo) < 500:
            continue
        pi = (np.sign(oi.sig) * oi.follow * 1e4).mean()
        po = np.sign(oo.sig) * oo.follow * 1e4
        t = po.mean() / (po.std(ddof=1) / np.sqrt(len(po)))
        flag = "  <--" if po.mean() > COST_YM and t > 2.5 and pi > 0 else ""
        print(f"  {str(tod)[:5]:>10} {pi:>9.4f} {po.mean():>9.4f} {t:>7.2f} "
              f"{len(po):>8} {po.mean()/COST_YM:>7.2f}x{flag}")

    print("\n  -- top-1% signals, by trailing-volatility tercile --")
    thr = IS.sig.abs().quantile(0.99)
    qv = IS.tvol.quantile([1/3, 2/3]).values
    print(f"  {'vol regime':>12} {'IS bp':>9} {'OOS bp':>9} {'OOS t':>7} {'n':>7} {'vs cost':>8}")
    for lab, lo, hi in [("low", -1e9, qv[0]), ("mid", qv[0], qv[1]), ("high", qv[1], 1e9)]:
        oi = IS[(IS.sig.abs() >= thr) & (IS.tvol > lo) & (IS.tvol <= hi)]
        oo = OS[(OS.sig.abs() >= thr) & (OS.tvol > lo) & (OS.tvol <= hi)]
        if len(oo) < 100:
            continue
        pi = (np.sign(oi.sig) * oi.follow * 1e4).mean()
        po = np.sign(oo.sig) * oo.follow * 1e4
        t = po.mean() / (po.std(ddof=1) / np.sqrt(len(po)))
        flag = "  <--" if po.mean() > COST_YM and t > 2.5 and pi > 0 else ""
        print(f"  {lab:>12} {pi:>9.4f} {po.mean():>9.4f} {t:>7.2f} {len(po):>7} "
              f"{po.mean()/COST_YM:>7.2f}x{flag}")
