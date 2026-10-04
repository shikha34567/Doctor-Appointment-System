import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import SessionLocal
from database.models import Department


def calculate_staffing_requirements(
    daily_volume: float = 45.0,
    active_inpatient_census: float = 210.0,
    nurse_icu_ratio: float = 2.0,       # 1 nurse per 2 ICU patients
    nurse_gen_ratio: float = 4.0,       # 1 nurse per 4 General patients
    physician_ratio: float = 10.0       # 1 physician per 10 active patients
) -> Dict[str, Any]:
    """
    Calculates staffing requirements across Morning, Afternoon, and Night shifts
    using configurable operational planning ratios.
    """
    # Active census distribution: ~15% in ICU, ~85% in General/Other
    icu_patients = active_inpatient_census * 0.15
    gen_patients = active_inpatient_census * 0.85

    # 24-hour total nursing hours requirement
    nurses_icu_needed = int(np.ceil(icu_patients / nurse_icu_ratio))
    nurses_gen_needed = int(np.ceil(gen_patients / nurse_gen_ratio))
    total_nurses_needed_day = nurses_icu_needed + nurses_gen_needed

    physicians_needed_day = int(np.ceil(active_inpatient_census / physician_ratio))

    # Shift distribution weights
    shift_weights = {
        "Morning": {"nurse_weight": 0.45, "phys_weight": 0.50},
        "Afternoon": {"nurse_weight": 0.35, "phys_weight": 0.35},
        "Night": {"nurse_weight": 0.20, "phys_weight": 0.15}
    }

    shift_breakdown = []
    baseline_roster = {
        "Morning": {"nurses": 42, "physicians": 14},
        "Afternoon": {"nurses": 32, "physicians": 9},
        "Night": {"nurses": 18, "physicians": 4}
    }

    total_nurses_shortage = 0
    total_physicians_shortage = 0

    for shift, weights in shift_weights.items():
        req_nurses = int(np.ceil(total_nurses_needed_day * weights["nurse_weight"]))
        req_phys = int(np.ceil(physicians_needed_day * weights["phys_weight"]))

        curr_nurses = baseline_roster[shift]["nurses"]
        curr_phys = baseline_roster[shift]["physicians"]

        nurse_var = curr_nurses - req_nurses
        phys_var = curr_phys - req_phys

        if nurse_var < 0:
            total_nurses_shortage += abs(nurse_var)
        if phys_var < 0:
            total_physicians_shortage += abs(phys_var)

        shift_breakdown.append({
            "shift": shift,
            "required_nurses": req_nurses,
            "on_duty_nurses": curr_nurses,
            "nurse_variance": nurse_var,
            "required_physicians": req_phys,
            "on_duty_physicians": curr_phys,
            "physician_variance": phys_var,
            "alert": "Staff Deficit" if (nurse_var < 0 or phys_var < 0) else "Adequate"
        })

    return {
        "daily_admission_volume": daily_volume,
        "active_inpatient_census": active_inpatient_census,
        "total_nurses_required_daily": total_nurses_needed_day,
        "total_physicians_required_daily": physicians_needed_day,
        "total_nurses_shortage": total_nurses_shortage,
        "total_physicians_shortage": total_physicians_shortage,
        "shifts": shift_breakdown,
        "planning_assumptions": {
            "nurse_icu_ratio": f"1:{nurse_icu_ratio}",
            "nurse_general_ratio": f"1:{nurse_gen_ratio}",
            "physician_patient_ratio": f"1:{physician_ratio}"
        }
    }


def simulate_what_if_scenario(
    scenario_preset: str = "Normal",
    demand_multiplier_pct: float = 0.0,
    los_adjustment_days: float = 0.0,
    bed_capacity_override: int = None,
    nurse_ratio_override: float = None,
    physician_ratio_override: float = None
) -> Dict[str, Any]:
    """
    Executes what-if resource scenario simulation.
    Adjusts admission volume, length of stay, bed capacities, and nurse ratios.
    Calculates projected bed occupancy, staffing deficits, and risk level.
    """
    presets = {
        "Low": {"demand_pct": -20.0, "los_adj": -0.5, "desc": "Low Demand Season / Off-peak"},
        "Normal": {"demand_pct": 0.0, "los_adj": 0.0, "desc": "Baseline Operating Conditions"},
        "High": {"demand_pct": 35.0, "los_adj": 1.2, "desc": "Seasonal Respiratory / Epidemic Surge"}
    }

    if scenario_preset in presets:
        active_preset = presets[scenario_preset]
        effective_demand_pct = active_preset["demand_pct"] if demand_multiplier_pct == 0.0 else demand_multiplier_pct
        effective_los_adj = active_preset["los_adj"] if los_adjustment_days == 0.0 else los_adjustment_days
    else:
        effective_demand_pct = demand_multiplier_pct
        effective_los_adj = los_adjustment_days

    # Baseline operating parameters
    baseline_daily_admissions = 45.0
    baseline_los = 4.4  # days
    baseline_capacity = 365  # total hospital beds

    total_beds = bed_capacity_override if bed_capacity_override is not None else baseline_capacity
    projected_daily_admissions = round(baseline_daily_admissions * (1.0 + (effective_demand_pct / 100.0)), 1)
    projected_los = max(1.0, round(baseline_los + effective_los_adj, 2))

    # Little's Law for average census in steady-state: L = lambda * W
    # Projected concurrent census = Daily Admissions * Average Length of Stay
    projected_occupied_beds = round(projected_daily_admissions * projected_los, 1)
    projected_occupancy_rate = round((projected_occupied_beds / max(1, total_beds)) * 100.0, 1)

    bed_shortage = max(0, int(np.ceil(projected_occupied_beds - total_beds)))

    # Staffing calculations
    nurse_ratio = nurse_ratio_override if nurse_ratio_override is not None else 3.8
    phys_ratio = physician_ratio_override if physician_ratio_override is not None else 10.0

    nurses_required = int(np.ceil(projected_occupied_beds / nurse_ratio))
    physicians_required = int(np.ceil(projected_occupied_beds / phys_ratio))

    available_nurses = 92
    available_physicians = 27

    nurse_deficit = max(0, nurses_required - available_nurses)
    phys_deficit = max(0, physicians_required - available_physicians)

    if projected_occupancy_rate > 95.0 or bed_shortage > 0 or nurse_deficit > 10:
        risk_level = "Severe Shortage (High Alert)"
    elif projected_occupancy_rate > 85.0 or nurse_deficit > 0:
        risk_level = "Moderate Strain (Caution)"
    else:
        risk_level = "Low Risk (Optimal)"

    recommendations = []
    if bed_shortage > 0:
        recommendations.append(f"Immediate surge bed activation required: {bed_shortage} additional beds needed.")
    if projected_occupancy_rate > 85.0:
        recommendations.append("Prioritize expedited discharge rounds and step-down unit transfers to preserve emergency capacity.")
    if nurse_deficit > 0:
        recommendations.append(f"Authorize {nurse_deficit} auxiliary nursing shifts or temporary locum nurse mobilization.")
    if phys_deficit > 0:
        recommendations.append(f"On-call physician rota mobilization recommended ({phys_deficit} additional cover required).")
    if not recommendations:
        recommendations.append("Hospital operations remain well within safety thresholds. Standard operating roster sufficient.")

    return {
        "scenario_name": scenario_preset,
        "demand_multiplier_pct": effective_demand_pct,
        "los_adjustment_days": effective_los_adj,
        "baseline_daily_admissions": baseline_daily_admissions,
        "projected_daily_admissions": projected_daily_admissions,
        "projected_average_los": projected_los,
        "total_bed_capacity": total_beds,
        "projected_occupied_beds": projected_occupied_beds,
        "projected_occupancy_rate_pct": projected_occupancy_rate,
        "bed_shortage": bed_shortage,
        "nurses_required": nurses_required,
        "physicians_required": physicians_required,
        "nurse_deficit": nurse_deficit,
        "physician_deficit": phys_deficit,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "is_simulated": True
    }


def compare_all_preset_scenarios() -> pd.DataFrame:
    """
    Generates side-by-side comparison for Low, Normal, and High demand presets.
    """
    scenarios = ["Low", "Normal", "High"]
    rows = []
    for sc in scenarios:
        res = simulate_what_if_scenario(scenario_preset=sc)
        rows.append({
            "Scenario": sc,
            "Daily Admissions": res["projected_daily_admissions"],
            "Avg LOS (Days)": res["projected_average_los"],
            "Projected Census": res["projected_occupied_beds"],
            "Occupancy Rate (%)": f"{res['projected_occupancy_rate_pct']}%",
            "Bed Deficit": res["bed_shortage"],
            "Nurse Deficit": res["nurse_deficit"],
            "Risk Level": res["risk_level"]
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    comp = compare_all_preset_scenarios()
    print(comp)
