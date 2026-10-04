import streamlit as st
import pandas as pd
from dashboard.api_client import api_client
from src.resource_planning import calculate_staffing_requirements


def render_staffing_view():
    token = st.session_state.get("token", "")

    st.markdown("""
    <div class="hospital-header">
        <h1>Staffing & Resource Capacity Planning</h1>
        <p>Operational Roster Modeling, Inpatient Ratios, and Shift Gap Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("⚙️ Configurable Planning Assumptions")
    st.write("Adjust operational planning ratios to evaluate nursing and physician shift allocations against active census.")

    c1, c2, c3 = st.columns(3)
    with c1:
        nurse_icu = st.slider("ICU Nurse-to-Patient Ratio (1:N)", min_value=1.0, max_value=4.0, value=2.0, step=0.5)
    with c2:
        nurse_gen = st.slider("General Ward Nurse Ratio (1:N)", min_value=2.0, max_value=8.0, value=4.0, step=0.5)
    with c3:
        phys_ratio = st.slider("Physician-to-Patient Ratio (1:N)", min_value=5.0, max_value=20.0, value=10.0, step=1.0)

    staff_plan = calculate_staffing_requirements(
        daily_volume=45.0,
        active_inpatient_census=210.0,
        nurse_icu_ratio=nurse_icu,
        nurse_gen_ratio=nurse_gen,
        physician_ratio=phys_ratio
    )

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total Daily Nurses Needed", staff_plan["total_nurses_required_daily"])
    with s2:
        st.metric("Total Physicians Needed", staff_plan["total_physicians_required_daily"])
    with s3:
        st.metric("Nursing Shift Shortage", staff_plan["total_nurses_shortage"], delta="Shortage" if staff_plan["total_nurses_shortage"] > 0 else "Balanced")
    with s4:
        st.metric("Physician Shift Shortage", staff_plan["total_physicians_shortage"], delta="Shortage" if staff_plan["total_physicians_shortage"] > 0 else "Balanced")

    st.subheader("Shift-by-Shift Operational Breakdown")
    shift_df = pd.DataFrame(staff_plan["shifts"])
    st.dataframe(shift_df, use_container_width=True)

    st.markdown("""
    <div class="disclaimer-box">
        <b>Planning Assumptions Governance:</b> Ratios and staffing recommendations are operational approximations designed to identify potential shift vulnerabilities. They must not replace clinical judgment, collective bargaining agreements, or certified acuity-based staffing models.
    </div>
    """, unsafe_allow_html=True)
