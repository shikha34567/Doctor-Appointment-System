import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic")
os.makedirs(DATA_DIR, exist_ok=True)


def generate_synthetic_hospital_data(
    num_days: int = 365,
    start_date_str: str = "2025-01-01",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a reproducible synthetic hospital operations dataset.
    Simulates patient arrivals, emergency triage priorities, waiting times,
    lengths of stay, bed assignments, and department patient flow.
    Every record is explicitly marked as is_synthetic=True.
    """
    np.random.seed(seed)
    random.seed(seed)

    departments = [
        "Cardiology", "General Medicine", "Neurology", "Orthopedics",
        "Pediatrics", "Dermatology", "ENT", "Ophthalmology",
        "Gastroenterology", "Gynecology & Obstetrics", "Psychiatry"
    ]

    dept_weights = [0.16, 0.20, 0.10, 0.12, 0.10, 0.04, 0.05, 0.04, 0.07, 0.08, 0.04]

    hospital_units = ["Emergency", "ICU", "General Ward", "Surgical"]
    admission_types = ["Emergency", "Elective", "Urgent"]
    admission_type_weights = [0.45, 0.35, 0.20]

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    records = []
    admission_counter = 1000

    for day_offset in range(num_days):
        current_day = start_date + timedelta(days=day_offset)
        day_of_week = current_day.weekday()  # 0=Monday, 6=Sunday

        # Seasonal and weekly demand fluctuation
        # Mondays and Tuesdays typically experience higher surge (+20%)
        # Weekends experience slightly lower elective admissions (-25%)
        base_admissions = 42
        weekday_factor = 1.20 if day_of_week in [0, 1] else (0.80 if day_of_week in [5, 6] else 1.0)
        # Seasonal wave (winter respiratory surge in winter months)
        month_factor = 1.15 if current_day.month in [11, 12, 1] else 1.0
        daily_count = int(np.random.poisson(base_admissions * weekday_factor * month_factor))

        for _ in range(daily_count):
            admission_counter += 1
            admission_id = f"ADM-{admission_counter:06d}"
            patient_id = f"PAT-SYN-{np.random.randint(10000, 99999)}"
            dept = np.random.choice(departments, p=dept_weights)
            adm_type = np.random.choice(admission_types, p=admission_type_weights)

            # Hour of arrival follows realistic bimodal hospital arrival curve (peaks at 10 AM and 6 PM)
            hour_probs = np.array([
                0.015, 0.010, 0.010, 0.010, 0.015, 0.020,
                0.035, 0.055, 0.075, 0.090, 0.095, 0.085,
                0.070, 0.065, 0.060, 0.055, 0.060, 0.075,
                0.070, 0.055, 0.040, 0.030, 0.020, 0.015
            ])
            hour_probs = hour_probs / hour_probs.sum()
            arrival_hour = int(np.random.choice(range(24), p=hour_probs))
            arrival_minute = int(np.random.randint(0, 60))
            admission_dt = current_day.replace(hour=arrival_hour, minute=arrival_minute, second=0)

            # Emergency priority: 1 (Immediate/Resuscitation) to 5 (Non-urgent)
            if adm_type == "Emergency":
                priority = int(np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.15, 0.40, 0.30, 0.10]))
                # Emergency waiting time in minutes depends strongly on priority and arrival hour load
                base_wait = {1: 5.0, 2: 18.0, 3: 45.0, 4: 75.0, 5: 110.0}[priority]
                hour_congestion = 1.35 if (9 <= arrival_hour <= 12 or 17 <= arrival_hour <= 20) else 0.90
                noise = np.random.normal(0, 8.0)
                waiting_time = max(2.0, round(base_wait * hour_congestion + noise, 1))
            else:
                priority = None
                waiting_time = max(5.0, round(np.random.exponential(scale=25.0), 1))

            # Length of Stay (days): log-normal distribution realistic for acute care
            if dept in ["Cardiology", "Neurology", "Gastroenterology"]:
                los = round(float(np.random.lognormal(mean=1.5, sigma=0.5)), 2)
            elif dept in ["Dermatology", "Ophthalmology", "ENT"]:
                los = round(float(np.random.lognormal(mean=0.8, sigma=0.4)), 2)
            else:
                los = round(float(np.random.lognormal(mean=1.3, sigma=0.5)), 2)
            los = max(0.5, min(los, 30.0))  # bound between half a day and 30 days

            discharge_dt = admission_dt + timedelta(hours=int(los * 24))

            # Unit and bed
            if priority in [1, 2] and dept in ["Cardiology", "Neurology", "General Medicine"]:
                unit = "ICU"
            elif adm_type == "Emergency":
                unit = "Emergency"
            elif dept in ["Orthopedics", "General Medicine"]:
                unit = np.random.choice(["General Ward", "Surgical"], p=[0.75, 0.25])
            else:
                unit = "General Ward"

            bed_id = f"BED-{dept[:4].upper()}-{unit[:3].upper()}-{np.random.randint(1, 30):02d}"

            # Shift determination
            if 7 <= arrival_hour < 15:
                shift = "Morning"
                staff_on_duty = int(np.random.randint(12, 18))
            elif 15 <= arrival_hour < 23:
                shift = "Afternoon"
                staff_on_duty = int(np.random.randint(10, 15))
            else:
                shift = "Night"
                staff_on_duty = int(np.random.randint(6, 10))

            age = int(np.random.choice(
                [np.random.randint(1, 18), np.random.randint(18, 65), np.random.randint(65, 92)],
                p=[0.12, 0.58, 0.30]
            ))

            records.append({
                "admission_id": admission_id,
                "patient_id": patient_id,
                "admission_datetime": admission_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "discharge_datetime": discharge_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "department": dept,
                "admission_type": adm_type,
                "emergency_priority": priority,
                "waiting_time_minutes": waiting_time,
                "length_of_stay_days": los,
                "bed_id": bed_id,
                "hospital_unit": unit,
                "staff_shift": shift,
                "staff_on_duty": staff_on_duty,
                "patient_age": age,
                "is_synthetic": True,
                "data_lineage": "Synthetic Reproducible Dataset (Seed 42)"
            })

    df = pd.DataFrame(records)
    output_path = os.path.join(DATA_DIR, "hospital_operations_synthetic.csv")
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} synthetic hospital operational records -> {output_path}")
    return df


if __name__ == "__main__":
    generate_synthetic_hospital_data()
