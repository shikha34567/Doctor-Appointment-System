import os
import streamlit as st
import pandas as pd
from src.eda import load_clean_data, generate_eda_kpis, create_los_distribution_chart
from src.data_validation import run_pipeline_validation


def render_reports_view():
    st.markdown("""
    <div class="hospital-header">
        <h1>Data Insights, Audit Reports & Power BI Exports</h1>
        <p>Data Quality Metrics, Exploratory Analysis, and Automated Reporting Pipeline</p>
    </div>
    """, unsafe_allow_html=True)

    tab_eda, tab_quality, tab_exports, tab_powerbi = st.tabs([
        "📈 Inpatient Data Insights (EDA)",
        "🛡️ Data Quality Scorecard",
        "📥 CSV Report Downloads",
        "📊 Power BI Integration Guide"
    ])

    df = load_clean_data()
    kpis = generate_eda_kpis(df)

    with tab_eda:
        st.subheader("Exploratory Data Findings")
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Total Admissions", f"{kpis['total_admissions']:,}")
        with k2:
            st.metric("Emergency Ratio", f"{kpis['emergency_pct']}%")
        with k3:
            st.metric("Avg Length of Stay", f"{kpis['avg_length_of_stay_days']} days")
        with k4:
            st.metric("Busiest Ward", kpis["top_department"])

        st.plotly_chart(create_los_distribution_chart(df), use_container_width=True)

    with tab_quality:
        st.subheader("Data Validation & Quality Assurance")
        clean_df, report = run_pipeline_validation()

        q1, q2, q3 = st.columns(3)
        with q1:
            st.metric("Data Quality Score", f"{report['data_quality_score_pct']}%", delta="High Integrity")
        with q2:
            st.metric("Duplicates Eliminated", report["duplicate_rows_detected"])
        with q3:
            st.metric("Timestamp Sanity Violations", report["invalid_timestamp_order_count"])

        st.json(report)

    with tab_exports:
        st.subheader("Download Normalized Datasets for BI & External Analysis")
        st.write("These files are structured for ingestion into Microsoft Power BI, Tableau, or Excel.")

        rep_dir = os.path.join(os.path.dirname(__file__), "..", "..", "reports")

        col1, col2, col3 = st.columns(3)
        with col1:
            f1 = os.path.join(rep_dir, "powerbi_admissions_trends.csv")
            if os.path.exists(f1):
                with open(f1, "rb") as f:
                    st.download_button(
                        label="📄 Download Admissions Time-Series CSV",
                        data=f,
                        file_name="hospital_admissions_trends.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        with col2:
            f2 = os.path.join(rep_dir, "powerbi_bed_occupancy_history.csv")
            if os.path.exists(f2):
                with open(f2, "rb") as f:
                    st.download_button(
                        label="📄 Download Bed Occupancy CSV",
                        data=f,
                        file_name="bed_occupancy_history.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        with col3:
            f3 = os.path.join(rep_dir, "powerbi_scenario_simulation_comparison.csv")
            if os.path.exists(f3):
                with open(f3, "rb") as f:
                    st.download_button(
                        label="📄 Download Scenario Benchmarks CSV",
                        data=f,
                        file_name="scenario_simulation_comparison.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

    with tab_powerbi:
        st.subheader("Power BI Desktop Connection & Dashboard Setup Guide")
        st.markdown("""
        ### Step-by-Step Instructions to Connect Power BI:

        1. **Option A: Connect to Clean CSV Data Extracts (Fastest)**
           * Open Microsoft Power BI Desktop.
           * Click on **Get Data** -> **Text/CSV**.
           * Select the files exported from the `reports/` folder (`powerbi_admissions_trends.csv`, `powerbi_bed_occupancy_history.csv`, etc.).
           * Click **Load** to import data into the Power BI semantic model.

        2. **Option B: Direct PostgreSQL / SQLite Database Connection**
           * In Power BI, select **Get Data** -> **PostgreSQL database** (or ODBC for SQLite).
           * Enter server host: `localhost` and Database: `hospital_system`.
           * Select tables `admissions`, `beds`, `departments`, `appointments`.
           * Create relationships between `admissions.department_id` and `departments.id`.

        3. **Recommended Visualizations in Power BI:**
           * **Card KPI**: Average Waiting Time & Total Inpatient Census.
           * **Line Chart**: 7-Day Rolling Admissions vs XGBoost Forecast Horizon.
           * **Clustered Column Chart**: Bed Occupancy Rate by Department with a constant line at 85%.
           * **Slicers**: Department, Admission Type (Emergency vs Elective), and Date Hierarchy.
        """)
