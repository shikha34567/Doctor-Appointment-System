import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple

PROCESSED_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

REQUIRED_COLUMNS = [
    "admission_id", "patient_id", "admission_datetime", "discharge_datetime",
    "department", "admission_type", "waiting_time_minutes", "length_of_stay_days",
    "hospital_unit", "staff_shift", "staff_on_duty"
]


def validate_and_clean_dataset(
    raw_df: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates hospital operations data integrity:
    - Verifies schema and required columns
    - Parses and validates timestamps (admission_datetime < discharge_datetime)
    - Removes duplicate admissions
    - Verifies waiting times and lengths of stay boundaries
    - Imputes non-critical missing values with explicit tags
    - Produces a comprehensive Data Quality scorecard
    """
    quality_report = {
        "raw_record_count": len(raw_df),
        "duplicate_rows_detected": 0,
        "invalid_timestamp_order_count": 0,
        "negative_wait_time_count": 0,
        "outlier_los_count": 0,
        "missing_values_by_column": {},
        "cleaned_record_count": 0,
        "data_quality_score_pct": 100.0,
        "validation_passed": True
    }

    # 1. Verify schema
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in raw_df.columns]
    if missing_cols:
        quality_report["validation_passed"] = False
        quality_report["error"] = f"Missing required columns: {missing_cols}"
        return pd.DataFrame(), quality_report

    df = raw_df.copy()

    # 2. Check duplicates on admission_id
    duplicate_mask = df.duplicated(subset=["admission_id"], keep="first")
    quality_report["duplicate_rows_detected"] = int(duplicate_mask.sum())
    if duplicate_mask.sum() > 0:
        df = df[~duplicate_mask]

    # 3. Missing values check
    for col in df.columns:
        m_count = int(df[col].isna().sum())
        if m_count > 0:
            quality_report["missing_values_by_column"][col] = m_count

    # 4. Parse timestamps & check ordering
    df["admission_datetime"] = pd.to_datetime(df["admission_datetime"], errors="coerce")
    df["discharge_datetime"] = pd.to_datetime(df["discharge_datetime"], errors="coerce")

    invalid_ts = df["admission_datetime"].isna() | df["discharge_datetime"].isna()
    order_inversion = df["discharge_datetime"] <= df["admission_datetime"]
    invalid_mask = invalid_ts | order_inversion
    quality_report["invalid_timestamp_order_count"] = int(invalid_mask.sum())

    # Filter out records where timestamps are fundamentally invalid
    df = df[~invalid_mask]

    # 5. Sanitize waiting time and length of stay
    df["waiting_time_minutes"] = pd.to_numeric(df["waiting_time_minutes"], errors="coerce")
    neg_wait = df["waiting_time_minutes"] < 0
    quality_report["negative_wait_time_count"] = int(neg_wait.sum())
    df.loc[neg_wait, "waiting_time_minutes"] = 0.0

    df["length_of_stay_days"] = pd.to_numeric(df["length_of_stay_days"], errors="coerce")
    # Identify impossible LOS (> 60 days in general acute ward without chronic transfer)
    outlier_los = (df["length_of_stay_days"] > 60.0) | (df["length_of_stay_days"] <= 0.0)
    quality_report["outlier_los_count"] = int(outlier_los.sum())
    df = df[~outlier_los]

    # Fill optional triage priority for non-emergency if missing
    if "emergency_priority" in df.columns:
        df["emergency_priority"] = df["emergency_priority"].fillna(0).astype(int)
    else:
        df["emergency_priority"] = 0

    quality_report["cleaned_record_count"] = len(df)
    # Calculate quality score
    flaws = (
        quality_report["duplicate_rows_detected"] +
        quality_report["invalid_timestamp_order_count"] +
        quality_report["negative_wait_time_count"] +
        quality_report["outlier_los_count"]
    )
    score = max(0.0, round(100.0 * (1.0 - (flaws / max(1, quality_report["raw_record_count"]))), 2))
    quality_report["data_quality_score_pct"] = score

    return df, quality_report


def run_pipeline_validation(
    raw_path: str = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    if raw_path is None:
        raw_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "synthetic", "hospital_operations_synthetic.csv"
        )

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}")

    raw_df = pd.read_csv(raw_path)
    clean_df, report = validate_and_clean_dataset(raw_df)

    processed_path = os.path.join(PROCESSED_DATA_DIR, "hospital_operations_clean.csv")
    clean_df.to_csv(processed_path, index=False)
    print(f"Validation finished. Score: {report['data_quality_score_pct']}%. Saved -> {processed_path}")
    return clean_df, report


if __name__ == "__main__":
    run_pipeline_validation()
