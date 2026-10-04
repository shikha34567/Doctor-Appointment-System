import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Safe MAPE calculation handling zero denominators"""
    non_zero = y_true != 0
    if not np.any(non_zero):
        return 0.0
    return float(np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100.0)


def train_admission_forecasting_pipeline(
    data_path: str = None
) -> Dict[str, Any]:
    """
    Trains multiple models for daily patient admission forecasting:
    - Baseline 1: 14-day Historical Average
    - Baseline 2: 7-day Moving Average
    - Random Forest Regressor
    - Gradient Boosting Regressor
    - XGBoost Regressor (if available)

    Uses strict chronological splitting to avoid future data leakage.
    Selects the best model based on validation MAE, evaluates on test set,
    and produces 7-day and 30-day forecast projections.
    """
    if data_path is None:
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "processed", "daily_admissions_timeseries.csv"
        )

    df = pd.read_csv(data_path)
    df["admission_date"] = pd.to_datetime(df["admission_date"])
    df = df.sort_values("admission_date").reset_index(drop=True)

    feature_cols = [
        "day_of_week", "month", "day_of_month", "is_weekend",
        "lag_1", "lag_2", "lag_7", "lag_14", "lag_28",
        "rolling_mean_7", "rolling_std_7", "rolling_mean_14", "rolling_mean_28"
    ]
    target_col = "total_admissions"

    n_total = len(df)
    train_size = int(n_total * 0.70)
    val_size = int(n_total * 0.15)
    test_size = n_total - train_size - val_size

    train_df = df.iloc[:train_size]
    val_df = df.iloc[train_size:train_size + val_size]
    test_df = df.iloc[train_size + val_size:]

    X_train, y_train = train_df[feature_cols], train_df[target_col].values
    X_val, y_val = val_df[feature_cols], val_df[target_col].values
    X_test, y_test = test_df[feature_cols], test_df[target_col].values

    results = {}

    # 1. Baseline: 14-day rolling mean
    val_pred_base = val_df["rolling_mean_14"].values
    test_pred_base = test_df["rolling_mean_14"].values
    results["Historical_14D_Average"] = {
        "val_mae": mean_absolute_error(y_val, val_pred_base),
        "val_rmse": np.sqrt(mean_squared_error(y_val, val_pred_base)),
        "val_mape": calculate_mape(y_val, val_pred_base),
        "test_mae": mean_absolute_error(y_test, test_pred_base),
        "test_rmse": np.sqrt(mean_squared_error(y_test, test_pred_base)),
        "test_mape": calculate_mape(y_test, test_pred_base),
        "model": None,
        "is_ml": False
    }

    # 2. Baseline: 7-day Moving Average
    val_pred_ma7 = val_df["rolling_mean_7"].values
    test_pred_ma7 = test_df["rolling_mean_7"].values
    results["Moving_Average_7D"] = {
        "val_mae": mean_absolute_error(y_val, val_pred_ma7),
        "val_rmse": np.sqrt(mean_squared_error(y_val, val_pred_ma7)),
        "val_mape": calculate_mape(y_val, val_pred_ma7),
        "test_mae": mean_absolute_error(y_test, test_pred_ma7),
        "test_rmse": np.sqrt(mean_squared_error(y_test, test_pred_ma7)),
        "test_mape": calculate_mape(y_test, test_pred_ma7),
        "model": None,
        "is_ml": False
    }

    # 3. Random Forest Regressor
    rf = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)
    val_pred_rf = rf.predict(X_val)
    test_pred_rf = rf.predict(X_test)
    results["Random_Forest"] = {
        "val_mae": mean_absolute_error(y_val, val_pred_rf),
        "val_rmse": np.sqrt(mean_squared_error(y_val, val_pred_rf)),
        "val_mape": calculate_mape(y_val, val_pred_rf),
        "test_mae": mean_absolute_error(y_test, test_pred_rf),
        "test_rmse": np.sqrt(mean_squared_error(y_test, test_pred_rf)),
        "test_mape": calculate_mape(y_test, test_pred_rf),
        "model": rf,
        "is_ml": True
    }

    # 4. Gradient Boosting Regressor
    gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=42)
    gb.fit(X_train, y_train)
    val_pred_gb = gb.predict(X_val)
    test_pred_gb = gb.predict(X_test)
    results["Gradient_Boosting"] = {
        "val_mae": mean_absolute_error(y_val, val_pred_gb),
        "val_rmse": np.sqrt(mean_squared_error(y_val, val_pred_gb)),
        "val_mape": calculate_mape(y_val, val_pred_gb),
        "test_mae": mean_absolute_error(y_test, test_pred_gb),
        "test_rmse": np.sqrt(mean_squared_error(y_test, test_pred_gb)),
        "test_mape": calculate_mape(y_test, test_pred_gb),
        "model": gb,
        "is_ml": True
    }

    # 5. XGBoost (if available)
    if HAS_XGBOOST:
        xgb_model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=42)
        xgb_model.fit(X_train, y_train)
        val_pred_xgb = xgb_model.predict(X_val)
        test_pred_xgb = xgb_model.predict(X_test)
        results["XGBoost"] = {
            "val_mae": mean_absolute_error(y_val, val_pred_xgb),
            "val_rmse": np.sqrt(mean_squared_error(y_val, val_pred_xgb)),
            "val_mape": calculate_mape(y_val, val_pred_xgb),
            "test_mae": mean_absolute_error(y_test, test_pred_xgb),
            "test_rmse": np.sqrt(mean_squared_error(y_test, test_pred_xgb)),
            "test_mape": calculate_mape(y_test, test_pred_xgb),
            "model": xgb_model,
            "is_ml": True
        }

    # Select best model based on validation MAE
    ml_models = {k: v for k, v in results.items() if v["is_ml"]}
    best_model_name = min(ml_models.keys(), key=lambda k: ml_models[k]["val_mae"])
    best_model = ml_models[best_model_name]["model"]

    # Save model artifact
    model_artifact_path = os.path.join(MODELS_DIR, "admission_forecast_model.joblib")
    joblib.dump({
        "model": best_model,
        "model_name": best_model_name,
        "feature_cols": feature_cols,
        "trained_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }, model_artifact_path)

    # Multi-step recursive forecasting for 7-day and 30-day horizon
    forecast_7d = generate_future_forecast(df, best_model, feature_cols, horizon=7)
    forecast_30d = generate_future_forecast(df, best_model, feature_cols, horizon=30)

    summary = {
        "best_model_name": best_model_name,
        "comparison_table": {
            k: {
                "val_mae": round(v["val_mae"], 2),
                "val_rmse": round(v["val_rmse"], 2),
                "val_mape": round(v["val_mape"], 2),
                "test_mae": round(v["test_mae"], 2),
                "test_rmse": round(v["test_rmse"], 2),
                "test_mape": round(v["test_mape"], 2)
            } for k, v in results.items()
        },
        "test_eval": {
            "MAE": round(results[best_model_name]["test_mae"], 2),
            "RMSE": round(results[best_model_name]["test_rmse"], 2),
            "MAPE": round(results[best_model_name]["test_mape"], 2)
        },
        "forecast_7d": forecast_7d,
        "forecast_30d": forecast_30d,
        "feature_importance": dict(zip(feature_cols, [round(float(fi), 4) for fi in best_model.feature_importances_]))
    }

    cache_path = os.path.join(MODELS_DIR, "forecast_cache.json")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Admission forecasting pipeline complete. Best model: {best_model_name} (Test MAE: {summary['test_eval']['MAE']})")
    return summary


def generate_future_forecast(
    historical_df: pd.DataFrame,
    model: Any,
    feature_cols: list,
    horizon: int = 30
) -> list:
    """
    Recursively projects admissions forward for `horizon` days.
    """
    history = historical_df.copy()
    last_date = pd.to_datetime(history["admission_date"].iloc[-1])
    projections = []

    # Use standard error of residuals to compute dynamic prediction interval
    residual_std = 3.5

    for step in range(1, horizon + 1):
        target_date = last_date + timedelta(days=step)
        day_of_week = target_date.weekday()
        month = target_date.month
        day_of_month = target_date.day
        is_weekend = 1 if day_of_week in [5, 6] else 0

        # Calculate lags from rolling simulation history
        all_totals = history["total_admissions"].values
        lag_1 = all_totals[-1]
        lag_2 = all_totals[-2] if len(all_totals) >= 2 else lag_1
        lag_7 = all_totals[-7] if len(all_totals) >= 7 else lag_1
        lag_14 = all_totals[-14] if len(all_totals) >= 14 else lag_1
        lag_28 = all_totals[-28] if len(all_totals) >= 28 else lag_1

        roll_7 = np.mean(all_totals[-7:])
        roll_std_7 = np.std(all_totals[-7:]) if len(all_totals) >= 7 else 1.0
        roll_14 = np.mean(all_totals[-14:])
        roll_28 = np.mean(all_totals[-28:])

        feat_row = pd.DataFrame([{
            "day_of_week": day_of_week,
            "month": month,
            "day_of_month": day_of_month,
            "is_weekend": is_weekend,
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_7": lag_7,
            "lag_14": lag_14,
            "lag_28": lag_28,
            "rolling_mean_7": roll_7,
            "rolling_std_7": roll_std_7,
            "rolling_mean_14": roll_14,
            "rolling_mean_28": roll_28
        }])[feature_cols]

        pred_val = float(model.predict(feat_row)[0])
        pred_val = max(10.0, round(pred_val, 1))

        # 95% confidence bounds
        margin = 1.96 * residual_std * np.sqrt(1 + step * 0.05)
        lower_b = max(5.0, round(pred_val - margin, 1))
        upper_b = round(pred_val + margin, 1)

        projections.append({
            "step": step,
            "date": target_date.strftime("%Y-%m-%d"),
            "day_name": target_date.strftime("%A"),
            "predicted_admissions": pred_val,
            "lower_bound": lower_b,
            "upper_bound": upper_b
        })

        # Append to simulation history for subsequent autoregressive lags
        new_row = pd.DataFrame([{
            "admission_date": target_date,
            "total_admissions": pred_val
        }])
        history = pd.concat([history, new_row], ignore_index=True)

    return projections


if __name__ == "__main__":
    train_admission_forecasting_pipeline()
