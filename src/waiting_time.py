import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def train_waiting_time_pipeline(
    data_path: str = None
) -> Dict[str, Any]:
    """
    Trains and validates models to estimate emergency department waiting times.
    Target: waiting_time_minutes.
    Features: arrival_hour, day_of_week, emergency_priority, department,
              staff_on_duty, patient_age, is_weekend.
    Evaluates Linear Regression, Random Forest, Gradient Boosting, XGBoost.
    """
    if data_path is None:
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "processed", "hospital_operations_clean.csv"
        )

    df = pd.read_csv(data_path)
    df["admission_datetime"] = pd.to_datetime(df["admission_datetime"])

    # Focus on emergency department triage arrivals where waiting times are critical
    er_df = df[df["admission_type"] == "Emergency"].copy()
    if len(er_df) == 0:
        er_df = df.copy()

    er_df["arrival_hour"] = er_df["admission_datetime"].dt.hour
    er_df["day_of_week"] = er_df["admission_datetime"].dt.dayofweek
    er_df["is_weekend"] = er_df["day_of_week"].isin([5, 6]).astype(int)

    # Convert emergency priority to numeric (1=Resuscitation to 5=Non-urgent)
    er_df["emergency_priority"] = pd.to_numeric(er_df["emergency_priority"], errors="coerce").fillna(3)

    # One-hot encode department
    dept_dummies = pd.get_dummies(er_df["department"], prefix="dept", drop_first=True, dtype=int)

    feature_df = pd.concat([
        er_df[["arrival_hour", "day_of_week", "is_weekend", "emergency_priority", "staff_on_duty", "patient_age"]],
        dept_dummies
    ], axis=1)

    y = er_df["waiting_time_minutes"].values
    X = feature_df

    # Split: 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    models = {
        "Linear_Regression": LinearRegression(),
        "Random_Forest": RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
        "Gradient_Boosting": GradientBoostingRegressor(n_estimators=100, learning_rate=0.08, max_depth=5, random_state=42)
    }

    if HAS_XGBOOST:
        models["XGBoost"] = xgb.XGBRegressor(n_estimators=100, learning_rate=0.08, max_depth=5, random_state=42)

    eval_results = {}
    best_model_name = None
    lowest_mae = float("inf")
    best_model = None

    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        eval_results[name] = {
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "R2": round(r2, 4)
        }

        if mae < lowest_mae:
            lowest_mae = mae
            best_model_name = name
            best_model = model

    # Feature importance
    if hasattr(best_model, "feature_importances_"):
        fi_vals = best_model.feature_importances_
        feature_importance = dict(zip(X.columns, [round(float(v), 4) for v in fi_vals]))
        # Sort by importance descending
        sorted_fi = dict(sorted(feature_importance.items(), key=lambda item: item[1], reverse=True))
    else:
        sorted_fi = {}

    # Sample actual vs predicted for interactive plotting
    sample_preds = best_model.predict(X_test.iloc[:150])
    sample_comparison = [
        {
            "actual": round(float(act), 1),
            "predicted": round(float(prd), 1),
            "priority": int(X_test.iloc[idx]["emergency_priority"]),
            "hour": int(X_test.iloc[idx]["arrival_hour"])
        }
        for idx, (act, prd) in enumerate(zip(y_test[:150], sample_preds))
    ]

    # Save model artifact
    model_artifact_path = os.path.join(MODELS_DIR, "waiting_time_model.joblib")
    joblib.dump({
        "model": best_model,
        "model_name": best_model_name,
        "feature_names": list(X.columns),
        "trained_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }, model_artifact_path)

    summary = {
        "best_model_name": best_model_name,
        "evaluation_metrics": eval_results,
        "best_model_metrics": eval_results[best_model_name],
        "feature_importance": sorted_fi,
        "sample_comparison": sample_comparison,
        "disclaimer": "Operational estimation only. These values represent predictive queue estimates based on operational conditions and priority scoring, NOT guaranteed clinical waiting times."
    }

    cache_path = os.path.join(MODELS_DIR, "waiting_time_cache.json")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Waiting time pipeline trained. Best: {best_model_name} (MAE: {eval_results[best_model_name]['MAE']} min, R2: {eval_results[best_model_name]['R2']})")
    return summary


def predict_waiting_time(
    arrival_hour: int,
    day_of_week: int,
    emergency_priority: int,
    department: str,
    staff_on_duty: int = 12,
    patient_age: int = 45
) -> Dict[str, Any]:
    """
    Predicts single patient waiting time estimate given real-time queue attributes.
    """
    model_artifact_path = os.path.join(MODELS_DIR, "waiting_time_model.joblib")
    if not os.path.exists(model_artifact_path):
        train_waiting_time_pipeline()

    artifact = joblib.load(model_artifact_path)
    model = artifact["model"]
    feature_names = artifact["feature_names"]

    row_data = {
        "arrival_hour": arrival_hour,
        "day_of_week": day_of_week,
        "is_weekend": 1 if day_of_week in [5, 6] else 0,
        "emergency_priority": emergency_priority,
        "staff_on_duty": staff_on_duty,
        "patient_age": patient_age
    }
    for col in feature_names:
        if col.startswith("dept_"):
            dept_name = col.replace("dept_", "")
            row_data[col] = 1 if department == dept_name else 0

    input_df = pd.DataFrame([row_data])
    for col in feature_names:
        if col not in input_df.columns:
            input_df[col] = 0
    input_df = input_df[feature_names]

    predicted_minutes = float(model.predict(input_df)[0])
    predicted_minutes = max(3.0, round(predicted_minutes, 1))

    return {
        "predicted_waiting_time_minutes": predicted_minutes,
        "priority_level": emergency_priority,
        "estimated_range": f"{max(2.0, predicted_minutes - 8.0):.0f} - {predicted_minutes + 10.0:.0f} mins",
        "is_estimate": True
    }


if __name__ == "__main__":
    train_waiting_time_pipeline()
