"""Interactive SaaS-style retail dashboard (Streamlit + Plotly).

Run: streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

IST = ZoneInfo("Asia/Kolkata")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SUMMARY_PATH = DATA_DIR / "latest_summary.json"
HISTORY_PATH = DATA_DIR / "history.json"
AI_INSIGHT_PATH = DATA_DIR / "ai_insight.txt"


def load_latest_summary(path: Path = SUMMARY_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_history(path: Path = HISTORY_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and "records" in raw:
        rec = raw["records"]
        return rec if isinstance(rec, list) else []
    return []


def load_ai_insight_text(summary: dict[str, Any]) -> str:
    raw = summary.get("ai_insight")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    if AI_INSIGHT_PATH.exists():
        return AI_INSIGHT_PATH.read_text(encoding="utf-8").strip()
    return ""


def parse_sent_timestamp(summary: dict[str, Any]) -> datetime | None:
    raw = summary.get("sent_at")
    if not raw or not isinstance(raw, str):
        return None
    try:
        normalized = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def last_send_status_caption(summary: dict[str, Any]) -> str:
    sent = parse_sent_timestamp(summary)
    if sent is None:
        return "● No send timestamp in summary"

    sent_ist = sent.astimezone(IST)
    today_ist = datetime.now(IST).date()
    if sent_ist.date() == today_ist:
        return "● Reports sent today ✓"
    return f"● Last send · {sent_ist.strftime('%d %b %Y, %H:%M IST')}"


def summary_to_metrics(summary: dict[str, Any], shop_filter: str) -> tuple[float, float]:
    totals = summary.get("totals") or {}
    
    if not shop_filter or shop_filter == "All Outlets":
        net = float(totals.get("net_sales", totals.get("total_net_sales", 0)))
        exp = float(totals.get("expenses", totals.get("total_expenses", 0)))
        return net, exp

    for row in summary.get("shops", []):
        if isinstance(row, dict) and row.get("name") == shop_filter:
            return float(row.get("net_sales", 0)), float(row.get("expenses", 0))
            
    return 0.0, 0.0


def history_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=["date", "net_sales", "expenses"])
    df = pd.DataFrame(records)
    if "date" not in df.columns:
        return pd.DataFrame(columns=["date", "net_sales", "expenses"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    
    df["net_sales"] = pd.to_numeric(df.get("net_sales", 0), errors="coerce").fillna(0.0)
    df["expenses"] = pd.to_numeric(df.get("expenses", 0), errors="coerce").fillna(0.0)
    
    return df.sort_values("date").reset_index(drop=True)


def style_plotly_fig(fig):
    """Applies premium dark theme styling to any Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#94A3B8", size=12),
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode="x unified",
        legend=dict(
            title=None,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(color="#64748B"),
            title=None,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            zeroline=False,
            showline=False,
            tickfont=dict(color="#64748B"),
            title=None,
        ),
    )
    return fig


def main() -> None:
    st.set_page_config(
        page_title="Retail Analytics",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.markdown(
        """
        <style>
        .centered-title {
            text-align: center;
            font-weight: 800;
            padding-top: 1rem;
            padding-bottom: 2rem;
            font-size: 3rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 2. Use the custom class for the title
    st.markdown('<h1 class="centered-title">📈 Sitaram Retail Analytics</h1>', unsafe_allow_html=True)
    
    st.write("")

    summary = load_latest_summary()
    insight_text = load_ai_insight_text(summary)
    history_records = load_history()
    hist_df = history_to_dataframe(history_records)

    shops_raw = summary.get("shops") or []
    shop_names = [s.get("name", "") for s in shops_raw if isinstance(s, dict) and s.get("name")]
    
    # Extract live detail dataframe
    detail = pd.DataFrame(columns=["Shop", "Net Sales", "Expenses"])
    if shop_names:
        detail = pd.DataFrame([
            {"Shop": s.get("name"), "Net Sales": float(s.get("net_sales", 0)), "Expenses": float(s.get("expenses", 0))}
            for s in shops_raw if isinstance(s, dict)
        ])

    # --- LAYOUT ---
    col_left, col_right = st.columns([1, 3], gap="large")

    # LEFT PANEL
    with col_left:
        with st.container(border=True):
            st.markdown("**Select View**")
            options = ["All Outlets"] + shop_names
            # index=0 ensures "All Outlets" is selected by default
            selected_view = st.radio("Filter by shop", options=options, label_visibility="collapsed", index=0)

    # RIGHT PANEL
    with col_right:
        st.caption(last_send_status_caption(summary))
        net, exp = summary_to_metrics(summary, selected_view)

        # 1. Metrics Card
        with st.container(border=True):
            m1, m2 = st.columns(2)
            with m1:
                st.metric(f"{selected_view} Net Sales", f"₹{net:,.0f}")
            with m2:
                st.metric("Expenses", f"₹{exp:,.0f}", delta_color="inverse")

        # 2. Chart Card
        with st.container(border=True):
            st.markdown(f"**Analytics: {selected_view}**")
            
            if selected_view == "All Outlets" and not detail.empty:
                # Grouped Bar Chart: X=Shop, Y=Sales & Expenses
                fig = px.bar(
                    detail,
                    x="Shop",
                    y=["Net Sales", "Expenses"],
                    barmode="group",
                    color_discrete_sequence=["#6366F1", "#F59E0B"] # Purple and Amber
                )
                fig = style_plotly_fig(fig)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                # Bar Chart over time: X=Date, Y=Sales
                if not hist_df.empty:
                    # Showing last 14 days of data for the chart
                    recent_hist = hist_df.tail(14).copy()
                    recent_hist["date_str"] = recent_hist["date"].dt.strftime("%d %b")
                    
                    fig = px.bar(
                        recent_hist,
                        x="date_str",
                        y="net_sales",
                        color_discrete_sequence=["#6366F1"]
                    )
                    fig.update_traces(marker_border_radius=4) # Slightly rounded bars
                    fig = style_plotly_fig(fig)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Historical data not available yet to display daily breakdown.")

        # 3. AI Insight Card
        if insight_text:
            with st.container(border=True):
                st.markdown("**🤖 AI Analyst**")
                st.write(insight_text)

if __name__ == "__main__":
    main()