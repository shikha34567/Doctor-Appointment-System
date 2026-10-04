import streamlit as st
import datetime
from dashboard.api_client import api_client


def render_patient_portal():
    user = st.session_state.get("user", {})
    token = st.session_state.get("token", "")

    st.markdown(f"""
    <div class="hospital-header">
        <h1>Patient Care & Appointment Portal</h1>
        <p>Welcome back, <b>{user.get('name', 'Patient')}</b> | Patient ID: {user.get('id', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

    tab_directory, tab_my_appts, tab_profile = st.tabs([
        "🔍 Find & Book Doctors (55 Registry)",
        "📋 My Appointments & Slips",
        "👤 My Patient Profile"
    ])

    with tab_directory:
        st.subheader("Consultant Physician Directory")
        st.write("Browse certified medical specialists across all 11 hospital departments.")

        col_search, col_dept = st.columns([1.5, 1])
        with col_search:
            search_query = st.text_input("Search Doctor by Name or Keyword", placeholder="e.g. Dr. John Smith, Cardiology...")
        with col_dept:
            specialties = [
                "All", "Cardiology", "General Medicine", "Neurology", "Orthopedics",
                "Pediatrics", "Dermatology", "ENT", "Ophthalmology",
                "Gastroenterology", "Gynecology & Obstetrics", "Psychiatry"
            ]
            selected_specialty = st.selectbox("Filter Specialty / Department", specialties)

        with st.spinner("Loading specialist directory..."):
            doctors = api_client.get_doctors(
                specialty=selected_specialty if selected_specialty != "All" else None,
                search=search_query if search_query else None
            )

        st.caption(f"Showing {len(doctors)} certified specialists matching your criteria.")

        for doc in doctors:
            with st.container():
                col_info, col_book = st.columns([2.2, 1], gap="medium")
                with col_info:
                    st.markdown(f"""
                    <div class="doctor-card">
                        <div class="doctor-name">{doc['name']}</div>
                        <span class="doctor-spec">{doc['specialty']}</span>
                        <div class="doctor-meta">
                            <b>Qualifications:</b> {doc.get('qualification', 'MBBS, MD')}<br>
                            <b>Clinical Experience:</b> {doc.get('experience', '10+ Years')} | <b>Languages:</b> {doc.get('languages', 'English')}<br>
                            <b>Consultation Room:</b> {doc.get('room', 'General Consultation Wing')}<br>
                            <b>Availability:</b> {doc.get('availability', 'Mon-Fri')}<br>
                            <p style="margin-top:0.4rem; color:#64748b; font-size:0.84rem;">{doc.get('bio', '')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_book:
                    st.markdown(f"<div style='padding-top:1rem;'><b>Fee:</b> ₹{doc['fee']:.0f}</div>", unsafe_allow_html=True)
                    with st.expander(f"Book with {doc['name']}", expanded=False):
                        booking_date = st.date_input(
                            "Select Consultation Date",
                            min_value=datetime.date.today(),
                            max_value=datetime.date.today() + datetime.timedelta(days=30),
                            key=f"date_{doc['doctor_id']}"
                        )
                        slots = [
                            "09:00 AM", "09:45 AM", "10:30 AM", "11:15 AM",
                            "02:00 PM", "02:45 PM", "03:30 PM", "04:15 PM"
                        ]
                        selected_slot = st.selectbox("Available Time Slot", slots, key=f"slot_{doc['doctor_id']}")
                        reason = st.text_area("Chief Medical Complaint / Notes", placeholder="e.g. Routine checkup or symptom summary", key=f"notes_{doc['doctor_id']}")

                        if st.button("Confirm Booking", key=f"btn_{doc['doctor_id']}", type="primary", use_container_width=True):
                            payload = {
                                "doctor_id": doc["doctor_id"],
                                "appointment_date": booking_date.strftime("%Y-%m-%d"),
                                "time_slot": selected_slot,
                                "patient_name": user.get("name", "Patient"),
                                "patient_phone": user.get("phone", "+91 98400 00000"),
                                "patient_email": user.get("email", ""),
                                "notes": reason
                            }
                            with st.spinner("Reserving appointment slot..."):
                                book_res = api_client.book_appointment(token, payload)
                                if book_res.get("success"):
                                    appt = book_res["data"]
                                    st.success(f"Appointment confirmed! Booking ID: {appt['id']}")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"Booking Error: {book_res.get('error')}")

    with tab_my_appts:
        st.subheader("Your Scheduled & Historical Appointments")
        with st.spinner("Fetching your consultation records..."):
            my_appts = api_client.get_patient_appointments(token)

        if not my_appts:
            st.info("You do not have any scheduled appointments yet. Use the 'Find & Book Doctors' tab to schedule a visit.")
        else:
            for appt in my_appts:
                badge_class = f"badge-{appt['status'].lower()}"
                col_a, col_b = st.columns([2.5, 1])
                with col_a:
                    st.markdown(f"""
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:1.2rem; margin-bottom:1rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0; color:#0e4f8a;">{appt['doctor_name']} ({appt['specialty']})</h4>
                            <span class="{badge_class}">{appt['status']}</span>
                        </div>
                        <div style="margin-top:0.6rem; font-size:0.88rem; color:#475569;">
                            <b>Appointment ID:</b> {appt['id']} | <b>Date:</b> {appt['appointment_date']} at <b>{appt['time_slot']}</b><br>
                            <b>Room:</b> {appt.get('room', 'OPD Wing')} | <b>Consultation Fee:</b> ₹{appt['fee']:.0f}<br>
                            <b>Clinical Notes:</b> {appt.get('notes') or 'No specific notes recorded.'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_b:
                    st.write("")
                    if appt["status"] == "Scheduled":
                        if st.button("Cancel Appointment", key=f"cancel_{appt['id']}", type="secondary", use_container_width=True):
                            cancel_res = api_client.cancel_appointment(token, appt["id"])
                            if cancel_res.get("success"):
                                st.warning("Appointment cancelled.")
                                st.rerun()
                            else:
                                st.error(cancel_res.get("error"))

    with tab_profile:
        st.subheader("Patient Health Profile")
        st.write("Review your registered patient demographic information.")
        p1, p2 = st.columns(2)
        with p1:
            st.text_input("Name", value=user.get("name", ""), disabled=True)
            st.text_input("Registered Email", value=user.get("email", ""), disabled=True)
        with p2:
            st.text_input("Contact Number", value=user.get("phone", "+91 98401 99999"), disabled=True)
            st.text_input("Role", value=user.get("role", "Patient"), disabled=True)
