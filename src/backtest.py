import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from optimize import optimize_battery


def run_backtest(country: str = "de-lu"):
    """
    Run the battery optimizer independently on every available day
    for a given country, and summarize total performance.
    """
    files = sorted(glob.glob(f"data/processed/prices_{country}_*.parquet"))

    if not files:
        raise FileNotFoundError(f"No price files found for {country}")

    eta_round_trip = 0.937
    eta_one_way = eta_round_trip ** 0.5

    results = []

    for filepath in files:
        df = pd.read_parquet(filepath)
        df = df.sort_values("timestamp").reset_index(drop=True)
        prices = df["price_eur_mwh"].to_numpy()

        # Extract the date from the filename for labeling
        date_str = filepath.split("_")[-1].replace(".parquet", "")

        try:
            charge, discharge, profit = optimize_battery(
                prices,
                capacity_mwh=3.9,
                max_power_mw=1.0,
                eta_ch=eta_one_way,
                eta_dis=eta_one_way,
                soc0_fraction=0.0,
            )
            results.append({"date": date_str, "profit_eur": profit})
            print(f"{date_str}: €{profit:.2f}")
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