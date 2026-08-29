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
| 01 Order flow imbalance | Real, **negative** — aggressors are adversely selected | ~4× too small to clear costs |
| 02 Lead–lag between contracts | Very strong, correctly signed | Lives inside 1 second; latency-infeasible |
| 03 Session direction | None | Clean null |
| 04 Opening range → day magnitude | Holds out-of-sample, both instruments | **Usable**, but forecasts size not direction |
| 05 Opening-range breakout | None on one contract, negative tilt on the other | No edge found |

Detail, tables and caveats in [FINDINGS.md](FINDINGS.md).

## Running it

```bash
pip install -r requirements.txt
cd src
python study_01_orderflow_imbalance.py --data-dir ../data
python study_02_lead_lag.py            --data-dir ../data
python study_03_sessions.py            --data-dir ../data
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
