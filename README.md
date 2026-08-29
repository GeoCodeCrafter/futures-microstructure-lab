# futures-microstructure-lab

Order-flow and microstructure research on CME index futures, recorded from a
self-hosted tick capture pipeline.

This repository holds **methods, findings and infrastructure notes** — not market
data. Exchange data is licensed and is never committed here.

## What this is

A running log of an attempt to answer one question honestly:

> Given tick data with an aggressor-side flag, is there a statistically real
> and economically tradeable edge in index futures?

So far the answer is **mostly no**, and the *shape* of the no is the useful part.
Findings are recorded whether they work or not — nulls are results, and a
repository of only positive findings is a repository of survivorship bias.

## Documents

| File | Purpose |
|------|---------|
| [FINDINGS.md](FINDINGS.md) | Every study, its result, and its verdict |
| [METHOD.md](METHOD.md) | Statistical standards this repo holds itself to |
| [PIPELINE.md](PIPELINE.md) | How the data is captured and archived |
| [RESOLUTIONS.md](RESOLUTIONS.md) | Problems hit, root causes, fixes |
| [CHANGELOG.md](CHANGELOG.md) | Dated log of changes and updates |

## Headline results

| Study | Effect | Verdict |
|-------|--------|---------|
| 01 Order flow imbalance | Real, **negative** - aggressors are adversely selected | ~4x too small to clear costs |
| 02 Lead-lag between contracts | Very strong (t = 120), correctly signed | Lives inside 1 second; latency-infeasible |
| 03 Session direction | None | Clean null |
| 04 Opening range -> day magnitude | Holds out-of-sample, both instruments | **Usable**, forecasts size not direction |
| 05 Opening-range breakout | None on one contract, negative tilt on the other | No edge found |
| 06 Spread mean reversion | None once the z-score is causal | No edge (see R-010) |
| 07 Volume bars / trade size | None | Resampling does not rescue it |
| 08 Regime conditioning | No reachable regime | Edge stays inside 1 second |
| 09 Daily horizon | None, where cost is only ~1% of the move | Decisive null |
| 10 Maker vs taker | Taker/maker swing = **6x the best signal found** | **The central result** |

**The conclusion after ten studies.** Where predictability exists it is at one
second and unreachable; where cost is irrelevant there is no predictability; in
between, gross edges of 0.02-0.35 bp sit against costs of 0.22-0.46 bp. The
largest quantity in the whole study is the spread itself - the taker/maker
difference is 0.662 bp against a best measured signal of 0.106 bp.

Effort belongs on the side of the trade, not the direction of it. Resolving that
needs market-by-order data.

Detail, tables and caveats in [FINDINGS.md](FINDINGS.md).

## Running it

```bash
pip install -r requirements.txt
cd src
python study_01_orderflow_imbalance.py --data-dir ../data
python study_02_lead_lag.py            --data-dir ../data
python study_03_sessions.py            --data-dir ../data   # studies 03-05
python study_06_pairs.py               --data-dir ../data
python study_10_execution.py                                # no data needed

# studies 07-09 read SCID_DIR from the environment
SCID_DIR=../data python study_07_volume_bars.py
SCID_DIR=../data python study_08_regime.py
SCID_DIR=../data python study_09_daily_signals.py
```

`--data-dir` must contain Sierra Chart `.scid` intraday files. `src/common.py`
documents the binary format if you want to read it with something else.

`src/config.py` holds instrument specs and the cost model. Adjust `comm` to your
own commission before drawing conclusions about viability — the cost model is
what decides whether an effect counts as an edge.

## Scope and honesty notes

- Tick data only. No depth or market-by-order data is captured yet, which
  bounds what can be tested — see the closing section of FINDINGS.
- Sample is modest. Tick-level studies have ample power; session-level studies
  are underpowered and labelled as such.
- `tstat()` returns `NaN` below 30 observations by design, so small conditional
  cells show `nan` rather than a meaningless number.

## Licence

MIT for the code. No market data, licensed or otherwise, is included.
