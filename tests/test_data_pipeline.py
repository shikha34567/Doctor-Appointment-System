import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.synthetic_data import generate_synthetic_hospital_data
from src.data_validation import validate_and_clean_dataset
from src.preprocessing import engineer_patient_level_features, aggregate_daily_admissions


def test_synthetic_data_generation():
    df = generate_synthetic_hospital_data(num_days=10, seed=123)
    assert len(df) > 0
    assert "admission_id" in df.columns
    assert "admission_datetime" in df.columns
    assert "discharge_datetime" in df.columns
    assert "waiting_time_minutes" in df.columns
    assert (df["is_synthetic"] == True).all()


def test_data_validation_clean_pipeline():
    sample_data = pd.DataFrame([
        {
            "admission_id": "ADM-001",
            "patient_id": "P-1",
            "admission_datetime": "2025-01-01 10:00:00",
            "discharge_datetime": "2025-01-03 12:00:00",
            "department": "Cardiology",
            "admission_type": "Emergency",
            "waiting_time_minutes": 25.0,
            "length_of_stay_days": 2.08,
            "hospital_unit": "Emergency",
            "staff_shift": "Morning",
            "staff_on_duty": 14
        },
        # Duplicate row to test deduplication
        {
            "admission_id": "ADM-001",
            "patient_id": "P-1",
            "admission_datetime": "2025-01-01 10:00:00",
            "discharge_datetime": "2025-01-03 12:00:00",
            "department": "Cardiology",
            "admission_type": "Emergency",
            "waiting_time_minutes": 25.0,
            "length_of_stay_days": 2.08,
            "hospital_unit": "Emergency",
            "staff_shift": "Morning",
            "staff_on_duty": 14
        },
        # Invalid timestamp order: discharge before admission
        {
            "admission_id": "ADM-002",
            "patient_id": "P-2",
            "admission_datetime": "2025-01-05 10:00:00",
            "discharge_datetime": "2025-01-04 10:00:00",
            "department": "Neurology",
            "admission_type": "Elective",
            "waiting_time_minutes": 15.0,
            "length_of_stay_days": -1.0,
            "hospital_unit": "General Ward",
            "staff_shift": "Morning",
            "staff_on_duty": 10
        }
    ])

    clean_df, report = validate_and_clean_dataset(sample_data)
    assert report["duplicate_rows_detected"] == 1
    assert report["invalid_timestamp_order_count"] == 1
    assert len(clean_df) == 1
    assert clean_df.iloc[0]["admission_id"] == "ADM-001"


def test_preprocessing_feature_engineering():
    df = pd.DataFrame([
        {
            "admission_id": f"A-{i}",
            "admission_datetime": (datetime(2025, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d 10:00:00"),
            "discharge_datetime": (datetime(2025, 1, 1) + timedelta(days=i+2)).strftime("%Y-%m-%d 10:00:00"),
            "department": "Cardiology",
            "admission_type": "Emergency",
            "waiting_time_minutes": 30.0,
            "length_of_stay_days": 2.0,
            "hospital_unit": "Emergency",
            "staff_shift": "Morning",
            "staff_on_duty": 12
        }
        for i in range(40)
    ])

    feat_df = engineer_patient_level_features(df)
    assert "arrival_hour" in feat_df.columns
    assert "day_of_week" in feat_df.columns
    assert "is_weekend" in feat_df.columns

    daily = aggregate_daily_admissions(feat_df)
    assert "total_admissions" in daily.columns
    assert "lag_1" in daily.columns
    assert "lag_7" in daily.columns
    assert "rolling_mean_7" in daily.columns
