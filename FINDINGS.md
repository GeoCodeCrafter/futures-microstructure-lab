# Findings

Every study run, with its verdict. Standards in [METHOD.md](METHOD.md).

Instruments are referred to as **A** (micro S&P 500 future) and **B** (Dow
future). Sample at time of writing: ~4.4M ticks, 59 overlapping sessions of
dense data, tick-level fields including the aggressor-side volume split.

Costs used: **A 0.464 bp**, **B 0.220 bp** round trip.

---

## Study 01 — Order flow imbalance

**Question.** Does `(ask_vol - bid_vol) / volume` predict forward returns?

**Result.** Yes, and *negatively* — at every horizon, in both halves of the
sample. Aggressive buying precedes price falling.

| Horizon | IS r | OOS r | IS t | OOS t |
|---|---|---|---|---|
| 1 bar | −0.061 | −0.016 | −10.1 | −2.6 |
| 5 bar | −0.036 | −0.023 | −6.9 | **−4.2** |
| 15 bar | −0.025 | −0.019 | −4.9 | −3.0 |
| 30 bar | −0.016 | −0.016 | −3.2 | −1.7 |

*(1-minute bars, instrument A.)*

**Economics.**

| Instrument | Best OOS gross | Cost | Ratio |
|---|---|---|---|
| A | 0.106 bp | 0.464 bp | 0.23× |
| B | 0.023 bp | 0.220 bp | 0.10× |

**Verdict — real, sub-cost.** Statistically solid, roughly four times too small
to pay for the spread.

**Interpretation.** This is adverse selection: traders who pay the spread to hit
the book lose slightly and systematically. The implication is that the profitable
side of this pattern is the *passive* side, where the cost term reverses sign.
That cannot be tested with trade data.

> Note the widespread retail claim that order flow imbalance signals continuation.
> On this sample the sign is consistently the other way.

---

## Study 02 — Lead–lag between contracts

**Question.** Does one index future lead the other?

**Result.** Unambiguously yes, A → B.

| Lag | A → B | t | B → A | t |
|---|---|---|---|---|
| 1 | **0.1230** | **120.5** | 0.0236 | 23.2 |
| 2 | 0.0254 | 24.9 | −0.0062 | −6.1 |
| 3 | 0.0067 | 6.6 | −0.0044 | −4.3 |
| 4 | 0.0042 | 4.1 | 0.0003 | 0.3 |

*(1-second bars, US cash session, n = 959,898.)*

The asymmetry is the finding: 0.123 one way against 0.024 the other. Price
discovery runs from the more liquid benchmark into the follower.

**Economics.** Signal = A's prior-bar return; trade B in the same direction for
one bar.

| Bars | Filter | OOS bp | OOS t | vs cost |
|---|---|---|---|---|
| 1s | all | 0.039 | 53.9 | 0.18× |
| 1s | top 5% | 0.196 | 6.4 | 0.89× |
| **1s** | **top 1%** | **0.339** | **3.3** | **1.54×** |
| 5s | top 5% | 0.079 | 1.3 | 0.36× |
| 30s | top 5% | −0.542 | −1.7 | −2.47× |

**Verdict — real, unreachable.** The only cell in this repository that clears its
costs, and it does not survive contact with reality:

1. **Latency.** Requires seeing a tick in A and being filled in B inside one
   second, from commodity infrastructure over a retail broker. This is a
   microsecond game.
2. **Generous accounting.** The test captures the whole following bar from its
   open; in practice entry happens partway through the move.
3. **Costs rise when it fires.** Top-1% moves are fast-market conditions, where
   the follower's spread widens.
4. **Multiple testing.** Most-filtered cell of seventeen, n = 2,479, t = 3.3.

The 30-second row deserves attention: strongly positive in-sample, firmly
negative out-of-sample. That is an overfit caught by the split, and it is why
every number here is quoted out-of-sample.

---

## Study 03 — Session direction

**Question.** Any daily-horizon directional edge? Latency is irrelevant here and
costs are negligible against a ~47 bp average daily move, so this is where a
usable edge would most plausibly live.

**Result.** Nothing.

- **Overnight gaps do not exist.** These contracts trade through the night; every
  session landed in the flat bucket. There is no gap to fade.
- **Opening-range direction does not predict the rest of the day** — signed
  continuation t between −1.58 and 0.49 across both instruments.
- **Day of week is noise** on 11–21 observations per weekday.

**Verdict — clean null.** Worth more than it looks: it rules out the class of
daily patterns that discretionary and retail systems most often assume.

---

## Study 04 — Opening range forecasts magnitude

**Question.** Direction failed. Is *magnitude* predictable?

**Result.** Yes, and it holds out-of-sample in both instruments independently.

| | IS r | OOS r | OOS t |
|---|---|---|---|
| A | 0.327 | 0.355 | 2.08 |
| B | 0.256 | 0.548 | 2.78 |

Monotone across terciles, out-of-sample:

| Opening range | A \|rest of day\| | B \|rest of day\| |
|---|---|---|
| Narrow | 23.0 bp | 16.3 bp |
| Mid | 26.0 bp | 21.0 bp |
| **Wide** | **49.9 bp** | **49.7 bp** |

**Verdict — holds.** The most robust finding in the repository.

**What it is and is not.** It is a *magnitude* forecast — it says nothing about
direction. Its uses are position sizing against expected range rather than fixed
size, scaling stops and targets to the day rather than to a constant, and
deciding whether a range-dependent strategy should trade at all on a given
morning.

A look-ahead bug was found and removed during this study — see
[RESOLUTIONS.md](RESOLUTIONS.md#r-006).

---

## Study 05 — Opening-range breakout

**Question.** Does a plain opening-range breakout work, and does range width
filter the good days?

**Setup.** Entry on first trade beyond the 30-minute opening range, exit at the
cash close, no stop.

| Instrument | Breakouts | Mean | t | Win rate |
|---|---|---|---|---|
| A | 95 of 97 | +4.09 bp | 0.74 | 54% |
| **B** | 58 of 58 | **−12.63 bp** | **−2.07** | 45% |

Conditioned on range width, instrument B: narrow −6.18 bp, mid −4.56 bp,
**wide −32.84 bp**.

**Verdict — no edge found.** A is indistinguishable from zero. B carries a
negative tilt that keeps its sign in both halves and concentrates in wide-range
days — precisely the days a breakout trader would find most attractive.

**Do not over-read it.** 58 sessions is small, the out-of-sample t is −0.87, and
this specification has no stops, no bracket logic and no session-close handling.
It justifies checking a live implementation against its own results on that
contract; it does not justify a conclusion about breakout strategies generally.

---

## Study 06 - Spread mean reversion between the contracts

**Question.** The two contracts are ~95% correlated. Does the spread revert
enough to pay for both legs (0.684 bp round trip)?

**Result with a causal z-score.** No.

| abs(z) > | Hold | IS bp | OOS bp | OOS t | vs cost |
|---|---|---|---|---|---|
| 1.0 | 5 | 0.080 | 0.043 | 0.95 | 0.06x |
| 1.5 | 15 | -0.046 | 0.282 | 2.86 | 0.41x |
| 2.0 | 5 | 0.364 | 0.379 | 4.45 | 0.55x |
| 2.0 | 30 | 0.563 | -0.129 | -0.61 | -0.19x |

**Verdict - no edge.** Nothing clears cost with a stable sign.

> **This study first reported edges of 25x cost with t > 30.** Those were
> entirely produced by normalising the spread with the *full day's* mean and
> standard deviation - the z-score at 10:00 knew where the session closed.
> With a trailing-window z-score the effect vanishes completely. See
> [R-010](RESOLUTIONS.md#r-010). It is the most instructive failure in this
> repository.

---

## Study 07 - Volume bars and trade-size stratification

**Question.** Time bars sample calendar time, which has nothing to do with
information arrival. Do volume bars, or splitting flow by average trade size
(a crude institutional/retail proxy), reveal signal that time bars hide?

**Result.** No. At ~400 bars/day the flagged cells have unstable in-sample sign;
at ~100 bars/day results turn uniformly negative out-of-sample.

**Verdict - no edge.** Resampling does not rescue a sub-cost signal.

---

## Study 08 - Regime conditioning

**Question.** The 1-second lead-lag is latency-infeasible. Does it concentrate
in a reachable regime - a time of day, or a volatility state - strongly enough
that the 5-second version clears costs?

**Result.** No time-of-day window clears cost in either instrument; the best is
0.29x at 5-second bars. The only cell that ever clears is the same 1-second
top-1% signal, now in the high-volatility tercile (1.63x cost, t = 3.37) on
n = 215.

**Verdict - no reachable regime.** The edge stays where it was: inside one
second.

---

## Study 09 - Daily horizon

**Question.** At daily horizons a round trip costs 0.7-1.0% of the average
absolute move. Cost is effectively free. Is anything predictable?

| Signal | IS r | OOS r | OOS t |
|---|---|---|---|
| Daily OFI | -0.014 | 0.034 | -0.84 |
| Close position in range | 0.035 | 0.146 | 0.86 |
| Prior-day return | -0.001 | -0.076 | -0.61 |
| Volume ratio | -0.164 | -0.011 | -0.41 |

Daily-OFI quintiles against next-day return are non-monotone noise
(+15.5, -10.0, +17.9, -10.7, +13.3 bp).

**Verdict - decisive null.** Every abs(t) below 1.0. This matters more than a
typical null: **cost is not the binding constraint at this horizon.** There is
simply no predictability to capture.

---

## Study 10 - Maker versus taker

Every study above assumes crossing the spread. Study 01 found aggressors are
adversely selected - which is the same statement as *passive fills are
compensated*. Pricing that difference:

| | Spread | Comm | Taker cost | Maker cost | Best gross | Taker net | Maker net |
|---|---|---|---|---|---|---|---|
| A | 0.331 | 0.132 | 0.464 | -0.199 | 0.106 | **-0.358** | **+0.305** |
| B | 0.190 | 0.030 | 0.220 | -0.159 | 0.023 | -0.197 | +0.182 |

The swing between taker and maker is twice the spread - **0.662 bp on
instrument A, roughly six times the largest gross edge found anywhere in this
research (0.106 bp).**

**This is the central result of the project.** Execution side dominates signal
quality by close to an order of magnitude. Every signal tested is economically
small next to the question of whether you pay or earn the spread.

**It is a bound, not a strategy.** Maker net assumes fills are free. A resting
order fills when someone chooses to trade against it, which happens
preferentially when they know something you do not. The true figure is:

```
maker_net  -  E[adverse selection | filled]
```

and the second term cannot be estimated from trade data.

---

## Conclusion after ten studies

The problem has a consistent shape, and it is not "no edge exists":

- **Where predictability exists, it is at one second.** The lead-lag is
  overwhelming (t = 120) but unreachable without professional latency.
- **Where costs are irrelevant, there is no predictability.** The daily horizon
  is a clean null, and cost is only ~1% of the move there.
- **In between, gross edges cluster at 0.02-0.35 bp** against costs of
  0.22-0.46 bp. Consistently the wrong side of the line.
- **The one quantity larger than any signal found is the spread itself.**

The implication is to stop searching for better signals. The measured signals
are all around 0.1 bp; the execution decision is worth around 0.66 bp. Effort
belongs on the side of the trade, not the direction of it.

Resolving that requires queue position, fill probability, and book state around
fills - market-by-order data. That is a specific, falsifiable reason to extend
the capture, and the only remaining question this dataset cannot answer.

## Tests run, for multiple-testing accounting

Approximately **150** signal / horizon / filter / regime combinations across ten
studies. At a 5% threshold, roughly seven would appear significant by chance.
Exactly one combination cleared costs with a stable sign - the 1-second top-1%
lead-lag - which is fewer than chance alone would predict, and it fails on
execution grounds rather than statistical ones.
