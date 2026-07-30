import pandas as pd

def add_local_time(df: pd.DataFrame, tz: str = "Europe/Berlin") -> pd.DataFrame:
    """
    Add a local-time column to a UTC-indexed price DataFrame.
    Safely handles DST transitions (spring-forward gap, autumn-fallback overlap).
    """
    df = df.copy()

    # Timestamps must already be UTC (tz-aware) — this is what fetch.py produces
    if df["timestamp"].dt.tz is None:
        raise ValueError("timestamp column must be tz-aware UTC. Check fetch.py output.")

    # Convert UTC -> local time. pandas handles the DST math correctly here
    # because we're converting *from* an unambiguous UTC timestamp,
    # not trying to parse an ambiguous local time string.
    df["local_time"] = df["timestamp"].dt.tz_convert(tz)

    return df


def validate_no_gaps(df: pd.DataFrame, freq: str = "15min") -> pd.DataFrame:
    """
    Check for missing timestamps in the UTC series (gaps in the data).
    Returns a DataFrame of missing expected timestamps (empty if none).
    """
    df = df.sort_values("timestamp")
    expected = pd.date_range(
        start=df["timestamp"].min(),
        end=df["timestamp"].max(),
        freq=freq,
        tz="UTC",
    )
    missing = expected.difference(df["timestamp"])
    if len(missing) > 0:
        print(f"⚠️  {len(missing)} missing timestamps detected")
    else:
        print("✅ No gaps in UTC timestamp series")
    return pd.DataFrame({"missing_timestamp": missing})


if __name__ == "__main__":
    df = pd.read_parquet("data/processed/prices_de-lu_2026-07-28.parquet")
    df = add_local_time(df)
    print(df.head())
    validate_no_gaps(df)