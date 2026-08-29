# Resolutions

Problems hit, what actually caused them, and how they were fixed. Recorded
because the diagnosis is usually worth more than the fix, and because several of
these looked like completely different problems than they were.

---

### R-001 — Package unavailable in base image
**Symptom.** Container build failed: `Package 'winetricks' has no installation candidate`.
**Cause.** The package lives in Debian's `contrib` component, not `main`.
**Fix.** Fetch the script directly from its upstream repository rather than
enabling an entire extra component for one shell script.

---

### R-002 — Dozens of application instances
**Symptom.** Login attempts timed out. Load average climbed to 10+ on a 4-core box.
**Cause.** The platform's `.exe` is a *launcher*: it spawns the real 64-bit
binary and exits within ~15 seconds. A naive `while true; do run; done`
supervisor treated each exit as a crash and started another instance. Within
fifteen minutes dozens were running, all contending for the same data directory.
**Fix.** Launch the 64-bit binary directly, and check whether the process is
already running before starting another.
**Lesson.** Log timestamps gave this away instantly — restarts every 17 seconds.
It was invisible from the UI.

---

### R-003 — Login timed out, network blamed
**Symptom.** `Timeout error. There was no response.`
**Diagnosis path**, all of which turned out to be wrong:
- DNS inside the container — worked.
- Outbound HTTPS to the vendor — HTTP 200.
- TLS libraries present for both architectures — yes.
- IPv6 black-holing — no AAAA records published.

**What settled it.** Sampling `/proc/net/tcp` during a login attempt showed a
connection to the vendor's IP on 443 reaching `ESTABLISHED` and *staying* there
for 35+ seconds. Connected, then nothing — the signature of a stalled
application-layer handshake, not a network fault.
**Cause.** Wine 8.0 (the distribution's default). A Windows `curl.exe` run under
the *same* Wine completed a TLS handshake to the same host in 0.52 s, proving
the TLS stack was fine and isolating the fault to the higher-level HTTP layer
the application uses.
**Fix.** Rebuild against current upstream Wine. The error immediately changed
from "timeout" to "invalid login" — a different problem, and progress.

---

### R-004 — Shift key silently did nothing
**Symptom.** Correct credentials rejected repeatedly. The vendor's website
accepted the same password without complaint.
**Cause.** `x11vnc` was started without `-xkb`. Without it, modifier keys are
dropped: every capital letter arrived lowercase. A password field shows the
correct number of asterisks either way, so nothing looked wrong.
**Fix.** Add `-xkb`.
**Lesson.** This was misdiagnosed as an account-side problem and nearly escalated
to the vendor. The user-reported detail "it won't let me type capitals" solved it
in seconds — worth more than an hour of packet-level diagnosis.

---

### R-005 — No window manager
**Symptom.** The application window was fixed-size with its toolbar clipped, and
could not be moved, resized or maximised. Keyboard maximise shortcuts were
intercepted by the local browser instead.
**Cause.** No window manager in the container. Nothing existed to draw
decorations or handle resize requests.
**Fix.** Add a minimal WM and start it before the VNC server. Appended as its own
image layer so the long Wine layers stay cached.

---

### R-006 — Look-ahead contamination in a volatility test
**Symptom.** "Session volume" appeared to predict rest-of-day movement at
r = 0.55–0.67 — far stronger than any other predictor tested.
**Cause.** Session volume was summed over the *whole* session, including the very
period being predicted. The predictor contained its own answer.
**Fix.** Result discarded. The opening-range predictor that replaced it is
complete by a fixed cutoff, before the predicted window opens.
**Lesson.** The suspiciously strong result is the one to audit first.

---

### R-007 — Configuration destroyed by image rebuilds
**Symptom.** None yet — caught before it bit.
**Cause.** Only the data and log directories were bind-mounted. Login credentials
and the record-enable flag lived inside the container filesystem, surviving
restarts and reboots but destroyed by any image rebuild. The platform would
return logged-out and not recording, and the archive would stop growing silently.
**Fix.** Copy the config files onto the host and bind-mount them back in.
**Verification.** Host-side file timestamps updated on the next application
start, proving writes were flowing through the mount rather than into the
container.

---

### R-008 — Cross-instrument correlations computed on nothing
**Symptom.** A lead–lag study reported plausible-looking correlations on ~9,000
rows where ~1,000,000 were expected.
**Cause.** The two instruments were resampled independently, producing
`datetime64` indexes of *different resolution*. The indexes intersected to
exactly zero rows; the join silently produced a tiny misaligned frame instead of
an error.
**Fix.** Force a common index unit after resampling, build bars per-session, and
assert on intersection size before computing anything.
**Lesson.** The tell was the row count, not the correlations — which looked
entirely reasonable. Sanity-check `n` before reading any statistic.

---

### R-009 — Shell portability on an embedded host
**Symptom.** Diagnostic scripts failed with `Call to undefined function` and
brace-expanded directory names taken literally.
**Cause.** BusyBox `ash` and BusyBox `awk`, not bash and GNU awk. No `strtonum()`,
no brace expansion.
**Fix.** POSIX shell only; hex decoding via shell `printf` instead of awk
extensions.

---

### R-010 - Look-ahead in a spread z-score produced a 25x "edge"
**Symptom.** A pairs study reported spread mean-reversion worth up to 25x round-trip
cost, with t-statistics above 30 and in-sample and out-of-sample figures agreeing
closely. Everything about it looked correct.
**Cause.** The spread was normalised with `groupby(date).transform(mean/std)` -
the *whole session's* mean and standard deviation. The z-score at 10:00 therefore
knew where the session closed. Being "extreme" was partly a statement about the
future.
**Fix.** Trailing-window mean and standard deviation with the current bar excluded
via `shift(1).rolling(...)`. The measured edge fell from 25x to 0.02-0.6x. Nothing
survived.
**Lesson.** This is the third look-ahead bug in this project (see R-006) and by far
the most convincing while it lasted. Two heuristics caught it:
 - an effect that large in a liquid, heavily-arbitraged market is a bug until
   proven otherwise;
 - in-sample and out-of-sample agreeing *too* closely suggests both are drawing on
   the same contaminated information, rather than one validating the other.

**Standing rule adopted:** any statistic computed with `groupby(...).transform(...)`
over a period that overlaps the prediction window is look-ahead. Normalisation must
be causal, always.
