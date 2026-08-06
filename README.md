# Electricity Price Pipeline

Automated daily fetch of European day-ahead electricity prices across multiple
bidding zones (DE-LU, AT, FR, NL, BE), via energy-charts.info. Runs daily via
GitHub Actions, validates data quality, and commits results as Parquet files.

Includes a battery storage optimizer that uses linear programming to find the
profit-maximizing charge/discharge schedule against real historical prices.

## Structure
- `src/fetch.py` — pulls day-ahead prices from the API across 5 European bidding zones, with retry/backoff for rate limits
- `src/transform.py` — DST-safe timestamp handling
- `src/validate.py` — data quality checks (row count, price range, timestamp integrity)
- `src/optimize.py` — battery charge/discharge optimization via `scipy.optimize.linprog`
- `src/backtest.py` — runs the optimizer across all accumulated days, per country, and compares results
- `data/processed/` — daily Parquet files, one per country per day
- `.github/workflows/fetch_prices.yml` — daily automation (14:00 UTC + backup run)

## Setup
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/fetch.py # fetch today's prices for all countries
python src/fetch.py 2026-08-03 # backfill a specific date
python src/optimize.py # run battery optimization on a chosen day
python src/backtest.py # run backtest across all countries and days

## Example output

Battery schedule for Aug 4, 2026, using specs matching a single Tesla Megapack 2
unit (3.9 MWh capacity, 1 MW power, ~93.7% round-trip efficiency). The battery
starts empty and is constrained to end the day with at least as much charge as
it started with.

![Battery schedule example](data/processed/battery_schedule_2026-08-04.png)

Optimizer correctly identifies price troughs to charge and price peaks to
discharge, yielding €488 theoretical profit for the day.

**Limitations of this example:**
- Assumes perfect foresight of the full day's prices. A realistic deployment
  would need to re-optimize on a rolling basis, using only prices known at
  each point in time (day-ahead auctions close ~1 day before delivery).
- Ignores battery degradation costs, which would reduce real-world profitability
  over many charge/discharge cycles.
- A production strategy would be backtested across many days and market
  conditions before being trusted

## Multi-country comparison

Running the same backtest across all 5 tracked bidding zones (Aug 2-6, 2026):

![Multi-country backtest](data/processed/backtest_summary_all_countries.png)

| Country | Avg. daily profit | Total (5 days) |
|---------|-------------------|-----------------|
| DE-LU   | €626.64            | €3,133.21       |
| NL      | €607.44            | €3,037.19       |
| FR      | €554.95            | €2,774.76       |
| AT      | €570.25            | €2,851.25       |
| BE      | €532.92            | €2,664.58       |

DE-LU shows the highest average arbitrage profit, plausibly reflecting Germany's
high renewable energy share (wind/solar), which tends to produce more volatile
day-ahead prices — and more volatility means more opportunity for battery arbitrage.
This is a small, early sample (5 days); a longer backtest would be needed to
confirm this pattern holds over different seasons and weather conditions. As
more days accumulate via the automated daily pipeline, this backtest will
naturally cover more market conditions and become more statistically meaningful.

## Pipeline reliability

As of this writing, the automated daily fetch has run successfully via GitHub
Actions' schedule for 3+ consecutive days without manual intervention, in
addition to on-demand manual runs used for testing and backfilling.
