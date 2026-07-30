import requests
import pandas as pd

def fetch_day_ahead_prices(country: str, date: str) -> pd.DataFrame:
    """
    Fetch day-ahead electricity prices from energy-charts.info (no API key required).
    country: e.g. 'de', 'fr', 'at'
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

    df.to_parquet(f"data/processed/prices_{country.lower()}_{date}.parquet")
    
    return df

if __name__ == "__main__":
    df = fetch_day_ahead_prices("DE-LU", "2026-07-28")
    print(df.head())
    print(f"Rows: {len(df)}")