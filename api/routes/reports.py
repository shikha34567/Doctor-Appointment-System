import os
import io
import pandas as pd
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse

from database.models import User
from api.dependencies import require_operations_manager
from src.bed_occupancy import calculate_department_bed_occupancy, compute_historical_occupancy_timeseries
from src.resource_planning import compare_all_preset_scenarios

router = APIRouter(prefix="/reports", tags=["Data Reports & Power BI Export"])


@router.get("/admissions")
def download_admissions_report(current_user: User = Depends(require_operations_manager)):
    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "processed", "daily_admissions_timeseries.csv"
    )
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame([{"date": "2025-10-01", "total_admissions": 45}])

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = Response(content=stream.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=hospital_admissions_trends.csv"
    return response


@router.get("/occupancy")
def download_bed_occupancy_report(current_user: User = Depends(require_operations_manager)):
    trend_df = compute_historical_occupancy_timeseries(days=60)
    stream = io.StringIO()
    trend_df.to_csv(stream, index=False)
    response = Response(content=stream.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=bed_occupancy_history.csv"
    return response


@router.get("/resources")
def download_resources_report(current_user: User = Depends(require_operations_manager)):
    comp_df = compare_all_preset_scenarios()
    stream = io.StringIO()
    comp_df.to_csv(stream, index=False)
    response = Response(content=stream.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=resource_scenarios_comparison.csv"
    return response
