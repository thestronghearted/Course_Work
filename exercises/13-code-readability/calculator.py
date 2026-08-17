"""Compound interest calculator (Exercise 13, Example 2 — Missing Documentation).

The original ``calculate`` had no docstring and terse names. This version adds
documentation and intention-revealing names while preserving the exact numeric
behaviour (verified by ``test_calculator.py``).
"""


def calculate(principal, rate, time, additional=0, frequency=12):
    """Project the future value of an investment with periodic compounding.

    Interest is compounded ``frequency`` times per year. An ``additional``
    contribution is added at the end of each completed year *except the last*
    (matching the original behaviour).

    Args:
        principal: Starting amount (currency units).
        rate: Annual interest rate as a percentage (e.g. ``5`` for 5%).
        time: Investment duration in whole years.
        additional: Amount contributed at the end of each year (except the last).
        frequency: Compounding periods per year (12 = monthly, 4 = quarterly).

    Returns:
        dict with:
            ``final_amount`` – balance after ``time`` years (rounded to 2 dp),
            ``interest_earned`` – final amount minus principal and contributions,
            ``total_contributions`` – principal plus all yearly contributions.
    """
    balance = principal
    rate_per_period = rate / 100 / frequency
    total_periods = time * frequency

    for period in range(1, total_periods + 1):
        interest = balance * rate_per_period
        balance += interest
        # Add the yearly contribution at each year boundary, but not after the
        # final period (so the last contribution isn't counted).
        is_year_boundary = period % frequency == 0
        if is_year_boundary and period < total_periods:
            balance += additional

    contributions = additional * (time - 1)
    return {
        "final_amount": round(balance, 2),
        "interest_earned": round(balance - principal - contributions, 2),
        "total_contributions": principal + contributions,
    }
