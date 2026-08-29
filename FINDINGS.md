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

## Where an edge would actually be

Two studies converge on the same place.

Study 01 found that aggressors are adversely selected. Study 02 found that the
tradeable form of the lead–lag requires being fast enough to aggress
profitably — which commodity infrastructure is not.

Both point at the **passive side of the book**: earning the spread rather than
paying it. On instrument B that swings the cost term by roughly 0.8 bp per round
trip, which is larger than every gross edge measured in this repository combined.

Testing it requires knowing where an order sits in the queue, whether it would
have filled, and what happened to the orders around it. None of that is present
in trade data — it needs full depth or market-by-order capture.

That is a specific, falsifiable reason to extend the capture pipeline, rather
than a general hope that more data helps.
