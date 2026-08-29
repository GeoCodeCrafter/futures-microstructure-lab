"""
Study 07 - alternative bar sampling and trade-size stratification.

Time bars sample calendar time, which has nothing to do with information flow.
Volume bars sample equal chunks of traded quantity, which is closer to how
information actually arrives, and typically give better-behaved returns.

Also splits flow by average trade size: large prints are a proxy for
institutional participation, small prints for retail.

All features are trailing-only. No full-sample or full-day statistics anywhere.
"""
import os
import numpy as np, pandas as pd
from common import dense, RTH

DATA = os.environ.get("SCID_DIR", "../data")

COSTS = {"MESU26-CME": 0.464, "YMU26-CBOT": 0.220}
HOR = [1, 3, 5, 10, 20]


def volume_bars(d, target):
    """Emit a bar every `target` contracts traded."""
    d = d.set_index("ts").between_time(*RTH).reset_index()
    d = d.sort_values("ts")
    cum = d.volume.cumsum()
    grp = (cum // target).astype("int64")
    g = d.groupby(grp)
    b = pd.DataFrame({
        "ts": g.ts.last(),
        "price": g.price.last(),
        "volume": g.volume.sum(),
        "bid_vol": g.bid_vol.sum(),
        "ask_vol": g.ask_vol.sum(),
        "trades": g.num_trades.sum(),
    })
    b["date"] = b.ts.dt.date
    b = b[b.volume > 0]
    b["ofi"] = (b.ask_vol - b.bid_vol) / b.volume
    b["avg_size"] = b.volume / b.trades.replace(0, np.nan)
    return b.dropna()


def evaluate(b, cost, label):
    # forward returns within day only
    lp = np.log(b.price)
    for h in HOR:
        b[f"f{h}"] = b.groupby("date").apply(
            lambda g: np.log(g.price).shift(-h) - np.log(g.price)
        ).reset_index(level=0, drop=True)
    b = b.dropna()
    days = sorted(b.date.unique())
    split = days[int(len(days) * 2 / 3)]
    IS, OS = b[b.date < split], b[b.date >= split]

    # trade-size terciles from IS only
    q = IS.avg_size.quantile([1/3, 2/3]).values

    print(f"\n--- {label}   n={len(b):,}  OOS={len(OS):,}  cost={cost:.3f} bp ---")
    print(f"  {'size bucket':>12} {'h':>3} {'IS bp':>9} {'OOS bp':>9} {'OOS t':>7} {'vs cost':>8}")
    for lab, sel in [("all", lambda x: x),
                     ("small trades", lambda x: x[x.avg_size <= q[0]]),
                     ("large trades", lambda x: x[x.avg_size > q[1]])]:
        for h in HOR:
            oi, oo = sel(IS), sel(OS)
            if len(oo) < 100:
                continue
            # fade the flow (study 01 sign)
            pi = (-np.sign(oi.ofi) * oi[f"f{h}"] * 1e4).mean()
            po = -np.sign(oo.ofi) * oo[f"f{h}"] * 1e4
            t = po.mean() / (po.std(ddof=1) / np.sqrt(len(po)))
            flag = "  <--" if po.mean() > cost and t > 2.5 and pi > 0 else ""
            print(f"  {lab:>12} {h:>3} {pi:>9.4f} {po.mean():>9.4f} {t:>7.2f} "
                  f"{po.mean()/cost:>7.2f}x{flag}")


for name in ["MESU26-CME", "YMU26-CBOT"]:
    d = dense(DATA + "/" + name + ".scid")
    med_daily = d.groupby("date").volume.sum().median()
    for divisor, tag in [(400, "~400 bars/day"), (100, "~100 bars/day")]:
        target = max(1, int(med_daily / divisor))
        b = volume_bars(d, target)
        evaluate(b, COSTS[name], f"{name}  volume bars ({target} contracts, {tag})")
