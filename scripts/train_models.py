import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.synthetic_data import generate_synthetic_hospital_data
from src.data_validation import run_pipeline_validation
from src.preprocessing import prepare_datasets
from src.forecasting import train_admission_forecasting_pipeline
from src.waiting_time import train_waiting_time_pipeline


def train_all_models():
    print("=== Step 1: Generating Synthetic Data ===")
    generate_synthetic_hospital_data()

    print("=== Step 2: Validating and Cleaning Data ===")
    clean_df, report = run_pipeline_validation()
    print(f"Data Quality Score: {report['data_quality_score_pct']}%")

    print("=== Step 3: Preprocessing and Engineering Time-Series Features ===")
    prepare_datasets(clean_df)

    print("=== Step 4: Training Patient Admission Forecasting Pipeline ===")
    forecast_results = train_admission_forecasting_pipeline()

    print("=== Step 5: Training Emergency Waiting-Time Pipeline ===")
    wait_results = train_waiting_time_pipeline()

    print("\n[SUCCESS] All Machine Learning Models and Analytics Pipelines Successfully Trained and Persisted!")


if __name__ == "__main__":
    train_all_models()
