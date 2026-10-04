import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def load_clean_data(path: str = None) -> pd.DataFrame:
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "hospital_operations_clean.csv")
    df = pd.read_csv(path)
    df["admission_datetime"] = pd.to_datetime(df["admission_datetime"])
    df["discharge_datetime"] = pd.to_datetime(df["discharge_datetime"])
    df["admission_date"] = df["admission_datetime"].dt.date
    df["arrival_hour"] = df["admission_datetime"].dt.hour
    df["day_name"] = df["admission_datetime"].dt.day_name()
    df["month_name"] = df["admission_datetime"].dt.month_name()
    return df


def generate_eda_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    total_admissions = len(df)
    er_count = int((df["admission_type"] == "Emergency").sum())
    elective_count = int((df["admission_type"] == "Elective").sum())
    urgent_count = int((df["admission_type"] == "Urgent").sum())
    avg_wait = round(float(df["waiting_time_minutes"].mean()), 1)
    avg_los = round(float(df["length_of_stay_days"].mean()), 1)

    top_dept = df["department"].value_counts().index[0]
    top_dept_vol = int(df["department"].value_counts().iloc[0])

    peak_hour = int(df["arrival_hour"].value_counts().index[0])
    peak_day = df["day_name"].value_counts().index[0]

    return {
        "total_admissions": total_admissions,
        "emergency_count": er_count,
        "emergency_pct": round((er_count / total_admissions) * 100.0, 1),
        "elective_count": elective_count,
        "urgent_count": urgent_count,
        "avg_waiting_time_mins": avg_wait,
        "avg_length_of_stay_days": avg_los,
        "top_department": top_dept,
        "top_department_volume": top_dept_vol,
        "peak_arrival_hour": peak_hour,
        "peak_day_of_week": peak_day
    }


def create_daily_volume_chart(df: pd.DataFrame) -> go.Figure:
    daily = df.groupby("admission_date").size().reset_index(name="Admissions")
    daily["7D_MA"] = daily["Admissions"].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["admission_date"],
        y=daily["Admissions"],
        name="Daily Admissions",
        marker_color="rgba(14, 165, 233, 0.45)"
    ))
    fig.add_trace(go.Scatter(
        x=daily["admission_date"],
        y=daily["7D_MA"],
        mode="lines",
        name="7-Day Moving Avg",
        line=dict(color="#0e4f8a", width=3)
    ))
    fig.update_layout(
        title="Daily Hospital Admissions Trend with 7-Day Moving Average",
        xaxis_title="Date",
        yaxis_title="Total Admissions",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def create_department_volume_chart(df: pd.DataFrame) -> go.Figure:
    dept_counts = df.groupby(["department", "admission_type"]).size().reset_index(name="Count")
    fig = px.bar(
        dept_counts,
        x="department",
        y="Count",
        color="admission_type",
        title="Department Patient Volume by Admission Type",
        color_discrete_map={
            "Emergency": "#ef4444",
            "Elective": "#0ea5e9",
            "Urgent": "#f59e0b"
        },
        template="plotly_white"
    )
    fig.update_layout(
        xaxis_title="Clinical Department",
        yaxis_title="Patient Volume",
        xaxis_tickangle=-45,
        margin=dict(l=40, r=40, t=50, b=100)
    )
    return fig


def create_waiting_time_by_priority_chart(df: pd.DataFrame) -> go.Figure:
    er = df[df["admission_type"] == "Emergency"].copy()
    er = er[er["emergency_priority"] > 0]
    er["Priority_Label"] = er["emergency_priority"].map({
        1: "P1: Resuscitation",
        2: "P2: Emergent",
        3: "P3: Urgent",
        4: "P4: Less Urgent",
        5: "P5: Non-Urgent"
    })
    er = er.sort_values("emergency_priority")

    fig = px.box(
        er,
        x="Priority_Label",
        y="waiting_time_minutes",
        color="Priority_Label",
        title="Emergency Department Waiting Time Distribution by Triage Priority",
        labels={"waiting_time_minutes": "Waiting Time (Minutes)", "Priority_Label": "Triage Priority"},
        template="plotly_white"
    )
    fig.update_layout(showlegend=False, margin=dict(l=40, r=40, t=50, b=60))
    return fig


def create_arrival_heatmap(df: pd.DataFrame) -> go.Figure:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = df.pivot_table(
        index="day_name",
        columns="arrival_hour",
        values="admission_id",
        aggfunc="count",
        fill_value=0
    ).reindex(day_order)

    fig = px.imshow(
        pivot,
        labels=dict(x="Hour of Day (0-23)", y="Day of Week", color="Arrivals"),
        x=list(range(24)),
        y=day_order,
        color_continuous_scale="Blues",
        title="Patient Arrival Congestion Heatmap (Day of Week vs Arrival Hour)"
    )
    fig.update_layout(template="plotly_white", margin=dict(l=40, r=40, t=50, b=40))
    return fig


def create_los_distribution_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        df,
        x="length_of_stay_days",
        nbins=40,
        color="hospital_unit",
        title="Inpatient Length of Stay (LOS) Distribution by Hospital Unit",
        template="plotly_white",
        labels={"length_of_stay_days": "Length of Stay (Days)"}
    )
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40))
    return fig
