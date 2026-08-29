# Method

Standards this repository holds itself to. They exist because microstructure
research is unusually easy to fool yourself in: samples are enormous, so almost
anything reaches statistical significance, while transaction costs quietly
exceed almost every effect you find.

## 1. Split by date, never by row

In-sample is the first two thirds of *sessions*; out-of-sample is the last third.
Splitting by row leaks information — adjacent bars are correlated, so a random
split puts near-duplicates of the training data into the test set.

No number in FINDINGS is quoted in-sample alone.

## 2. Costs are part of the hypothesis

Every gross edge is divided by a round-trip cost before it is described as an
edge. The cost model (`src/config.py`) is:

```
cost_bp = tick_size/price * 1e4  +  commission/(price * multiplier) * 1e4
```

This assumes a one-tick spread crossed once and no slippage. It is deliberately
**optimistic** — real costs are worse precisely when signals fire hardest,
because that is when spreads widen. An effect that only just clears this bar has
not really cleared it.

## 3. Sign stability beats significance

With a million bars, `t = 5` is unremarkable. What is hard to fake is an effect
that keeps its sign across:

- both halves of the sample, and
- both instruments, tested independently.

Findings are promoted on sign stability, not on the size of the t-statistic.
The strongest-looking cell in a table is usually the most overfit one.

## 4. Nulls are recorded

Studies that find nothing are written up with the same detail as studies that
find something. A repository containing only positive results is a repository
of survivorship bias, and the nulls here do real work — knowing that session
direction is unpredictable rules out a large class of strategies.

## 5. Multiple testing is stated

Roughly forty signal/horizon/filter combinations have been examined. At
conventional thresholds, two would look significant by chance alone. Wherever a
number is the best of many, that is said explicitly next to it.

## 6. Session boundaries are respected

Returns are never differenced across a session boundary, and bars are built
per-day. Studies that depend on genuine two-sided liquidity are restricted to
the US cash session; overnight bars are largely stale-price artefacts.

## 7. Backfill is not recording

Days with fewer than 1,000 ticks are stubs from a historical backfill, not real
sessions, and are dropped before anything is computed.

## 8. Look-ahead is actively hunted

Any predictor computed over a window that overlaps the period being predicted is
contaminated. One such bug was found and removed during Study 04 — see
[RESOLUTIONS.md](RESOLUTIONS.md#r-006). Predictors must be complete before the
predicted window opens.

## 9. Small cells report nothing rather than noise

`tstat()` returns `NaN` below 30 observations. Conditional breakdowns on small
samples therefore show `nan` instead of a t-statistic that would only invite
over-interpretation.

## Known limitations

- **No depth data.** Everything here is trade-level. Anything about queue
  position, fill probability or passive execution is untestable with this data.
- **Session-level power is poor.** Tick studies rest on millions of observations;
  session studies rest on tens. The latter should be re-run as the sample grows.
- **One contract per instrument.** No roll-adjusted continuous series yet, so
  studies do not span contract rolls.
