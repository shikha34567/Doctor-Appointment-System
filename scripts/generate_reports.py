import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.bed_occupancy import compute_historical_occupancy_timeseries, calculate_department_bed_occupancy
from src.resource_planning import compare_all_preset_scenarios
from src.eda import load_clean_data, generate_eda_kpis

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_all_reports():
    print("Generating Power BI and operational reports...")

    # 1. Admissions Time-Series
    clean_ts_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "daily_admissions_timeseries.csv")
    if os.path.exists(clean_ts_path):
        df_ts = pd.read_csv(clean_ts_path)
        out_adm = os.path.join(REPORTS_DIR, "powerbi_admissions_trends.csv")
        df_ts.to_csv(out_adm, index=False)
        print(f"Exported: {out_adm}")

    # 2. Bed Occupancy History
    df_occ = compute_historical_occupancy_timeseries(days=90)
    out_occ = os.path.join(REPORTS_DIR, "powerbi_bed_occupancy_history.csv")
    df_occ.to_csv(out_occ, index=False)
    print(f"Exported: {out_occ}")

    # 3. Department Current Bed Status
    occ_summary = calculate_department_bed_occupancy()
    df_dept = pd.DataFrame(occ_summary["department_summaries"])
    out_dept = os.path.join(REPORTS_DIR, "powerbi_department_capacity.csv")
    df_dept.to_csv(out_dept, index=False)
    print(f"Exported: {out_dept}")

    # 4. Resource Scenario Comparison
    df_sim = compare_all_preset_scenarios()
    out_sim = os.path.join(REPORTS_DIR, "powerbi_scenario_simulation_comparison.csv")
    df_sim.to_csv(out_sim, index=False)
    print(f"Exported: {out_sim}")

    # 5. EDA Summary Report (Markdown/Text)
    clean_df = load_clean_data()
    kpis = generate_eda_kpis(clean_df)
    report_text = f"""# Hospital Operational Analytics & EDA Report
Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. Executive Operations Summary
- Total Historical Records Analyzed: {kpis['total_admissions']:,}
- Emergency Admissions: {kpis['emergency_count']:,} ({kpis['emergency_pct']}%)
- Elective Admissions: {kpis['elective_count']:,}
- Urgent Admissions: {kpis['urgent_count']:,}
- Average Emergency Waiting Time: {kpis['avg_waiting_time_mins']} minutes
- Average Inpatient Length of Stay (LOS): {kpis['avg_length_of_stay_days']} days

## 2. Demand Patterns
- Peak Clinical Department: {kpis['top_department']} ({kpis['top_department_volume']:,} admissions)
- Peak Patient Arrival Hour: {kpis['peak_arrival_hour']}:00 (Hospital Congestion Window)
- Busiest Weekday: {kpis['peak_day_of_week']} (Elective surge + Monday backlog)

## 3. Power BI Integration Note
The CSV data exports generated in the `reports/` directory are fully normalized and ready for ingestion into Power BI Desktop or Service.
"""
    out_text = os.path.join(REPORTS_DIR, "operational_eda_report.md")
    with open(out_text, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Exported: {out_text}")

    print("\n[SUCCESS] All operational reports and Power BI CSV datasets successfully compiled.")


if __name__ == "__main__":
    generate_all_reports()
