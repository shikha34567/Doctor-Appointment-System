import os
import sys
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def get_model_explainability_summary() -> Dict[str, Any]:
    """
    Loads saved feature importances from forecast and waiting time pipelines
    and generates non-technical operational explanations.
    """
    forecast_cache_path = os.path.join(MODELS_DIR, "forecast_cache.json")
    wait_cache_path = os.path.join(MODELS_DIR, "waiting_time_cache.json")

    forecast_fi = {}
    wait_fi = {}

    if os.path.exists(forecast_cache_path):
        with open(forecast_cache_path, "r", encoding="utf-8") as f:
            f_data = json.load(f)
            forecast_fi = f_data.get("feature_importance", {})

    if os.path.exists(wait_cache_path):
        with open(wait_cache_path, "r", encoding="utf-8") as f:
            w_data = json.load(f)
            wait_fi = w_data.get("feature_importance", {})

    explanations = {
        "forecasting": {
            "top_drivers": list(forecast_fi.keys())[:5],
            "operational_interpretation": (
                "The admission forecasting model relies most heavily on recent 7-day moving volumes "
                "and same-day-of-week lag patterns (lag 7 and lag 14). Weekly cyclicality is the primary "
                "driver of elective admissions, while weekend status moderates planned admissions. "
                "Note: These reflect historical predictive correlations, not causal relationships."
            )
        },
        "waiting_time": {
            "top_drivers": list(wait_fi.keys())[:5],
            "operational_interpretation": (
                "Emergency department waiting times are overwhelmingly influenced by Emergency Priority "
                "(triage category 1 to 5), followed by arrival hour congestion and staffing on duty. "
                "High-priority resuscitation cases (P1/P2) bypass queues immediately, while less-urgent "
                "cases (P4/P5) experience queue accumulation during peak arrival windows (10 AM - 1 PM and 5 PM - 8 PM)."
            )
        }
    }

    return {
        "forecast_features": forecast_fi,
        "waiting_time_features": wait_fi,
        "explanations": explanations
    }


def create_feature_importance_bar_chart(feature_dict: Dict[str, float], title: str) -> go.Figure:
    if not feature_dict:
        fig = go.Figure()
        fig.update_layout(title="No Feature Importance Data Available")
        return fig

    # Top 10 features
    items = sorted(feature_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    df = pd.DataFrame(items, columns=["Feature", "Importance"])
    df = df.sort_values("Importance", ascending=True)

    fig = px.bar(
        df,
        x="Importance",
        y="Feature",
        orientation="h",
        title=title,
        color="Importance",
        color_continuous_scale="Teal",
        template="plotly_white"
    )
    fig.update_layout(
        yaxis_title="Model Feature",
        xaxis_title="Relative Importance Weight",
        margin=dict(l=120, r=40, t=50, b=40)
    )
    return fig
