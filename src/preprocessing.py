import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)


def engineer_patient_level_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts time-based and operational features at the patient admission level.
    """
    df = df.copy()
    df["admission_datetime"] = pd.to_datetime(df["admission_datetime"])

    df["admission_date"] = df["admission_datetime"].dt.date
    df["arrival_hour"] = df["admission_datetime"].dt.hour
    df["day_of_week"] = df["admission_datetime"].dt.dayofweek
    df["day_name"] = df["admission_datetime"].dt.day_name()
    df["month"] = df["admission_datetime"].dt.month
    df["month_name"] = df["admission_datetime"].dt.month_name()
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_monday"] = (df["day_of_week"] == 0).astype(int)

    return df


def aggregate_daily_admissions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates admissions to daily totals and builds chronological time-series
    features: lags (1, 7, 14, 28) and rolling means/stds without future data leakage.
    """
    if "admission_date" not in df.columns:
        df = engineer_patient_level_features(df)

    daily = df.groupby("admission_date").agg(
        total_admissions=("admission_id", "count"),
        emergency_admissions=("admission_type", lambda x: (x == "Emergency").sum()),
        elective_admissions=("admission_type", lambda x: (x == "Elective").sum()),
        urgent_admissions=("admission_type", lambda x: (x == "Urgent").sum()),
        avg_waiting_time=("waiting_time_minutes", "mean"),
        avg_los=("length_of_stay_days", "mean")
    ).reset_index()

    daily["admission_date"] = pd.to_datetime(daily["admission_date"])
    daily = daily.sort_values("admission_date").reset_index(drop=True)

    # Calendar features
    daily["day_of_week"] = daily["admission_date"].dt.dayofweek
    daily["month"] = daily["admission_date"].dt.month
    daily["day_of_month"] = daily["admission_date"].dt.day
    daily["is_weekend"] = daily["day_of_week"].isin([5, 6]).astype(int)
    daily["day_of_year"] = daily["admission_date"].dt.dayofyear

    # Lag features strictly strictly from prior observations (no future leakage)
    for lag in [1, 2, 7, 14, 28]:
        daily[f"lag_{lag}"] = daily["total_admissions"].shift(lag)

    # Rolling window statistics (using closed='left' to exclude current day)
    daily["rolling_mean_7"] = daily["total_admissions"].shift(1).rolling(window=7, min_periods=1).mean()
    daily["rolling_std_7"] = daily["total_admissions"].shift(1).rolling(window=7, min_periods=1).std().fillna(0)
    daily["rolling_mean_14"] = daily["total_admissions"].shift(1).rolling(window=14, min_periods=1).mean()
    daily["rolling_mean_28"] = daily["total_admissions"].shift(1).rolling(window=28, min_periods=1).mean()

    # Drop early warm-up rows where lag 28 is NaN to maintain rigorous training sets
    clean_daily = daily.dropna().reset_index(drop=True)

    daily_path = os.path.join(PROCESSED_DIR, "daily_admissions_timeseries.csv")
    clean_daily.to_csv(daily_path, index=False)
    print(f"Aggregated daily time-series created ({len(clean_daily)} days) -> {daily_path}")
    return clean_daily


def prepare_datasets(clean_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    patient_df = engineer_patient_level_features(clean_df)
    patient_path = os.path.join(PROCESSED_DIR, "patient_admissions_featured.csv")
    patient_df.to_csv(patient_path, index=False)

    daily_df = aggregate_daily_admissions(patient_df)
    return patient_df, daily_df


if __name__ == "__main__":
    from src.data_validation import run_pipeline_validation
    clean_df, _ = run_pipeline_validation()
    prepare_datasets(clean_df)
