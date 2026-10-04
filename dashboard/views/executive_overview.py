import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.api_client import api_client
from src.eda import load_clean_data, create_daily_volume_chart, create_department_volume_chart


def render_executive_overview():
    token = st.session_state.get("token", "")

    st.markdown("""
    <div class="hospital-header">
        <h1>Executive Hospital Operations Dashboard</h1>
        <p>Real-Time Capacity Monitoring, Inpatient Demand, and Operational Alerts</p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Connecting to operations intelligence engine..."):
        overview = api_client.get_operations_overview(token)

    if not overview:
        st.warning("Unable to fetch operational metrics from backend. Please ensure the backend is running.")
        return

    # Data Freshness & Source Banner
    st.markdown(f"""
    <div style="background:#f1f5f9; border:1px solid #cbd5e1; padding:0.6rem 1rem; border-radius:8px; font-size:0.82rem; color:#475569; margin-bottom:1.2rem; display:flex; justify-content:space-between;">
        <span>🕒 <b>System Freshness:</b> {overview.get('data_freshness')}</span>
        <span>🏷️ <b>Data Lineage Mode:</b> <span style="color:#0284c7; font-weight:600;">{overview.get('data_source_mode')}</span></span>
    </div>
    """, unsafe_allow_html=True)

    if overview.get("high_occupancy_alert"):
        st.error("🚨 **High Occupancy Warning:** Hospital bed occupancy has exceeded 85.0% threshold. Implement bed management protocols.")

    # KPI Metrics Row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Active Census (Occupied Beds)</div>
            <div class="kpi-value">{overview.get('occupied_beds')} <span style="font-size:1rem; color:#64748b;">/ {overview.get('total_bed_capacity')}</span></div>
            <div class="kpi-subtext">Occupancy Rate: <b>{overview.get('occupancy_rate_pct')}%</b></div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Available Inpatient Beds</div>
            <div class="kpi-value" style="color:#059669;">{overview.get('available_beds')}</div>
            <div class="kpi-subtext">Across 11 Clinical Wards</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Emergency Avg Waiting Time</div>
            <div class="kpi-value">{overview.get('average_waiting_time_minutes'):.1f} <span style="font-size:1rem;">mins</span></div>
            <div class="kpi-subtext">Triage Categories P1 - P5</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Projected Inflow (Next 24h)</div>
            <div class="kpi-value" style="color:#0284c7;">~{overview.get('today_admissions')}</div>
            <div class="kpi-subtext">XGBoost Forecast Model</div>
        </div>
        """, unsafe_allow_html=True)

    # Operational Visualizations
    st.subheader("📊 Inpatient Demand & Department Workload")
    df = load_clean_data()

    chart_col1, chart_col2 = st.columns([1.2, 1], gap="medium")
    with chart_col1:
        fig_vol = create_daily_volume_chart(df)
        st.plotly_chart(fig_vol, use_container_width=True)

    with chart_col2:
        fig_dept = create_department_volume_chart(df)
        st.plotly_chart(fig_dept, use_container_width=True)

    st.markdown("""
    <div class="disclaimer-box">
        <b>Operational Decision Support Notice:</b> Metrics and forecasts displayed on this executive overview are intended for hospital capacity planning, bed management, and staffing logistics. They are not intended for clinical diagnosis, treatment decisions, or patient triage.
    </div>
    """, unsafe_allow_html=True)
