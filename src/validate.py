import pandas as pd

def validate_row_count(df: pd.DataFrame, freq_per_hour: int = 4) -> bool:
    """
    Check the number of rows matches what's expected for a full day.
    freq_per_hour=4 for 15-min data (96 rows/day normally).
    Allows for DST transition days (92 or 100 rows).
    """
    n = len(df)
    normal = 24 * freq_per_hour
    short_day = normal - freq_per_hour   # spring-forward, one hour missing
    long_day = normal + freq_per_hour    # fall-back, one hour duplicated

    if n in (normal, short_day, long_day):
        print(f"✅ Row count OK: {n} rows")
        return True
    else:
        print(f"⚠️  Unexpected row count: {n} (expected {short_day}, {normal}, or {long_day})")
        return False


def validate_price_range(df: pd.DataFrame, col: str = "price_eur_mwh",
                          low: float = -500, high: float = 4000) -> bool:
    """
    European day-ahead prices can legitimately go negative (oversupply)
    but shouldn't exceed exchange price caps (~4000 EUR/MWh on EPEX/Nord Pool).
    """
    out_of_range = df[(df[col] < low) | (df[col] > high)]
    if len(out_of_range) == 0:
        print(f"✅ Prices within plausible range [{low}, {high}]")
        return True
    else:
        print(f"⚠️  {len(out_of_range)} price(s) outside plausible range")
        print(out_of_range)
        return False


def validate_timestamps_unique_increasing(df: pd.DataFrame, col: str = "timestamp") -> bool:
    """Check timestamps are sorted and have no duplicates."""
    is_sorted = df[col].is_monotonic_increasing
    has_duplicates = df[col].duplicated().any()

    if is_sorted and not has_duplicates:
        print("✅ Timestamps sorted, no duplicates")
        return True
    else:
        if not is_sorted:
            print("⚠️  Timestamps not sorted")
        if has_duplicates:
            print(f"⚠️  {df[col].duplicated().sum()} duplicate timestamp(s)")
        return False


def run_all_validations(df: pd.DataFrame) -> bool:
    """Run all checks. Returns True only if everything passes."""
    results = [
        validate_row_count(df),
        validate_price_range(df),
        validate_timestamps_unique_increasing(df),
    ]
    all_passed = all(results)
    if all_passed:
        print("\n✅ All validations passed")
    else:
        print("\n❌ Validation failed — see warnings above")
    return all_passed


if __name__ == "__main__":
    df = pd.read_parquet("data/processed/prices_de-lu_2026-07-28.parquet")
    passed = run_all_validations(df)
    if not passed:
        exit(1)   # non-zero exit code = red X in GitHub Actions