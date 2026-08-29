"""
Study 06 - is the A/B spread mean-reverting enough to pay for both legs?

Spread trading pays both instruments' costs, so reversion must be large, not
merely significant.

IMPORTANT: v1 of this study normalised the spread with the full-day mean and
standard deviation. That is look-ahead - the z-score at 10:00 knew where the
session closed - and it produced apparent edges of 25x cost with t > 30. This
version computes the mean and standard deviation from a trailing window only,
with the current bar excluded. The edge disappears entirely. See RESOLUTIONS
R-010.
"""
import argparse
import numpy as np
import pandas as pd

from common import dense, day_bars
from config import INSTRUMENTS, cost_bp, IS_FRACTION

HOR = [1, 5, 15, 30]


def panel(data_dir, freq):
    a = dense(f"{data_dir}/{INSTRUMENTS['MES']['file']}")
    b = dense(f"{data_dir}/{INSTRUMENTS['YM']['file']}")
    days = sorted(set(a.date.unique()) & set(b.date.unique()))
    out = []
    for day in days:
        ba, bb = day_bars(a, day, freq), day_bars(b, day, freq)
        idx = ba.index.intersection(bb.index)
        if len(idx) < 60:
            continue
        f = pd.DataFrame({"m": np.log(ba.loc[idx, "price"]),
                          "y": np.log(bb.loc[idx, "price"])})
        f["date"] = day
        out.append(f)
    return pd.concat(out), days


def run(data_dir="data"):
    cost = (cost_bp(INSTRUMENTS["MES"], 7549)[0]
            + cost_bp(INSTRUMENTS["YM"], 52740)[0])
    for freq, win in [("60s", 60), ("300s", 24)]:
        P, days = panel(data_dir, freq)
        split = days[int(len(days) * IS_FRACTION)]
        IS0 = P[P.date < split]
        beta = np.polyfit(IS0.m, IS0.y, 1)[0]
        P["spread"] = P.y - beta * P.m

        # causal z-score: trailing window, current bar excluded
        g = P.groupby("date").spread
        mu = g.transform(lambda s: s.shift(1).rolling(win, min_periods=win // 2).mean())
        sd = g.transform(lambda s: s.shift(1).rolling(win, min_periods=win // 2).std())
        P["z"] = (P.spread - mu) / sd

        for h in HOR:
            P[f"f{h}"] = P.groupby("date").spread.shift(-h) - P.spread
        Q = P.replace([np.inf, -np.inf], np.nan).dropna()
        IS, OS = Q[Q.date < split], Q[Q.date >= split]

        print(f"\n{'='*72}\n{freq} bars, trailing window {win}, beta={beta:.3f}"
              f"   OOS n={len(OS):,}   both-leg cost {cost:.3f} bp\n{'='*72}")
        print(f"  {'|z|>':>5} {'h':>4} {'IS bp':>9} {'OOS bp':>9} {'OOS t':>7} "
              f"{'n':>7} {'vs cost':>8}")
        for thr in [0.5, 1.0, 1.5, 2.0]:
            for h in HOR:
                mo, mi = OS[OS.z.abs() > thr], IS[IS.z.abs() > thr]
                if len(mo) < 100:
                    continue
                po = -np.sign(mo.z) * mo[f"f{h}"] * 1e4
                pi = (-np.sign(mi.z) * mi[f"f{h}"] * 1e4).mean() if len(mi) > 100 else np.nan
                t = po.mean() / (po.std(ddof=1) / np.sqrt(len(po)))
                print(f"  {thr:>5.1f} {h:>4} {pi:>9.3f} {po.mean():>9.3f} "
                      f"{t:>7.2f} {len(po):>7} {po.mean()/cost:>7.2f}x")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data")
    run(p.parse_args().data_dir)
