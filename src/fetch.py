import requests
import pandas as pd
from validate import run_all_validations

def fetch_day_ahead_prices(country: str, date: str) -> pd.DataFrame:
    """
    Fetch day-ahead electricity prices from energy-charts.info (no API key required).
    country: e.g. 'DE-LU', 'FR', 'AT'
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
    import datetime

    country = "DE-LU"
    date = datetime.date.today().isoformat()   # always "today" when the script runs

    df = fetch_day_ahead_prices(country, date)
    print(df.head())
    print(f"Rows: {len(df)}")

    passed = run_all_validations(df)
    if not passed:
        raise SystemExit(f"Validation failed for {country} {date} — data not saved")

    df.to_parquet(f"data/processed/prices_{country.lower()}_{date}.parquet")
    print("Saved successfully")