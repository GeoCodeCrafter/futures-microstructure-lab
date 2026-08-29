"""Shared loaders for Sierra Chart .scid intraday tick files."""
import numpy as np
import pandas as pd

SC_EPOCH = np.datetime64("1899-12-30T00:00:00", "us")

# US cash session in UTC. Both index futures trade around the clock, but
# overnight bars are mostly stale-price artefacts, so most studies restrict here.
RTH = ("13:30", "20:00")

DTYPE = np.dtype([
    ("dt", "<i8"),
    ("open", "<f4"), ("high", "<f4"), ("low", "<f4"), ("close", "<f4"),
    ("num_trades", "<u4"), ("volume", "<u4"),
    ("bid_vol", "<u4"), ("ask_vol", "<u4"),
])


def read_scid(path, max_records=None):
    """Read a .scid file into a DataFrame.

    Format: 56-byte header, then 40-byte records.
      int64  DateTime   microseconds since 1899-12-30
      float  Open High Low Close
      uint32 NumTrades TotalVolume BidVolume AskVolume

    BidVolume/AskVolume split each trade by the side of the book it executed
    into - i.e. the aggressor side. That field is what makes order-flow work
    possible and is absent from most retail feeds.
    """
    with open(path, "rb") as f:
        header = f.read(56)
        if header[:4] != b"SCID":
            raise ValueError(f"{path}: not a .scid file (magic={header[:4]!r})")
        rec_size = int.from_bytes(header[8:12], "little")
        if rec_size != 40:
            raise ValueError(f"{path}: unexpected record size {rec_size}")
        raw = np.fromfile(f, dtype=DTYPE, count=max_records or -1)

    df = pd.DataFrame({
        "ts": SC_EPOCH + raw["dt"].astype("timedelta64[us]"),
        "price": raw["close"].astype("float64"),
        "volume": raw["volume"].astype("int64"),
        "bid_vol": raw["bid_vol"].astype("int64"),
        "ask_vol": raw["ask_vol"].astype("int64"),
        "num_trades": raw["num_trades"].astype("int64"),
    })
    return df[(df.price > 0) & (df.volume >= 0)].reset_index(drop=True)


def dense(path, min_ticks=1000):
    """Drop days that are backfill stubs rather than real sessions."""
    d = read_scid(path)
    d["date"] = d.ts.dt.date
    n = d.groupby("date").size()
    return d[d.date.isin(set(n[n > min_ticks].index))]


def day_bars(d, day, freq, rth=RTH):
    """Bars for a single session.

    Resampling per-day matters: it keeps returns from being differenced across
    a session boundary, and forcing the index unit avoids a subtle failure where
    two instruments resampled separately end up with datetime64 indexes of
    different resolution and intersect to nothing.
    """
    x = d[d.date == day].set_index("ts").sort_index()
    b = x.resample(freq).agg(price=("price", "last"),
                             vol=("volume", "sum"),
                             bid=("bid_vol", "sum"),
                             ask=("ask_vol", "sum"))
    b["price"] = b.price.ffill()
    b = b.between_time(*rth).dropna(subset=["price"])
    b.index = b.index.astype("datetime64[ns]")
    return b


def tstat(x):
    x = pd.Series(x).dropna()
    if len(x) < 30:
        return float("nan")
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
