import pytest
import os
import joblib
import pandas as pd
import numpy as np

from src.forecasting import calculate_mape, train_admission_forecasting_pipeline
from src.waiting_time import predict_waiting_time, train_waiting_time_pipeline


def test_safe_mape_calculation():
    y_true = np.array([10.0, 20.0, 0.0, 40.0])
    y_pred = np.array([12.0, 18.0, 5.0, 44.0])
    mape = calculate_mape(y_true, y_pred)
    assert isinstance(mape, float)
    assert not np.isnan(mape)
    assert not np.isinf(mape)
    assert mape > 0.0


def test_forecasting_pipeline_artifacts():
    summary = train_admission_forecasting_pipeline()
    assert "best_model_name" in summary
    assert "test_eval" in summary
    assert "MAE" in summary["test_eval"]
    assert "forecast_7d" in summary
    assert len(summary["forecast_7d"]) == 7
    assert len(summary["forecast_30d"]) == 30

    # Ensure artifact exists
    artifact_path = os.path.join(os.path.dirname(__file__), "..", "models", "admission_forecast_model.joblib")
    assert os.path.exists(artifact_path)
    loaded = joblib.load(artifact_path)
    assert "model" in loaded


def test_waiting_time_prediction():
    pred = predict_waiting_time(
        arrival_hour=10,
        day_of_week=0,
        emergency_priority=2,
        department="Cardiology",
        staff_on_duty=14,
        patient_age=50
    )
    assert "predicted_waiting_time_minutes" in pred
    assert pred["predicted_waiting_time_minutes"] > 0
    assert pred["is_estimate"] == True
