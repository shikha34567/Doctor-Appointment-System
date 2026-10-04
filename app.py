import os
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dashboard.styles import get_custom_css
from dashboard.views.landing_login import render_landing_login
from dashboard.views.patient_portal import render_patient_portal
from dashboard.views.physician_portal import render_physician_portal
from dashboard.views.executive_overview import render_executive_overview
from dashboard.views.admission_forecasting import render_admission_forecasting
from dashboard.views.waiting_time_view import render_waiting_time_view
from dashboard.views.bed_occupancy_view import render_bed_occupancy_view
from dashboard.views.staffing_view import render_staffing_view
from dashboard.views.what_if_view import render_what_if_view
from dashboard.views.reports_view import render_reports_view

# Page Config
st.set_page_config(
    page_title="Hospital Resource & Patient Flow Optimization System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom HealthCare Blue/Teal Theme CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Session State Initialization
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None


def logout_user():
    st.session_state["token"] = None
    st.session_state["user"] = None
    st.session_state["role"] = None
    st.rerun()


# Routing Logic
if not st.session_state["token"] or not st.session_state["user"]:
    render_landing_login()
else:
    user = st.session_state["user"]
    role = user.get("role", "Patient")

    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### 🏥 HealthCare Platform")
        st.markdown(f"**Logged in as:**<br><b>{user.get('name')}</b>", unsafe_allow_html=True)
        st.caption(f"Role: **{role}** | {user.get('email')}")
        if user.get("doctor_id"):
            st.caption(f"Doctor Registry ID: `{user.get('doctor_id')}`")

        st.markdown("---")

        # Role-based menu options
        if role == "Patient":
            menu_options = ["Patient Portal & Appointments"]
        elif role == "Physician":
            menu_options = ["Physician Clinical Schedule"]
        elif role == "OperationsManager":
            menu_options = [
                "Executive Overview",
                "Admission Forecasting",
                "Emergency Waiting Times",
                "Bed Occupancy & Capacity",
                "Staff & Resource Planning",
                "Interactive What-If Simulator",
                "Data Insights & Reports"
            ]
        else:
            menu_options = ["Patient Portal & Appointments"]

        selected_page = st.radio("Navigation Menu", menu_options)

        st.markdown("---")
        if st.button("🚪 Log Out", use_container_width=True, type="secondary"):
            logout_user()

        st.caption("Hospital Resource Optimization v2.0.0")

    # Render selected view
    if selected_page == "Patient Portal & Appointments":
        render_patient_portal()
    elif selected_page == "Physician Clinical Schedule":
        render_physician_portal()
    elif selected_page == "Executive Overview":
        render_executive_overview()
    elif selected_page == "Admission Forecasting":
        render_admission_forecasting()
    elif selected_page == "Emergency Waiting Times":
        render_waiting_time_view()
    elif selected_page == "Bed Occupancy & Capacity":
        render_bed_occupancy_view()
    elif selected_page == "Staff & Resource Planning":
        render_staffing_view()
    elif selected_page == "Interactive What-If Simulator":
        render_what_if_view()
    elif selected_page == "Data Insights & Reports":
        render_reports_view()
