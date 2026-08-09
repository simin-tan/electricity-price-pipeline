import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def naive_strategy(
    prices: np.ndarray,
    capacity_mwh: float = 3.9,
    max_power_mw: float = 1.0,
    eta_ch: float = 0.968,
    eta_dis: float = 0.968,
    interval_hours: float = 0.25,
    low_percentile: float = 25,
    high_percentile: float = 75,
):
    """
    Simple rule-based strategy: charge when price is in the bottom
    percentile, discharge when price is in the top percentile.
    No lookahead, no optimization — just a fixed threshold rule.
    """
    T = len(prices)
    low_threshold = np.percentile(prices, low_percentile)
    high_threshold = np.percentile(prices, high_percentile)

    soc = 0.0
    charge = np.zeros(T)
    discharge = np.zeros(T)
    cash = 0.0

    for t in range(T):
        price = prices[t]

        if price <= low_threshold and soc < capacity_mwh:
            power = min(max_power_mw, (capacity_mwh - soc) / (eta_ch * interval_hours))
            charge[t] = power
            soc += power * eta_ch * interval_hours
            cash -= power * interval_hours * price

        elif price >= high_threshold and soc > 0:
            power = min(max_power_mw, soc / (interval_hours / eta_dis))
            discharge[t] = power
            soc -= power * interval_hours / eta_dis
            cash += power * interval_hours * price * eta_dis

    return charge, discharge, cash


if __name__ == "__main__":
    files = sorted(glob.glob("data/processed/prices_de-lu_*.parquet"))
    results = []

    for filepath in files:
        df = pd.read_parquet(filepath)
        df = df.sort_values("timestamp").reset_index(drop=True)
        prices = df["price_eur_mwh"].to_numpy()

        date_str = filepath.split("_")[-1].replace(".parquet", "")
        charge, discharge, profit = naive_strategy(prices)
        results.append({"date": date_str, "naive_profit_eur": profit})
        print(f"{date_str}: €{profit:.2f}")

    results_df = pd.DataFrame(results)

    # Hardcoded optimizer results from backtest.py's DE-LU run, for comparison
    optimizer_profits = {
        "2026-08-02": 665.72,
        "2026-08-03": 631.14,
        "2026-08-04": 488.31,
        "2026-08-05": 721.23,
        "2026-08-06": 626.80,
        "2026-08-07": 610.06,
        "2026-08-08": 694.94,
    }
    results_df["optimizer_profit_eur"] = results_df["date"].map(optimizer_profits)

    print(results_df)
    print(f"\nAverage naive profit: €{results_df['naive_profit_eur'].mean():.2f}")
    print(f"Average optimizer profit: €{results_df['optimizer_profit_eur'].mean():.2f}")

    improvement = (
        (results_df["optimizer_profit_eur"] - results_df["naive_profit_eur"])
        / results_df["naive_profit_eur"] * 100
    )
    print(f"Average improvement: {improvement.mean():.1f}%")

    x = np.arange(len(results_df))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width/2, results_df["naive_profit_eur"], width, label="Naive rule", color="gray")
    ax.bar(x + width/2, results_df["optimizer_profit_eur"], width, label="LP optimizer", color="steelblue")
    ax.set_xticks(x)
    ax.set_xticklabels(results_df["date"])
    ax.set_ylabel("Profit (EUR)")
    ax.set_title(f"Naive rule vs. LP optimizer — DE-LU (avg improvement: {improvement.mean():.1f}%)")
    ax.legend()
    plt.tight_layout()
    plt.savefig("data/processed/naive_vs_optimizer.png")
    plt.show()