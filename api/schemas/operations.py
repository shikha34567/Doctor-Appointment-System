from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class OperationsOverviewResponse(BaseModel):
    total_admissions: int
    active_admissions: int
    today_admissions: int
    today_appointments: int
    average_waiting_time_minutes: float
    total_bed_capacity: int
    occupied_beds: int
    available_beds: int
    occupancy_rate_pct: float
    high_occupancy_alert: bool
    data_freshness: str
    data_source_mode: str


class BedOccupancySummary(BaseModel):
    department: str
    code: str
    total_beds: int
    occupied_beds: int
    available_beds: int
    occupancy_pct: float
    icu_occupancy_pct: float
    status: str  # 'Normal', 'Elevated', 'Critical'


class StaffingSummary(BaseModel):
    department: str
    shift: str
    staff_type: str
    staff_on_duty: int
    required_staff: int
    variance: int
    status: str


class ForecastPoint(BaseModel):
    date: str
    day_name: str
    predicted_admissions: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    horizon_days: int
    forecast_model: str
    generated_at: str
    points: List[ForecastPoint]
    metrics: Dict[str, float]
    disclaimer: str


class SimulationRequest(BaseModel):
    scenario_preset: Optional[str] = "Normal"  # 'Low', 'Normal', 'High', 'Custom'
    demand_multiplier_pct: float = Field(default=0.0, ge=-50.0, le=100.0)  # -50% to +100%
    los_adjustment_days: float = Field(default=0.0, ge=-3.0, le=5.0)
    bed_capacity_override: Optional[int] = Field(default=None, ge=10, le=1000)
    nurse_ratio_override: Optional[float] = Field(default=None, ge=1.0, le=10.0)
    physician_ratio_override: Optional[float] = Field(default=None, ge=2.0, le=20.0)


class SimulationResult(BaseModel):
    scenario_name: str
    baseline_daily_admissions: float
    projected_daily_admissions: float
    average_length_of_stay: float
    total_bed_capacity: int
    projected_occupied_beds: float
    projected_occupancy_rate_pct: float
    bed_shortage: int
    nurses_required: int
    physicians_required: int
    nurses_shortage: int
    physicians_shortage: int
    risk_level: str  # 'Low Risk', 'Moderate Risk', 'Severe Shortage'
    recommendations: List[str]
    is_simulated: bool = True
