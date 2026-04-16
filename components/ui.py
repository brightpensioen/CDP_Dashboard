"""
Shared UI components for the CDP dashboard.
"""

import streamlit as st
import pandas as pd


CHANNEL_COLORS = {
    "Paid Search":     "#378ADD",
    "Organic Search":  "#1d9e75",
    "Direct":          "#e8a838",
    "Email":           "#9b59b6",
    "Referral":        "#e67e22",
    "Affiliates":      "#D85A30",
    "Organic AI":      "#5DCAA5",
    "Organic Social":  "#F0997B",
    "Organic Video":   "#AFA9EC",
    "Paid Display":    "#85B7EB",
    "Paid Social":     "#F4C0D1",
    "Other Advertising": "#B4B2A9",
    "(Other)":         "#888780",
}

STATUS_COLORS = {
    "customer": "#1d9e75",
    "lead":     "#378ADD",
    "churned":  "#D85A30",
}


def inject_global_css():
    """Inject global CSS overrides for a polished dark aesthetic."""
    st.markdown(
        """
        <style>
        /* ---- hide default Streamlit page nav ---- */
        [data-testid="stSidebarNav"] { display: none !important; }

        /* ---- sidebar ---- */
        [data-testid="stSidebar"] {
            background: #12121f;
            border-right: 0.5px solid rgba(255,255,255,0.08);
        }
        [data-testid="stSidebar"] label {
            font-size: 14px !important;
        }

        /* ---- main background ---- */
        .stApp {
            background: #1a1a2e;
        }
        .main .block-container {
            padding-top: 28px;
            padding-bottom: 40px;
            max-width: 1400px;
        }

        /* ---- metric cards ---- */
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.04);
            border: 0.5px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 14px 18px !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 11px !important;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: rgba(255,255,255,0.45) !important;
            font-family: 'DM Mono', monospace;
        }
        [data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: 600 !important;
            color: #f0ede4 !important;
        }
        [data-testid="stMetricDelta"] svg { display: none; }

        /* ---- headings ---- */
        h1, h2, h3 {
            color: #f0ede4 !important;
            letter-spacing: -0.02em;
        }

        /* ---- dataframe ---- */
        [data-testid="stDataFrame"] {
            border: 0.5px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            overflow: hidden;
        }

        /* ---- divider ---- */
        hr {
            border-color: rgba(255,255,255,0.08) !important;
        }

        /* ---- date input ---- */
        [data-testid="stDateInput"] input {
            background: rgba(255,255,255,0.05) !important;
            border: 0.5px solid rgba(255,255,255,0.15) !important;
            color: #f0ede4 !important;
            border-radius: 8px !important;
        }

        /* ---- selectbox ---- */
        [data-testid="stSelectbox"] > div > div {
            background: rgba(255,255,255,0.05) !important;
            border: 0.5px solid rgba(255,255,255,0.15) !important;
            border-radius: 8px !important;
            color: #f0ede4 !important;
        }

        /* ---- tabs ---- */
        [data-testid="stTabs"] [role="tab"] {
            font-size: 13px;
            color: rgba(255,255,255,0.5);
        }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            color: #e8a838;
            border-bottom-color: #e8a838 !important;
        }

        /* ---- expander ---- */
        [data-testid="stExpander"] {
            background: rgba(255,255,255,0.03);
            border: 0.5px solid rgba(255,255,255,0.08) !important;
            border-radius: 10px;
        }

        /* ---- info/warning boxes ---- */
        [data-testid="stInfo"] {
            background: rgba(55,138,221,0.1);
            border: 0.5px solid rgba(55,138,221,0.3);
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    """Render a consistent page header."""
    st.markdown(
        f"""
        <div style="
            display:flex;
            align-items:baseline;
            gap:14px;
            border-bottom:0.5px solid rgba(255,255,255,0.08);
            padding-bottom:16px;
            margin-bottom:24px;
        ">
            <span style="
                font-size:22px;
                font-weight:600;
                color:#f0ede4;
                letter-spacing:-0.02em;
            ">{title}</span>
            {"<span style='font-size:12px;color:rgba(255,255,255,0.4);font-family:monospace;'>" + subtitle + "</span>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    """Return an HTML badge for a profile status."""
    colors = {
        "customer": ("rgba(29,158,117,0.2)", "#5DCAA5"),
        "lead":     ("rgba(55,138,221,0.2)",  "#85B7EB"),
        "churned":  ("rgba(216,90,48,0.2)",   "#F0997B"),
    }
    bg, fg = colors.get(status.lower(), ("rgba(136,135,128,0.2)", "#B4B2A9"))
    return (
        f'<span style="background:{bg};color:{fg};'
        f'padding:2px 8px;border-radius:4px;font-size:11px;'
        f'font-family:monospace;white-space:nowrap;">{status}</span>'
    )


def kpi_row(metrics: list[dict]):
    """
    Render a row of Streamlit metric cards.
    Each dict: {label, value, delta (optional), delta_color (optional)}
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.metric(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
            )


def section_label(text: str):
    """Small uppercase section label."""
    st.markdown(
        f'<p style="font-size:10px;text-transform:uppercase;'
        f'letter-spacing:0.1em;color:rgba(255,255,255,0.4);'
        f'margin-bottom:8px;font-family:monospace;">{text}</p>',
        unsafe_allow_html=True,
    )


def channel_color(channel: str) -> str:
    return CHANNEL_COLORS.get(channel, "#888780")


def pct_delta(current: float, previous: float) -> str | None:
    """Return a formatted percentage delta string, or None."""
    if previous == 0:
        return None
    delta = (current - previous) / previous * 100
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.1f}%"
