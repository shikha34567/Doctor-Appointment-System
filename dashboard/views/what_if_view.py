import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.api_client import api_client
from src.resource_planning import simulate_what_if_scenario, compare_all_preset_scenarios


def render_what_if_view():
    token = st.session_state.get("token", "")

    st.markdown("""
    <div class="hospital-header">
        <h1>Interactive What-If Scenario Simulator</h1>
        <p>Stress-Testing Hospital Capacity, Inpatient Surge Scenarios, and Bottleneck Projections</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Select Scenario Preset or Custom Operational Parameters")
    preset = st.radio(
        "Simulation Preset",
        ["Normal", "Low", "High", "Custom"],
        format_func=lambda x: {
            "Normal": "Normal Operating Baseline (45 daily admissions)",
            "Low": "Low Demand Season (-20% surge, -0.5d LOS)",
            "High": "High Demand Surge / Winter Epidemic (+35% surge, +1.2d LOS)",
            "Custom": "Custom Parameter Tuning"
        }[x],
        horizontal=True
    )

    if preset == "Custom":
        c1, c2, c3 = st.columns(3)
        with c1:
            demand_pct = st.slider("Demand Volume Multiplier (%)", min_value=-50.0, max_value=100.0, value=20.0, step=5.0)
        with c2:
            los_adj = st.slider("Average Length of Stay Adjustment (Days)", min_value=-2.0, max_value=4.0, value=0.5, step=0.25)
        with c3:
            bed_cap = st.number_input("Available Bed Capacity Override", min_value=100, max_value=600, value=365)
    else:
        demand_pct = 0.0
        los_adj = 0.0
        bed_cap = 365

    with st.spinner("Executing Little's Law steady-state simulation..."):
        sim_res = simulate_what_if_scenario(
            scenario_preset=preset,
            demand_multiplier_pct=demand_pct,
            los_adjustment_days=los_adj,
            bed_capacity_override=bed_cap if preset == "Custom" else None
        )

    # Simulation KPI results
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Projected Daily Admissions", f"{sim_res['projected_daily_admissions']:.1f}")
    with k2:
        st.metric("Projected Census (Beds)", f"{sim_res['projected_occupied_beds']:.0f} / {sim_res['total_bed_capacity']}")
    with k3:
        st.metric("Projected Occupancy Rate", f"{sim_res['projected_occupancy_rate_pct']}%", delta=sim_res["risk_level"])
    with k4:
        st.metric("Bed Shortage Deficit", sim_res["bed_shortage"], delta="Shortage" if sim_res["bed_shortage"] > 0 else "Sufficient")

    # Recommendations banner
    st.subheader(f"Operational Assessment: {sim_res['risk_level']}")
    for rec in sim_res["recommendations"]:
        if "Immediate" in rec or "Severe" in sim_res["risk_level"]:
            st.error(f"⚠️ {rec}")
        elif "Caution" in sim_res["risk_level"] or "Prioritize" in rec:
            st.warning(f"🟡 {rec}")
        else:
            st.success(f"🟢 {rec}")

    # Side-by-side comparison across all standard presets
    st.subheader("Comparative Benchmark: Low vs Normal vs High Demand")
    comp_df = compare_all_preset_scenarios()
    st.dataframe(comp_df, use_container_width=True)

    # Plotly comparison
    fig = px.bar(
        comp_df,
        x="Scenario",
        y="Projected Census",
        color="Scenario",
        title="Projected Inpatient Census Across Standard Operating Scenarios",
        color_discrete_map={"Low": "#14b8a6", "Normal": "#0284c7", "High": "#ef4444"},
        template="plotly_white"
    )
    fig.add_hline(y=365, line_dash="dash", line_color="#0f172a", annotation_text="Standard Capacity (365 Beds)")
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40))
    st.plotly_chart(fig, use_container_width=True)
