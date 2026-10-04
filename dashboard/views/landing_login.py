import streamlit as st
from dashboard.api_client import api_client


def render_landing_login():
    st.markdown("""
    <div class="hospital-header">
        <h1>Hospital Resource & Patient Flow Optimization System</h1>
        <p>Enterprise Healthcare Resource Analytics, Dynamic Bed Allocation & Patient Flow Decision Support</p>
    </div>
    """, unsafe_allow_html=True)

    # Backend connectivity banner
    backend_online = api_client.check_health()
    if backend_online:
        st.markdown("""
        <div class="notice-banner">
            🟢 <b>Backend API Connected:</b> FastAPI REST service operational with Argon2/scrypt cryptographic authentication.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("⚠️ **Secure Backend API Unavailable.** Backend server is offline or unreachable at port 8000. Please start the backend (`uvicorn api.main:app --port 8000`). Authentication cannot proceed without the secure server.")
        return

    col1, col2 = st.columns([1.1, 0.9], gap="large")

    with col1:
        st.subheader("🏥 Clinical & Operations Platform")
        st.markdown("""
        Welcome to the next-generation **Hospital Resource & Patient Flow Optimization System**.
        This platform coordinates outpatient consultations with acute hospital operations,
        machine learning forecasting, bed capacity management, and staff resource planning.

        **Role-Based Capabilities:**
        - **Patients**: Browse all 55 verified physicians across 11 clinical specialties, book appointments with real-time slot conflict checking, and manage medical visits.
        - **Consulting Physicians**: Review your dedicated patient queue, access consultation notes, and update appointment statuses.
        - **Hospital Operations Managers**: Executive oversight of bed capacity, daily admission forecasts, emergency waiting-time analytics, what-if simulators, and Power BI reporting.
        """)

        with st.expander("🔑 Default Test Credentials for System Verification", expanded=True):
            st.markdown("""
            * **Operations Manager**: `admin.operations@healthcare.demo` / `Admin#Operations2026!`
            * **Cardiologist (Physician)**: `dr.johnsmith@healthcare.demo` / `Doctor#doc-0012026!`
            * **General Physician**: `dr.davidwilson@healthcare.demo` / `Doctor#doc-0062026!`
            * **Patient**: `ananya.raman@healthcare.demo` / `Patient#Secure2026!`
            """)

    with col2:
        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Patient Registration"])

        with tab_login:
            st.markdown("### Secure Sign In")
            with st.form("login_form"):
                email = st.text_input("Work or Patient Email", placeholder="e.g. admin.operations@healthcare.demo")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Authenticate & Access", use_container_width=True, type="primary")

                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        with st.spinner("Verifying credentials with secure backend..."):
                            res = api_client.login(email.strip(), password)
                            if res.get("success"):
                                token_data = res["data"]
                                st.session_state["token"] = token_data["access_token"]
                                st.session_state["user"] = token_data["user"]
                                st.session_state["role"] = token_data["user"]["role"]
                                st.success(f"Welcome back, {token_data['user']['name']} ({token_data['user']['role']})!")
                                st.rerun()
                            else:
                                st.error(f"Authentication Failed: {res.get('error')}")

        with tab_register:
            st.markdown("### New Patient Sign Up")
            with st.form("register_form"):
                name = st.text_input("Full Legal Name", placeholder="e.g. Priya Sharma")
                reg_email = st.text_input("Email Address", placeholder="priya.sharma@example.com")
                reg_pw = st.text_input("Create Password (min 8 chars)", type="password")
                reg_phone = st.text_input("Phone Number", placeholder="+91 98400 12345")
                c1, c2, c3 = st.columns(3)
                with c1:
                    age = st.number_input("Age", min_value=1, max_value=120, value=28)
                with c2:
                    gender = st.selectbox("Gender", ["Female", "Male", "Other"])
                with c3:
                    blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

                reg_submit = st.form_submit_button("Create Patient Account", use_container_width=True)
                if reg_submit:
                    if not name or not reg_email or not reg_pw:
                        st.error("Please complete all required fields.")
                    elif len(reg_pw) < 8:
                        st.error("Password must be at least 8 characters long.")
                    else:
                        payload = {
                            "name": name,
                            "email": reg_email,
                            "password": reg_pw,
                            "phone": reg_phone,
                            "age": int(age),
                            "gender": gender,
                            "blood_group": blood
                        }
                        with st.spinner("Provisioning patient account..."):
                            reg_res = api_client.register(payload)
                            if reg_res.get("success"):
                                token_data = reg_res["data"]
                                st.session_state["token"] = token_data["access_token"]
                                st.session_state["user"] = token_data["user"]
                                st.session_state["role"] = "Patient"
                                st.success(f"Account created successfully for {name}!")
                                st.rerun()
                            else:
                                st.error(f"Registration error: {reg_res.get('error')}")
