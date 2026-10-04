import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.api_client import api_client
from src.bed_occupancy import calculate_department_bed_occupancy, compute_historical_occupancy_timeseries


def render_bed_occupancy_view():
    token = st.session_state.get("token", "")

    st.markdown("""
    <div class="hospital-header">
        <h1>Inpatient Bed Capacity & Occupancy Analytics</h1>
        <p>Ward-Level Census Tracking, Concurrent Occupancy Trends, and Surge Capacity Management</p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Computing real-time bed census..."):
        occ = api_client.get_bed_occupancy(token)
        if not occ:
            occ = calculate_department_bed_occupancy()

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.metric("Total Configured Beds", occ["total_hospital_beds"])
    with b2:
        st.metric("Current Occupied Beds", occ["total_occupied_beds"])
    with b3:
        st.metric("Available Beds", occ["total_available_beds"], delta=f"{occ['total_available_beds']} open")
    with b4:
        st.metric("Overall Occupancy Rate", f"{occ['hospital_occupancy_rate_pct']}%", delta="Normal" if occ['hospital_occupancy_rate_pct'] < 85 else "Caution")

    st.subheader("Clinical Department Bed Utilization")
    dept_df = pd.DataFrame(occ["department_summaries"])

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=dept_df["department"],
        y=dept_df["occupied_beds"],
        name="Occupied Beds",
        marker_color="#0e4f8a"
    ))
    fig_bar.add_trace(go.Bar(
        x=dept_df["department"],
        y=dept_df["available_beds"],
        name="Available Beds",
        marker_color="#38bdf8"
    ))
    fig_bar.update_layout(
        barmode="stack",
        title="Department Bed Allocation: Occupied vs Available Capacity",
        xaxis_title="Department",
        yaxis_title="Beds",
        template="plotly_white",
        xaxis_tickangle=-40,
        margin=dict(l=40, r=40, t=50, b=90)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Department table breakdown
    st.dataframe(
        dept_df[["department", "total_beds", "occupied_beds", "available_beds", "occupancy_pct", "icu_total", "icu_occupied", "icu_occupancy_pct", "status"]],
        use_container_width=True
    )

    # Historical trend
    st.subheader("Historical Occupancy Trend (Trailing 60 Days)")
    trend_df = compute_historical_occupancy_timeseries(days=60)

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_df["date"],
        y=trend_df["occupancy_rate_pct"],
        mode="lines",
        name="Occupancy Rate (%)",
        line=dict(color="#0284c7", width=2.5)
    ))
    fig_trend.add_hline(y=85.0, line_dash="dash", line_color="#ef4444", annotation_text="85% Safety Alert Threshold")
    fig_trend.update_layout(
        title="Hospital-Wide Midday Bed Occupancy Rate (%)",
        xaxis_title="Date",
        yaxis_title="Occupancy Percentage (%)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    st.plotly_chart(fig_trend, use_container_width=True)
