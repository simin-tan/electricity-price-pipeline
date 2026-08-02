import time
import datetime
import requests
import pandas as pd
from validate import run_all_validations


def fetch_day_ahead_prices(country: str, date: str) -> pd.DataFrame:
    """
    Fetch day-ahead electricity prices from energy-charts.info (no API key required).
    country: e.g. 'DE-LU', 'AT', 'FR', 'NL', 'BE'
    date: 'YYYY-MM-DD'
    """
    url = "https://api.energy-charts.info/price"
    params = {"bzn": country.upper(), "start": date, "end": date}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(data["unix_seconds"], unit="s", utc=True),
        "price_eur_mwh": data["price"],
    })

    return df


if __name__ == "__main__":
    countries = ["DE-LU", "AT", "FR", "NL", "BE"]
    date = datetime.date.today().isoformat()

    for country in countries:
        print(f"\n--- Fetching {country} for {date} ---")

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                df = fetch_day_ahead_prices(country, date)
                print(f"Rows: {len(df)}")

                passed = run_all_validations(df)
                if not passed:
                    print(f"Validation failed for {country} {date} — skipping save")
                    break

                df.to_parquet(f"data/processed/prices_{country.lower()}_{date}.parquet")
                print(f"Saved {country} successfully")
                break   # success, no need to retry

            except Exception as e:
                print(f"Attempt {attempt} failed for {country}: {e}")
                if attempt < max_retries:
                    wait = 5 * attempt   # 5s, then 10s, then 15s
                    print(f"Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"Giving up on {country} after {max_retries} attempts")

        time.sleep(4)   # pause before moving to next country