import pytest
from src.bed_occupancy import calculate_department_bed_occupancy, compute_historical_occupancy_timeseries
from src.resource_planning import calculate_staffing_requirements, simulate_what_if_scenario, compare_all_preset_scenarios


def test_bed_occupancy_calculations():
    res = calculate_department_bed_occupancy()
    assert res["total_hospital_beds"] > 0
    assert res["total_occupied_beds"] >= 0
    assert res["total_available_beds"] >= 0
    assert 0.0 <= res["hospital_occupancy_rate_pct"] <= 100.0
    assert len(res["department_summaries"]) == 11


def test_staffing_requirements():
    staff = calculate_staffing_requirements(
        daily_volume=50.0,
        active_inpatient_census=200.0,
        nurse_icu_ratio=2.0,
        nurse_gen_ratio=4.0,
        physician_ratio=10.0
    )
    assert staff["total_nurses_required_daily"] > 0
    assert staff["total_physicians_required_daily"] > 0
    assert len(staff["shifts"]) == 3


def test_what_if_simulator_presets():
    res_normal = simulate_what_if_scenario(scenario_preset="Normal")
    res_high = simulate_what_if_scenario(scenario_preset="High")

    # High surge must yield higher projected admissions and higher census
    assert res_high["projected_daily_admissions"] > res_normal["projected_daily_admissions"]
    assert res_high["projected_occupied_beds"] > res_normal["projected_occupied_beds"]
    assert res_normal["is_simulated"] == True

    comp_df = compare_all_preset_scenarios()
    assert len(comp_df) == 3
    assert "Scenario" in comp_df.columns
