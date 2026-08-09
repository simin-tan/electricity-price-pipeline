# Electricity Price Pipeline

Automated daily fetch of European day-ahead electricity prices across multiple
bidding zones (DE-LU, AT, FR, NL, BE), via energy-charts.info. Runs daily via
GitHub Actions, validates data quality, and commits results as Parquet files.

Price data collected here is used by a separate optimization project:
[battery-dispatch-optimizer](https://github.com/simin-tan/battery-dispatch-optimizer),
which finds profit-maximizing battery charge/discharge schedules using this data.

## Structure
- `src/fetch.py` — pulls day-ahead prices from the API across 5 European bidding zones, with retry/backoff for rate limits
- `src/transform.py` — DST-safe timestamp handling
- `src/validate.py` — data quality checks (row count, price range, timestamp integrity)
- `data/processed/` — daily Parquet files, one per country per day
- `.github/workflows/fetch_prices.yml` — daily automation (14:00 UTC + backup run)

## Setup
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python src/fetch.py # fetch today's prices for all countries
python src/fetch.py 2026-08-03 # backfill a specific date
```

## Pipeline reliability

The automated daily fetch runs via GitHub Actions' schedule, with a backup
run added as a safety net against occasionally skipped scheduled triggers.
Data quality is checked on every fetch (row count, price range, timestamp
integrity) before being saved — failed validation blocks the save rather
than committing bad data.

## Possible next steps

- Add more bidding zones as needed
- Extend validation checks (e.g. cross-check against a second data source)
- Add a simple data quality dashboard summarizing recent fetch history