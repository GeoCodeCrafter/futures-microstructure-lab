"""Instrument specs and cost model.

Costs are the whole game: every gross edge in this repo is quoted against a
round-trip cost, and nothing is called an edge until it clears one.

  tick      minimum price increment, index points
  mult      contract multiplier (currency per index point)
  comm      round-trip commission estimate, account currency
"""

INSTRUMENTS = {
    "MES": dict(file="MESU26-CME.scid",  tick=0.25, mult=5, comm=0.50,
                label="Micro E-mini S&P 500"),
    "YM":  dict(file="YMU26-CBOT.scid",  tick=1.00, mult=5, comm=0.80,
                label="E-mini Dow"),
}


def cost_bp(spec, price):
    """Round-trip cost in basis points: cross one tick, plus commission.

    Optimistic by construction - it assumes a one-tick spread and no slippage.
    Real costs are worse precisely when signals fire hardest, because that is
    when spreads widen.
    """
    tick_bp = spec["tick"] / price * 1e4
    comm_bp = spec["comm"] / (price * spec["mult"]) * 1e4
    return tick_bp + comm_bp, tick_bp, comm_bp


# Split fraction for the walk-forward holdout. Always split by DATE, never by
# row, or adjacent bars leak across the boundary.
IS_FRACTION = 2 / 3
