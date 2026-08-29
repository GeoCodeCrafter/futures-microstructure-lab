"""
Study 10 - maker versus taker economics.

Every other study assumes crossing the spread. Study 01 found aggressors are
adversely selected, which is the same statement as: passive fills are
compensated. This prices that difference.

Reported as a BOUND, not a backtest: fill probability cannot be estimated from
trade data.
"""
from config import INSTRUMENTS, cost_bp

# Largest out-of-sample gross edge measured for each instrument, from Study 01.
GROSS = {"MES": 0.106, "YM": 0.023}
PRICE = {"MES": 7549, "YM": 52740}


def run():
    print(f"{'':<6}{'spread':>9}{'comm':>8}{'taker':>9}{'maker':>9}"
          f"{'gross':>9}{'taker net':>11}{'maker net':>11}")
    print("-" * 72)
    swing = {}
    for k, spec in INSTRUMENTS.items():
        _, spread_bp, comm_bp = cost_bp(spec, PRICE[k])
        taker, maker = spread_bp + comm_bp, comm_bp - spread_bp
        g = GROSS[k]
        swing[k] = taker - maker
        print(f"{k:<6}{spread_bp:>9.3f}{comm_bp:>8.3f}{taker:>9.3f}"
              f"{maker:>9.3f}{g:>9.3f}{g-taker:>11.3f}{g-maker:>11.3f}")

    print(f"""
All figures are basis points per round trip.

    taker cost = +spread + commission   (pay to cross, both ways)
    maker cost = -spread + commission   (paid to provide, both ways)

The swing between the columns is twice the spread: {swing['MES']:.3f} bp on the
S&P contract. That is roughly SIX TIMES the largest gross edge found anywhere in
this research ({GROSS['MES']:.3f} bp).

Execution side dominates signal quality by close to an order of magnitude. Every
signal tested is economically small next to the question of whether you pay or
earn the spread.

WHY THIS IS A BOUND, NOT A STRATEGY

Maker net assumes fills are free. They are not. A resting order fills when
someone chooses to trade against it, which happens preferentially when they know
something you do not - the adverse selection of Study 01, seen from the other
side. The true figure is:

    maker_net  -  E[adverse selection | filled]

The second term is unmeasurable from trade data. It needs queue position, fill
probability, and book state around the fill - i.e. market-by-order data.
""")


if __name__ == "__main__":
    run()
