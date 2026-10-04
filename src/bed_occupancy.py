import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import SessionLocal
from database.models import Department, Bed


def calculate_department_bed_occupancy(
    reference_dt: datetime = None,
    admissions_path: str = None
) -> Dict[str, Any]:
    """
    Computes bed occupancy based on concurrent active patient stays
    during the reference timestamp:
    An admission is active at reference_dt IF:
        admission_datetime <= reference_dt <= discharge_datetime
    """
    if admissions_path is None:
        admissions_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "processed", "hospital_operations_clean.csv"
        )

    df = pd.read_csv(admissions_path)
    df["admission_datetime"] = pd.to_datetime(df["admission_datetime"])
    df["discharge_datetime"] = pd.to_datetime(df["discharge_datetime"])

    if reference_dt is None:
        # Default to a recent realistic date in the dataset
        reference_dt = df["admission_datetime"].max() - timedelta(days=2)

    # Active admissions at reference timestamp
    active_mask = (df["admission_datetime"] <= reference_dt) & (df["discharge_datetime"] >= reference_dt)
    active_df = df[active_mask]

    db = SessionLocal()
    try:
        departments = db.query(Department).all()
        dept_configs = {
            d.name: {
                "id": d.id,
                "code": d.code,
                "total_beds": d.total_beds,
                "icu_beds": d.icu_beds,
                "emergency_beds": d.emergency_beds,
                "general_beds": d.general_beds
            }
            for d in departments
        }
    finally:
        db.close()

    dept_summaries = []
    total_hospital_beds = 0
    total_hospital_occupied = 0

    for dept_name, cfg in dept_configs.items():
        dept_active = active_df[active_df["department"] == dept_name]
        occupied = len(dept_active)
        total_beds = cfg["total_beds"]

        # Bound occupied by total beds for standard occupancy metric
        effective_occupied = min(occupied, total_beds)
        available = max(0, total_beds - effective_occupied)
        occupancy_pct = round((occupied / total_beds) * 100.0, 1)

        # ICU specific occupancy
        icu_occupied = len(dept_active[dept_active["hospital_unit"] == "ICU"])
        icu_total = cfg["icu_beds"]
        icu_pct = round((icu_occupied / max(1, icu_total)) * 100.0, 1)

        if occupancy_pct >= 90.0:
            status = "Critical (Overload Risk)"
        elif occupancy_pct >= 80.0:
            status = "Elevated Caution"
        else:
            status = "Normal (Adequate)"

        dept_summaries.append({
            "department": dept_name,
            "code": cfg["code"],
            "total_beds": total_beds,
            "occupied_beds": occupied,
            "available_beds": available,
            "occupancy_pct": occupancy_pct,
            "icu_total": icu_total,
            "icu_occupied": icu_occupied,
            "icu_occupancy_pct": icu_pct,
            "status": status
        })

        total_hospital_beds += total_beds
        total_hospital_occupied += occupied

    total_avail = max(0, total_hospital_beds - total_hospital_occupied)
    hospital_rate = round((total_hospital_occupied / max(1, total_hospital_beds)) * 100.0, 1)

    return {
        "reference_datetime": reference_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "total_hospital_beds": total_hospital_beds,
        "total_occupied_beds": total_hospital_occupied,
        "total_available_beds": total_avail,
        "hospital_occupancy_rate_pct": hospital_rate,
        "high_occupancy_warning": hospital_rate >= 85.0,
        "department_summaries": sorted(dept_summaries, key=lambda x: x["occupancy_pct"], reverse=True)
    }


def compute_historical_occupancy_timeseries(
    admissions_path: str = None,
    days: int = 60
) -> pd.DataFrame:
    """
    Computes daily midday (12:00 PM) bed occupancy over a trailing window of days.
    """
    if admissions_path is None:
        admissions_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "processed", "hospital_operations_clean.csv"
        )

    df = pd.read_csv(admissions_path)
    df["admission_datetime"] = pd.to_datetime(df["admission_datetime"])
    df["discharge_datetime"] = pd.to_datetime(df["discharge_datetime"])

    end_date = df["admission_datetime"].max().date()
    start_date = end_date - timedelta(days=days)

    total_capacity = 365  # Sum of configured beds across all 11 departments
    trend_rows = []

    current = start_date
    while current <= end_date:
        midday_dt = datetime(current.year, current.month, current.day, 12, 0, 0)
        active_count = int(((df["admission_datetime"] <= midday_dt) & (df["discharge_datetime"] >= midday_dt)).sum())
        rate = round((active_count / total_capacity) * 100.0, 1)

        trend_rows.append({
            "date": current.strftime("%Y-%m-%d"),
            "occupied_beds": active_count,
            "total_capacity": total_capacity,
            "occupancy_rate_pct": rate
        })
        current += timedelta(days=1)

    return pd.DataFrame(trend_rows)


if __name__ == "__main__":
    res = calculate_department_bed_occupancy()
    print("Bed Occupancy:", res["hospital_occupancy_rate_pct"], "%")
