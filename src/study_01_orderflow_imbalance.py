"""
Study 01 - does order flow imbalance predict forward returns?

OFI = (ask_volume - bid_volume) / total_volume, per bar.
  +1 = every contract traded into the offer (aggressive buying)
  -1 = every contract traded into the bid (aggressive selling

Result: the correlation is NEGATIVE at every horizon, in both halves of the
sample. Aggressive buying precedes price falling. Statistically solid,
economically about four times too small to pay for the spread.
"""
import argparse

import numpy as np
import pandas as pd

from common import dense, tstat
from config import INSTRUMENTS, cost_bp, IS_FRACTION

HORIZONS = [1, 5, 15, 30]


def bars(d, freq="1min"):
    x = d.set_index("ts")
    b = x.resample(freq).agg(
        price=("price", "last"), volume=("volume", "sum"),
        bid_vol=("bid_vol", "sum"), ask_vol=("ask_vol", "sum"),
    ).dropna(subset=["price"])
    b = b[b.volume > 0].copy()
    b["ofi"] = (b.ask_vol - b.bid_vol) / b.volume
    b["ret"] = np.log(b.price).diff()
    b["date"] = b.index.date
    for h in HORIZONS:
        b[f"fwd{h}"] = np.log(b.price).shift(-h) - np.log(b.price)
    return b.dropna()


def run(data_dir="data"):
    for key, spec in INSTRUMENTS.items():
        b = bars(dense(f"{data_dir}/{spec['file']}"))
        days = sorted(b.date.unique())
        split = days[int(len(days) * IS_FRACTION)]
        IS, OS = b[b.date < split], b[b.date >= split]
        rt, _, _ = cost_bp(spec, b.price.median())

        print(f"\n{'='*68}\n{key}  {spec['label']}   {len(b):,} bars, "
              f"{len(days)} days, split {split}\n{'='*68}")
        print(f"  round-trip cost: {rt:.3f} bp\n")
        print(f"  {'horizon':>8} {'IS r':>9} {'OOS r':>9} {'IS t':>8} {'OOS t':>8} {'OOS bp':>9}")
        for h in HORIZONS:
            pnl_is = -np.sign(IS.ofi) * IS[f"fwd{h}"]
            pnl_os = -np.sign(OS.ofi) * OS[f"fwd{h}"]
            print(f"  {h:>8} {IS.ofi.corr(IS[f'fwd{h}']):>9.4f} "
                  f"{OS.ofi.corr(OS[f'fwd{h}']):>9.4f} "
                  f"{tstat(pnl_is):>8.2f} {tstat(pnl_os):>8.2f} "
                  f"{pnl_os.mean()*1e4:>9.4f}")

        best = max((-np.sign(OS.ofi) * OS[f"fwd{h}"]).mean() * 1e4 for h in HORIZONS)
        print(f"\n  best OOS gross edge : {best:.3f} bp")
        print(f"  cost to capture     : {rt:.3f} bp")
        print(f"  ratio               : {best/rt:.2f}x  "
              f"({'viable' if best > rt else 'NOT viable'})")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data")
    run(p.parse_args().data_dir)
