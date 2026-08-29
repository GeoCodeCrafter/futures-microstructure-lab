# Pipeline

How the data gets captured. Deliberately generic — this describes an
architecture, not a specific machine.

```
   CME  ──►  charting platform  ──►  .scid tick files  ──►  archive
             (Wine, headless)        (bind-mounted)          (hourly, gzipped)
                    │
                    └── remote GUI over VNC, loopback-only, reached by SSH tunnel
```

## Capture host

A low-power 4-core NAS running Linux and Docker. Chosen because it is already
powered 24/7; the trade-off is limited CPU, which is a real constraint for
depth capture and is tracked as an open risk.

## Container

The charting platform is a Windows application, run under Wine in a Debian
container.

- **Headless display.** Xvfb provides a virtual screen; x11vnc exposes it;
  noVNC serves it over HTTP.
- **Window manager required.** Without one, Wine windows have no title bars and
  cannot be moved, resized or maximised. A minimal WM (openbox) fixes this.
- **Loopback binding only.** The VNC server runs without authentication, so the
  port is bound to localhost and reached exclusively through an SSH tunnel. It
  is never exposed to the LAN.
- **Supervised, not looped.** The platform's launcher process exits once it has
  spawned the real binary. A naive restart loop therefore spawns a new instance
  every cycle — see [RESOLUTIONS.md](RESOLUTIONS.md#r-002).

## Persistence

Three categories, and getting them wrong is how a capture silently stops:

| What | Where | Survives rebuild? |
|------|-------|-------------------|
| Tick/depth data | bind-mounted to host | yes |
| Logs | bind-mounted to host | yes |
| **Login + settings** | bind-mounted to host | yes — *after* [R-007](RESOLUTIONS.md#r-007) |
| Application binaries | container image | rebuilt from image |

Configuration originally lived inside the container. It survived restarts and
reboots but was destroyed by any image rebuild, which would silently return the
platform to a logged-out, not-recording state.

## Archiving

Depth data is only backfillable for a short window (roughly 15 days on this
feed), so anything not copied out before it ages is unrecoverable at retail
prices. An hourly job:

1. copies new files into a permanent `archive/YYYY/MM/` tree,
2. re-copies today's file while it is still growing, so a crash costs at most an
   hour,
3. gzips anything older than three days,
4. raises a **stale-data alarm** into a log if no file has been written in six
   hours on a weekday.

The alarm is the important part. The dangerous failure is not a crash — it is
recording stopping quietly while everything still looks healthy.

## Resilience

| Failure | Recovery |
|---------|----------|
| Application crashes | supervisor relaunches, single instance enforced |
| Container stops | `restart: unless-stopped` |
| Docker daemon dies | 5-minute cron watchdog restarts it |
| Host reboots | watchdog covers a known flaky boot path |
| Image rebuilt | config restored from host mounts |
| Recording stops silently | detected within the hour; **not** auto-repaired |

That last row is the known gap: the alarm is written to a log, and nothing acts
on it.

## Data hygiene

- Exchange data is licensed. It is archived locally and **never** published.
- This repository contains code and aggregate statistics only.
