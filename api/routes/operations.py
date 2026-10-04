import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User, Department, Appointment, Bed, OperationalConfig
from api.dependencies import get_current_user, require_operations_manager
from api.schemas.operations import (
    OperationsOverviewResponse, BedOccupancySummary, ForecastResponse,
    SimulationRequest, SimulationResult
)
from src.bed_occupancy import calculate_department_bed_occupancy
from src.resource_planning import calculate_staffing_requirements, simulate_what_if_scenario

router = APIRouter(prefix="/operations", tags=["Hospital Operations"])


@router.get("/overview", response_model=OperationsOverviewResponse)
def get_operations_overview(
    current_user: User = Depends(require_operations_manager),
    db: Session = Depends(get_db)
):
    occ = calculate_department_bed_occupancy()
    total_appts = db.query(Appointment).count()

    # Load forecasting metrics if available
    cache_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "forecast_cache.json")
    forecast_total = 45.0
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            f_data = json.load(f)
            if f_data.get("forecast_7d"):
                forecast_total = f_data["forecast_7d"][0]["predicted_admissions"]

    # Active admissions in hospital
    active_beds = occ["total_occupied_beds"]

    return {
        "total_admissions": 15789,
        "active_admissions": active_beds,
        "today_admissions": int(round(forecast_total)),
        "today_appointments": total_appts,
        "average_waiting_time_minutes": 38.4,
        "total_bed_capacity": occ["total_hospital_beds"],
        "occupied_beds": occ["total_occupied_beds"],
        "available_beds": occ["total_available_beds"],
        "occupancy_rate_pct": occ["hospital_occupancy_rate_pct"],
        "high_occupancy_alert": occ["high_occupancy_warning"],
        "data_freshness": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "data_source_mode": "SYNTHETIC DEMO & LIVE OPERATIONAL REGISTRY"
    }


@router.get("/bed-occupancy")
def get_bed_occupancy_data(
    current_user: User = Depends(require_operations_manager)
):
    return calculate_department_bed_occupancy()


@router.get("/staffing")
def get_staffing_status(
    current_user: User = Depends(require_operations_manager)
):
    occ = calculate_department_bed_occupancy()
    active_census = float(occ["total_occupied_beds"])
    return calculate_staffing_requirements(daily_volume=45.0, active_inpatient_census=active_census)


@router.get("/forecasts", response_model=ForecastResponse)
def get_admissions_forecast(
    horizon: int = Query(7, ge=7, le=30, description="Forecast horizon: 7 or 30 days"),
    current_user: User = Depends(require_operations_manager)
):
    cache_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "forecast_cache.json")
    if not os.path.exists(cache_path):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Forecast models not yet initialized. Please run training pipeline."
        )

    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    points_data = data["forecast_7d"] if horizon == 7 else data["forecast_30d"]

    points = [
        {
            "date": p["date"],
            "day_name": p["day_name"],
            "predicted_admissions": p["predicted_admissions"],
            "lower_bound": p["lower_bound"],
            "upper_bound": p["upper_bound"]
        }
        for p in points_data
    ]

    return {
        "horizon_days": horizon,
        "forecast_model": data.get("best_model_name", "XGBoost"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "points": points,
        "metrics": data.get("test_eval", {}),
        "disclaimer": "Forecasts represent algorithmic projections based on historical cycles and demand trends. Clinical management review is required."
    }


@router.post("/simulate", response_model=SimulationResult)
def run_simulation(
    payload: SimulationRequest,
    current_user: User = Depends(require_operations_manager)
):
    result = simulate_what_if_scenario(
        scenario_preset=payload.scenario_preset,
        demand_multiplier_pct=payload.demand_multiplier_pct,
        los_adjustment_days=payload.los_adjustment_days,
        bed_capacity_override=payload.bed_capacity_override,
        nurse_ratio_override=payload.nurse_ratio_override,
        physician_ratio_override=payload.physician_ratio_override
    )
    return result
