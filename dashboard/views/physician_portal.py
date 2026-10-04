import streamlit as st
import datetime
from dashboard.api_client import api_client


def render_physician_portal():
    user = st.session_state.get("user", {})
    token = st.session_state.get("token", "")
    doctor_id = user.get("doctor_id", "doc-001")

    st.markdown(f"""
    <div class="hospital-header">
        <h1>Physician Clinical Practice & Schedule Portal</h1>
        <p>Physician: <b>{user.get('name', 'Doctor')}</b> | Doctor Registry ID: <b>{doctor_id}</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Doctor Profile Summary
    col_doc_info, col_doc_stat = st.columns([2, 1])
    with col_doc_info:
        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:1.2rem; margin-bottom:1.5rem;">
            <h3 style="margin:0 0 0.3rem 0; color:#0e4f8a;">{user.get('name')}</h3>
            <p style="margin:0; color:#64748b; font-size:0.9rem;">
                <b>Official Email:</b> {user.get('email')} | <b>Assigned Doctor ID:</b> {doctor_id}<br>
                <b>Data Isolation:</b> Protected under Role-Based Access Control. You can only view and modify appointments mapped to your doctor ID.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_doc_stat:
        st.markdown("""
        <div class="kpi-card" style="margin-bottom:0;">
            <div class="kpi-label">Consultation Status</div>
            <div class="kpi-value" style="font-size:1.4rem; color:#0f766e;">Active on Duty</div>
            <div class="kpi-subtext">Clinical Queue Synchronized</div>
        </div>
        """, unsafe_allow_html=True)

    # Filters
    st.subheader("Assigned Patient Queue & Appointments")
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        date_filter = st.date_input("Filter Consultation Date", value=None)
    with f_col2:
        status_filter = st.selectbox("Filter Status", ["All", "Scheduled", "Completed", "Cancelled"])
    with f_col3:
        st.write("")
        st.write("")
        clear_filters = st.button("Reset Filters", use_container_width=True)
        if clear_filters:
            date_filter = None
            status_filter = "All"
            st.rerun()

    formatted_date = date_filter.strftime("%Y-%m-%d") if date_filter else None

    with st.spinner("Fetching assigned consultation queue..."):
        appts = api_client.get_physician_appointments(
            token,
            date_filter=formatted_date,
            status_filter=status_filter if status_filter != "All" else None
        )

    if not appts:
        st.info("No appointments currently scheduled matching the selected filters.")
    else:
        st.caption(f"Displaying {len(appts)} consultation records assigned to your care.")

        for appt in appts:
            badge_class = f"badge-{appt['status'].lower()}"
            with st.container():
                col_p, col_act = st.columns([2.3, 1], gap="medium")
                with col_p:
                    st.markdown(f"""
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:1.2rem; margin-bottom:1rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0; color:#0e4f8a;">Patient: {appt['patient_name']}</h4>
                            <span class="{badge_class}">{appt['status']}</span>
                        </div>
                        <div style="margin-top:0.6rem; font-size:0.88rem; color:#334155; line-height:1.5;">
                            <b>Appointment ID:</b> {appt['id']} | <b>Date:</b> {appt['appointment_date']} at <b>{appt['time_slot']}</b><br>
                            <b>Patient Contact:</b> {appt.get('patient_phone') or 'Not recorded'} | <b>Email:</b> {appt.get('patient_email') or 'N/A'}<br>
                            <b>Age/Gender:</b> {appt.get('patient_age') or 'N/A'} yrs / {appt.get('patient_gender') or 'N/A'}<br>
                            <b>Clinical Notes / Chief Complaint:</b> {appt.get('notes') or 'No notes recorded.'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_act:
                    st.markdown("<div style='padding-top:0.8rem;'></div>", unsafe_allow_html=True)
                    new_st = st.selectbox(
                        "Update Status",
                        ["Scheduled", "Completed", "Cancelled"],
                        index=["Scheduled", "Completed", "Cancelled"].index(appt["status"]),
                        key=f"status_sel_{appt['id']}"
                    )
                    clinical_update = st.text_input("Consultation note", placeholder="Diagnosis / Rx", key=f"note_input_{appt['id']}")
                    if st.button("Save Status", key=f"update_{appt['id']}", type="primary", use_container_width=True):
                        update_res = api_client.update_appointment_status(token, appt["id"], new_st, clinical_update)
                        if update_res.get("success"):
                            st.success(f"Updated {appt['id']} to {new_st}")
                            st.rerun()
                        else:
                            st.error(update_res.get("error"))
