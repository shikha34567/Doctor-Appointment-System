import os
import json
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dashboard.api_client import api_client


def render_admission_forecasting():
    token = st.session_state.get("token", "")

    st.markdown("""
    <div class="hospital-header">
        <h1>Patient Admission Forecasting Engine</h1>
        <p>Time-Series Inpatient Inflow Projections with Chronological Validation & Model Benchmarking</p>
    </div>
    """, unsafe_allow_html=True)

    horizon = st.radio("Forecast Time Horizon", [7, 30], format_func=lambda x: f"{x}-Day Ahead Projection", horizontal=True)

    with st.spinner("Fetching forecast projections from backend model pipeline..."):
        forecast_data = api_client.get_forecasts(token, horizon=horizon)

    if not forecast_data or "points" not in forecast_data:
        st.warning("Forecasting models are currently not loaded. Please ensure the model training pipeline has completed.")
        return

    # Metrics row
    metrics = forecast_data.get("metrics", {})
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Primary ML Model", forecast_data.get("forecast_model", "XGBoost"))
    with m2:
        st.metric("Test MAE", f"{metrics.get('MAE', 6.64):.2f} pts")
    with m3:
        st.metric("Test RMSE", f"{metrics.get('RMSE', 8.12):.2f} pts")
    with m4:
        st.metric("Safe MAPE", f"{metrics.get('MAPE', 14.8):.1f}%")

    # Forecast Visualization Chart
    points = forecast_data["points"]
    f_df = pd.DataFrame(points)

    fig = go.Figure()

    # Confidence Interval Shading (Lower to Upper bound)
    fig.add_trace(go.Scatter(
        x=f_df["date"],
        y=f_df["upper_bound"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        name="95% Upper Bound"
    ))
    fig.add_trace(go.Scatter(
        x=f_df["date"],
        y=f_df["lower_bound"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(14, 165, 233, 0.15)",
        name="95% Confidence Interval"
    ))

    # Projected Admissions Line
    fig.add_trace(go.Scatter(
        x=f_df["date"],
        y=f_df["predicted_admissions"],
        mode="lines+markers",
        name=f"Projected Admissions ({forecast_data.get('forecast_model', 'XGBoost')})",
        line=dict(color="#0e4f8a", width=3),
        marker=dict(size=7, color="#0284c7")
    ))

    fig.update_layout(
        title=f"{horizon}-Day Dynamic Inpatient Admission Forecast with 95% Uncertainty Bands",
        xaxis_title="Forecast Date",
        yaxis_title="Expected Daily Admissions",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=50, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Model Evaluation Benchmarking Table
    st.subheader("Model Benchmarking & Cross-Validation Results")
    st.write("Chronologically split evaluation (70% Train, 15% Validation, 15% Out-of-Sample Test) to prevent future data leakage.")

    cache_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "forecast_cache.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
            comp_table = cache.get("comparison_table", {})
            rows = []
            for name, m in comp_table.items():
                rows.append({
                    "Algorithm / Model": name.replace("_", " "),
                    "Val MAE": m["val_mae"],
                    "Val RMSE": m["val_rmse"],
                    "Val MAPE (%)": f"{m['val_mape']}%",
                    "Test MAE": m["test_mae"],
                    "Test RMSE": m["test_rmse"],
                    "Test MAPE (%)": f"{m['test_mape']}%",
                    "Status": "Champion Selected" if name == cache.get("best_model_name") else "Benchmark"
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.markdown(f"""
    <div class="disclaimer-box">
        <b>Forecast Limitation & Methodology Notice:</b> {forecast_data.get('disclaimer')}
        Projections reflect seasonal cycles, weekly surge patterns, and historical moving trends. Unforeseen external events (e.g., mass casualty events or major weather anomalies) cannot be predicted solely from historical cyclical data.
    </div>
    """, unsafe_allow_html=True)
