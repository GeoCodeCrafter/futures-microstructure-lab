# Changelog

Dated log of changes to the pipeline and the research. Newest first.

Format: `Added` / `Changed` / `Fixed` / `Found` / `Open`.
`Found` records a research result; see [FINDINGS.md](FINDINGS.md) for detail.

---

## 2026-08-29 (second pass)

Deep second pass: five further studies covering the classes of test the first
pass did not reach.

**Added**
- `study_06_pairs.py` - spread mean reversion between the two contracts.
- `study_07_volume_bars.py` - volume-bar sampling and trade-size stratification.
- `study_08_regime.py` - time-of-day and volatility-regime conditioning.
- `study_09_daily_signals.py` - daily-horizon signals where cost is negligible.
- `study_10_execution.py` - maker versus taker economics.

**Found**
- **Study 06** - no spread edge once the z-score is causal.
- **Study 07** - volume bars and trade-size splits do not rescue a sub-cost signal.
- **Study 08** - no reachable regime; the lead-lag stays inside one second.
- **Study 09** - decisive null at daily horizon, where cost is only ~1% of the
  average move. Cost is not the binding constraint there; predictability is absent.
- **Study 10** - **the central result.** The taker/maker swing is 0.662 bp, about
  six times the largest gross edge measured anywhere (0.106 bp). Execution side
  dominates signal quality by close to an order of magnitude.

**Fixed**
- `R-010` look-ahead in the spread z-score, which had produced an apparent 25x-cost
  edge with t > 30. Recomputed causally; the effect vanished entirely.

**Changed**
- Multiple-testing accounting added to FINDINGS: ~150 combinations tested across
  ten studies, one cleared costs with a stable sign - fewer than chance alone
  would predict.

**Open**
- The maker bound cannot be resolved with trade data. Requires market-by-order.
- Stale-recording alarm still writes to a log with nothing acting on it.

---

## 2026-08-29

**Added**
- Public repository created. Code, methods and aggregate findings only — no
  market data, which is licensed.
- `METHOD.md` — statistical standards, written down so they can be held to.
- `PIPELINE.md` — capture architecture and resilience matrix.
- `RESOLUTIONS.md` — nine problems with root causes.
- Studies refactored into importable modules with guarded entry points; shared
  loaders extracted to `common.py`, instrument and cost model to `config.py`.

**Found**
- **Study 02** — one index future leads the other, 1-second lag correlation
  0.123 (t = 120) against 0.024 in reverse. Tradeable only in the top 1% of
  moves at 1-second resolution; fails realistic execution assumptions.
- **Study 03** — no session-level directional edge. Clean null.
- **Study 04** — opening-range width forecasts rest-of-day magnitude. Holds
  out-of-sample in both instruments, monotone across terciles. Most robust
  result so far.
- **Study 05** — opening-range breakout shows no edge; negative tilt on one
  instrument concentrated in wide-range days. Small sample, flagged not
  concluded.

**Fixed**
- `R-008` cross-instrument joins were intersecting to zero rows through a
  `datetime64` resolution mismatch. All lead–lag numbers recomputed.
- `R-006` look-ahead contamination in a volatility predictor. Result withdrawn.

**Changed**
- Configuration persisted to host mounts (`R-007`), so image rebuilds no longer
  reset the capture to a logged-out state.

**Open**
- Stale-recording alarm writes to a log but nothing acts on it. Notification
  hook wanted.
- Capture host CPU headroom is unproven for depth data; tick capture runs
  comfortably, depth is far heavier.

---

## 2026-08-28

**Added**
- Tick capture pipeline stood up end to end: containerised charting platform
  under Wine, headless via Xvfb/VNC, data bind-mounted to array storage.
- Hourly archiver with dated roll-up, gzip after three days, and a weekday
  stale-data alarm.
- Cron installation extended following the existing host convention — timestamped
  backup, refusal to write if the existing crontab reads empty, sanity check on
  retained line count.

**Fixed**
- `R-001` build failure on a component-gated package.
- `R-002` supervisor spawning an instance every 17 seconds.
- `R-003` login stall traced to the Wine version, not the network.
- `R-004` VNC dropping modifier keys, silently lowercasing passwords.
- `R-005` no window manager, so windows could not be resized.
- `R-009` BusyBox shell/awk portability in diagnostics.

**Found**
- **Study 01** — order flow imbalance predicts forward returns *negatively* at
  every horizon. Real, sign-stable, and roughly four times too small to clear
  costs. Implies aggressors are adversely selected.

**Open**
- No depth data. Bounds every question about queue position and passive fills.
