import numpy as np
import sys
sys.path.insert(0, "src")
from optimize import optimize_battery


def test_battery_respects_power_limits():
    """Charge and discharge should never exceed max_power_mw."""
    prices = np.array([50, 100, 150, 200, 50, 100, 150, 200] * 12)
    max_power = 1.0
    charge, discharge, profit, ending_soc = optimize_battery(
        prices, capacity_mwh=3.9, max_power_mw=max_power
    )
    assert (charge <= max_power + 1e-6).all()
    assert (discharge <= max_power + 1e-6).all()


def test_battery_never_negative_power():
    """Charge and discharge should never be negative."""
    prices = np.array([50, 100, 150, 200, 50, 100, 150, 200] * 12)
    charge, discharge, profit, ending_soc = optimize_battery(prices, capacity_mwh=3.9, max_power_mw=1.0)
    assert (charge >= -1e-6).all()
    assert (discharge >= -1e-6).all()


def test_zero_volatility_gives_zero_profit():
    """If price never changes, there's no arbitrage opportunity — profit should be ~0."""
    prices = np.full(96, 100.0)
    charge, discharge, profit, ending_soc = optimize_battery(
        prices, capacity_mwh=3.9, max_power_mw=1.0, soc0_fraction=0.0
    )
    assert profit < 1.0


def test_higher_volatility_gives_more_profit():
    """More price spread should generally allow more arbitrage profit."""
    low_volatility = np.array([90, 100, 110, 100] * 24)
    high_volatility = np.array([10, 100, 200, 100] * 24)

    _, _, profit_low, _ = optimize_battery(low_volatility, capacity_mwh=3.9, max_power_mw=1.0)
    _, _, profit_high, _ = optimize_battery(high_volatility, capacity_mwh=3.9, max_power_mw=1.0)

    assert profit_high > profit_low