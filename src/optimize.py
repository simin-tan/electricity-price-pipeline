import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import linprog


def optimize_battery(
    prices: np.ndarray,
    capacity_mwh: float = 1.0,
    max_power_mw: float = 0.5,
    eta_ch: float = 0.95,
    eta_dis: float = 0.95,
    soc0_fraction: float = 0.5,
    interval_hours: float = 0.25,   # 15-min resolution = 0.25h per step
):
    """
    Find the optimal charge/discharge schedule to maximize profit,
    given a price curve and battery constraints.

    Returns: (charge_mw, discharge_mw, profit_eur)
    """
    T = len(prices)
    n = 2 * T   # decision variables: T charge powers + T discharge powers

    # Objective: minimize (cost of charging - revenue from discharging)
    # linprog minimizes, so revenue is negative cost
    c_obj = np.zeros(n)
    c_obj[:T] = prices * interval_hours / eta_ch
    c_obj[T:] = -prices * interval_hours * eta_dis

    # Power bounds: 0 <= charge, discharge <= max_power_mw
    bounds = [(0, max_power_mw)] * T + [(0, max_power_mw)] * T

    # State of charge constraints, built as cumulative sums
    soc0 = soc0_fraction * capacity_mwh
    A_ub, b_ub = [], []

    for t in range(T):
        row = np.zeros(n)
        row[:t + 1] = eta_ch * interval_hours
        row[T:T + t + 1] = -interval_hours / eta_dis

        # soc_t <= capacity
        A_ub.append(row.copy())
        b_ub.append(capacity_mwh - soc0)

        # soc_t >= 0  -->  -soc_t <= soc0
        A_ub.append(-row)
        b_ub.append(soc0)

    # NOTE: end-of-day floor constraint removed for multi-day chaining experiments.
    # With this constraint active, the optimizer always drains back to exactly
    # its starting SoC every day (since it has no incentive to save charge for
    # a future it can't see), making day-to-day chaining meaningless.
    #
    # final_row = np.zeros(n)
    # final_row[:T] = eta_ch * interval_hours
    # final_row[T:] = -interval_hours / eta_dis
    # A_ub.append(-final_row)
    # b_ub.append(0)

    result = linprog(
        c_obj,
        A_ub=np.array(A_ub),
        b_ub=np.array(b_ub),
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")

    charge = result.x[:T]
    discharge = result.x[T:]
    profit = -result.fun

    # Compute ending state of charge, to allow chaining across multiple days
    soc0 = soc0_fraction * capacity_mwh
    net_energy = np.sum(charge * eta_ch * interval_hours) - np.sum(discharge * interval_hours / eta_dis)
    ending_soc = soc0 + net_energy

    return charge, discharge, profit, ending_soc


if __name__ == "__main__":
    # Load one real day of prices to test against
    df = pd.read_parquet("data/processed/prices_de-lu_2026-08-04.parquet")
    df = df.sort_values("timestamp").reset_index(drop=True)

    prices = df["price_eur_mwh"].to_numpy()

    # Battery specs matching a single Tesla Megapack 2 unit
    # (3.9 MWh capacity, ~1 MW power, ~93.7% round-trip efficiency)
    eta_round_trip = 0.937
    eta_one_way = eta_round_trip ** 0.5   # split evenly between charge/discharge legs

    charge, discharge, profit, ending_soc = optimize_battery(
        prices,
        capacity_mwh=3.9,
        max_power_mw=1.0,
        eta_ch=eta_one_way,
        eta_dis=eta_one_way,
        soc0_fraction=0.0,   # start empty, nothing to discharge until battery has charged something
    )

    df["charge_mw"] = charge
    df["discharge_mw"] = discharge

    print(df[["timestamp", "price_eur_mwh", "charge_mw", "discharge_mw"]])
    print(f"\nTotal profit: €{profit:.2f}")
    print(f"Hours charging: {(charge > 0.01).sum() * 0.25:.2f}h")
    print(f"Hours discharging: {(discharge > 0.01).sum() * 0.25:.2f}h")

    fig, ax1 = plt.subplots(figsize=(14, 5))

    ax1.plot(df["timestamp"], df["price_eur_mwh"], color="black", label="Price (EUR/MWh)")
    ax1.set_ylabel("Price (EUR/MWh)")
    ax1.set_xlabel("Time")

    ax2 = ax1.twinx()
    ax2.bar(df["timestamp"], df["charge_mw"], width=0.01, color="green", alpha=0.5, label="Charging")
    ax2.bar(df["timestamp"], -df["discharge_mw"], width=0.01, color="red", alpha=0.5, label="Discharging")
    ax2.set_ylabel("Power (MW)")

    fig.legend(loc="upper left")
    plt.title(f"Battery schedule — profit: €{profit:.2f}")
    plt.tight_layout()
    plt.savefig("data/processed/battery_schedule_2026-08-04.png")
    plt.show()