"""
Study 02 - does one index lead the other, and can the lead be traded?

Two highly correlated index futures. If one systematically moves first, the
lag is exploitable in principle. Part A measures the lead; part B prices it.

Result: the S&P contract leads the Dow contract unambiguously (t > 100 at
1-second bars, with the reverse direction far weaker). The tradeable version
exists only at 1-second resolution on the largest ~1% of moves, and does not
survive realistic execution assumptions.
"""
import argparse

import numpy as np
import pandas as pd

from common import dense, day_bars
from config import INSTRUMENTS, cost_bp, IS_FRACTION

LEADER, FOLLOWER = "MES", "YM"


def paired(data_dir, freq):
    """Aligned per-session returns for both instruments."""
    a = dense(f"{data_dir}/{INSTRUMENTS[LEADER]['file']}")
    b = dense(f"{data_dir}/{INSTRUMENTS[FOLLOWER]['file']}")
    days = sorted(set(a.date.unique()) & set(b.date.unique()))
    frames = []
    for day in days:
        ba, bb = day_bars(a, day, freq), day_bars(b, day, freq)
        idx = ba.index.intersection(bb.index)
        if len(idx) < 100:
            continue
        f = pd.DataFrame({
            "lead": np.log(ba.loc[idx, "price"]).diff(),
            "follow": np.log(bb.loc[idx, "price"]).diff(),
        }).dropna()
        f["date"] = day
        frames.append(f)
    return pd.concat(frames), days


def measure(data_dir):
    print(f"\n{'#'*68}\n# Part A - which leads?\n{'#'*68}")
    for freq in ["1s", "5s", "30s"]:
        D, days = paired(data_dir, freq)
        D = D[(D.lead != 0) | (D.follow != 0)]
        se = 1 / np.sqrt(len(D))
        print(f"\n--- {freq} bars, n={len(D):,}, {len(days)} sessions "
              f"(corr se ~{se:.4f}) ---")
        print(f"  contemporaneous: {D.lead.corr(D.follow):.4f}")
        print(f"  {'lag':>4} {LEADER+'->'+FOLLOWER:>12} {'t':>8} "
              f"{FOLLOWER+'->'+LEADER:>12} {'t':>8}")
        for k in range(1, 6):
            f = D.lead.shift(k).corr(D.follow)
            r = D.follow.shift(k).corr(D.lead)
            print(f"  {k:>4} {f:>12.4f} {f/se:>8.1f} {r:>12.4f} {r/se:>8.1f}")


def economics(data_dir):
    spec = INSTRUMENTS[FOLLOWER]
    print(f"\n{'#'*68}\n# Part B - is the lead worth trading?\n{'#'*68}")
    for freq in ["1s", "5s", "30s"]:
        D, days = paired(data_dir, freq)
        D["sig"] = D.lead.shift(1)
        D = D.dropna()
        D = D[D.sig != 0]
        split = days[int(len(days) * IS_FRACTION)]
        IS, OS = D[D.date < split], D[D.date >= split]
        # price level only used for the cost model
        rt, _, _ = cost_bp(spec, 52740)

        print(f"\n=== {freq}   IS n={len(IS):,}  OOS n={len(OS):,}   "
              f"cost {rt:.3f} bp ===")
        print(f"  {'filter':>10} {'IS bp':>9} {'OOS bp':>9} {'OOS t':>8} {'vs cost':>9}")
        for label, q in [("all", 0.0), ("top 50%", .50), ("top 20%", .80),
                         ("top 5%", .95), ("top 1%", .99)]:
            thr = IS.sig.abs().quantile(q) if q else 0.0
            pi = (np.sign(IS.sig) * IS.follow)[IS.sig.abs() >= thr] * 1e4
            po = (np.sign(OS.sig) * OS.follow)[OS.sig.abs() >= thr] * 1e4
            if len(po) < 100:
                continue
            t = po.mean() / (po.std(ddof=1) / np.sqrt(len(po)))
            print(f"  {label:>10} {pi.mean():>9.4f} {po.mean():>9.4f} "
                  f"{t:>8.1f} {po.mean()/rt:>8.2f}x")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data")
    p.add_argument("--part", choices=["a", "b", "both"], default="both")
    a = p.parse_args()
    if a.part in ("a", "both"):
        measure(a.data_dir)
    if a.part in ("b", "both"):
        economics(a.data_dir)
