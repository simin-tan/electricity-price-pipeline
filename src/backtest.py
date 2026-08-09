import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from optimize import optimize_battery


def run_backtest(country: str = "de-lu", chain_soc: bool = False):
    """
    Run the battery optimizer independently on every available day
    for a given country, and summarize total performance.

    If chain_soc=True, the ending state of charge from each day carries
    over as the starting state of charge for the next day (more realistic
    — a real battery doesn't reset to empty every midnight).
    """
    files = sorted(glob.glob(f"data/processed/prices_{country}_*.parquet"))

    if not files:
        raise FileNotFoundError(f"No price files found for {country}")

    eta_round_trip = 0.937
    eta_one_way = eta_round_trip ** 0.5
    capacity_mwh = 3.9

    results = []
    carried_soc_fraction = 0.0   # first day always starts empty

    for filepath in files:
        df = pd.read_parquet(filepath)
        df = df.sort_values("timestamp").reset_index(drop=True)
        prices = df["price_eur_mwh"].to_numpy()

        date_str = filepath.split("_")[-1].replace(".parquet", "")

        soc0_fraction = carried_soc_fraction if chain_soc else 0.0

        try:
            charge, discharge, profit, ending_soc = optimize_battery(
                prices,
                capacity_mwh=capacity_mwh,
                max_power_mw=1.0,
                eta_ch=eta_one_way,
                eta_dis=eta_one_way,
                soc0_fraction=soc0_fraction,
            )
            results.append({"date": date_str, "profit_eur": profit})
            print(f"{date_str}: €{profit:.2f} (start SoC: {soc0_fraction:.2f}, end SoC: {ending_soc / capacity_mwh:.2f})")

            if chain_soc:
                carried_soc_fraction = max(0.0, min(1.0, ending_soc / capacity_mwh))

        except Exception as e:
            print(f"{date_str}: failed — {e}")

    results_df = pd.DataFrame(results)
    return results_df


if __name__ == "__main__":
    countries = ["de-lu", "at", "fr", "nl", "be"]
    all_results = []

    for country in countries:
        print(f"\n=== Backtesting {country.upper()} ===")
        try:
            results_df = run_backtest(country)
            results_df["country"] = country.upper()
            all_results.append(results_df)
        except FileNotFoundError as e:
            print(f"Skipping {country}: {e}")

    combined_df = pd.concat(all_results, ignore_index=True)

    print("\n--- Summary by country ---")
    summary = combined_df.groupby("country")["profit_eur"].agg(["sum", "mean", "count"])
    summary.columns = ["total_profit_eur", "avg_daily_profit_eur", "days"]
    print(summary)

    # Plot: grouped bar chart, one color per country
    fig, ax = plt.subplots(figsize=(12, 6))
    for country in combined_df["country"].unique():
        subset = combined_df[combined_df["country"] == country]
        ax.plot(subset["date"], subset["profit_eur"], marker="o", label=country)

    ax.set_ylabel("Profit (EUR)")
    ax.set_xlabel("Date")
    ax.set_title("Daily battery profit by country")
    ax.legend()
    plt.tight_layout()
    plt.savefig("data/processed/backtest_summary_all_countries.png")
    plt.show()