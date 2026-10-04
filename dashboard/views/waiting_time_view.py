import os
import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.eda import load_clean_data, create_waiting_time_by_priority_chart, create_arrival_heatmap
from src.waiting_time import predict_waiting_time
from src.explainability import create_feature_importance_bar_chart


def render_waiting_time_view():
    st.markdown("""
    <div class="hospital-header">
        <h1>Emergency Waiting-Time Analytics & Estimation</h1>
        <p>Triage-Prioritized Queue Modeling, Machine Learning Predictions, and Bottleneck Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    df = load_clean_data()

    tab_calc, tab_analytics, tab_models = st.tabs([
        "⏱️ Real-Time Waiting Time Estimator",
        "📊 Historical Queue Analytics & Distributions",
        "🧠 Model Performance & Feature Importance"
    ])

    with tab_calc:
        st.subheader("Simulate / Estimate Emergency Queue Waiting Time")
        st.write("Input current department conditions to estimate expected queue waiting time before medical consultation.")

        c1, c2, c3 = st.columns(3)
        with c1:
            priority = st.selectbox(
                "Triage Emergency Priority",
                [1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "P1: Resuscitation (Immediate)",
                    2: "P2: Emergent (Within 15 mins)",
                    3: "P3: Urgent (Within 45 mins)",
                    4: "P4: Less Urgent (Standard)",
                    5: "P5: Non-Urgent (Minor)"
                }[x],
                index=2
            )
            dept = st.selectbox("Presenting Clinical Department", [
                "Cardiology", "General Medicine", "Neurology", "Orthopedics",
                "Pediatrics", "Gastroenterology", "ENT"
            ])
        with c2:
            arr_hour = st.slider("Arrival Hour of Day (24h)", min_value=0, max_value=23, value=11)
            day_of_week = st.selectbox(
                "Day of Week",
                list(range(7)),
                format_func=lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x]
            )
        with c3:
            staff = st.slider("Clinical Staff on Duty (Emergency Unit)", min_value=4, max_value=25, value=12)
            age = st.number_input("Patient Age", min_value=1, max_value=110, value=42)

        est = predict_waiting_time(
            arrival_hour=arr_hour,
            day_of_week=day_of_week,
            emergency_priority=priority,
            department=dept,
            staff_on_duty=staff,
            patient_age=age
        )

        res_col1, res_col2 = st.columns([1, 1.5], gap="large")
        with res_col1:
            st.markdown(f"""
            <div class="kpi-card" style="margin-top:1rem; border-color:#0284c7;">
                <div class="kpi-label">Estimated Queue Wait</div>
                <div class="kpi-value" style="color:#0e4f8a;">{est['predicted_waiting_time_minutes']:.1f} <span style="font-size:1.1rem;">minutes</span></div>
                <div class="kpi-subtext" style="color:#0f766e;">Confidence Interval: {est['estimated_range']}</div>
            </div>
            """, unsafe_allow_html=True)

        with res_col2:
            st.markdown("""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:1.2rem; margin-top:1rem; font-size:0.88rem; color:#475569;">
                <b>Clinical Workflow Context:</b>
                <ul>
                    <li>P1 & P2 patients are admitted immediately without waiting in standard waiting areas.</li>
                    <li>Congestion peaks occur during 10:00 AM – 1:00 PM and 5:00 PM – 8:00 PM due to acute outpatient escalations.</li>
                    <li>Adding 3 additional nursing/triage staff members during peak windows decreases average wait by ~18%.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    with tab_analytics:
        st.subheader("Waiting Time Patterns by Priority and Hour")
        ch1, ch2 = st.columns([1, 1], gap="medium")
        with ch1:
            fig_p = create_waiting_time_by_priority_chart(df)
            st.plotly_chart(fig_p, use_container_width=True)
        with ch2:
            fig_heat = create_arrival_heatmap(df)
            st.plotly_chart(fig_heat, use_container_width=True)

    with tab_models:
        st.subheader("Model Evaluation & Explainable AI")
        cache_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "waiting_time_cache.json")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                wt_cache = json.load(f)

            ev = wt_cache.get("evaluation_metrics", {})
            st.write("<b>Algorithm Comparison Table (Test Set Evaluation)</b>", unsafe_allow_html=True)
            ev_df = pd.DataFrame([
                {"Model": k.replace("_", " "), "MAE (Minutes)": v["MAE"], "RMSE": v["RMSE"], "R² Score": v["R2"]}
                for k, v in ev.items()
            ])
            st.dataframe(ev_df, use_container_width=True)

            fi = wt_cache.get("feature_importance", {})
            fig_fi = create_feature_importance_bar_chart(fi, "Waiting Time Predictive Feature Importances")
            st.plotly_chart(fig_fi, use_container_width=True)

    st.markdown("""
    <div class="disclaimer-box">
        <b>Transparency & Clinical Disclosure:</b> Predictions generated by this module are non-guaranteed operational estimates intended solely for triage flow planning. Emergency medical treatment is always administered based on real-time clinical assessment, not software predictions.
    </div>
    """, unsafe_allow_html=True)
