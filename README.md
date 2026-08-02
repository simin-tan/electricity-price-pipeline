# Electricity Price Pipeline

Automated daily fetch of European day-ahead electricity prices (DE-LU bidding zone),
via energy-charts.info. Runs daily via GitHub Actions, validates data quality,
and commits results as Parquet files.

## Structure
- `src/fetch.py` — pulls day-ahead prices from the API
- `src/transform.py` — DST-safe timestamp handling
- `src/validate.py` — data quality checks (row count, price range, timestamp integrity)
- `data/processed/` — daily Parquet files, one per day
- `.github/workflows/fetch_prices.yml` — daily automation (14:00 UTC)

## Setup
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/fetch.py