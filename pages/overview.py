"""
Overview page — CDP health dashboard.
Shows KPIs, week-over-week growth, status donut, and a conversion funnel.
"""

import streamlit as st
import pandas as pd
from datetime import date

from components.ui import inject_global_css, page_header, kpi_row, section_label, pct_delta
from components.charts import weekly_growth_chart, status_donut, conversion_funnel
from utils.data_loader import load_profiles, load_profile_growth, load_source_tracking


def render():
    inject_global_css()
    page_header(
        "CDP Overview",
        subtitle="tab_profiles · vw_source_tracking_enriched",
    )

    # ── date picker ───────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Date range")
        start_date = st.date_input("Start date", value=date(2026, 3, 1))
        end_date   = st.date_input("End date",   value=date.today())
        if start_date >= end_date:
            st.error("Start date must be before end date.")
            return

    # ── load data ─────────────────────────────────────────────────────────────
    with st.spinner("Loading profiles…"):
        df_profiles = load_profiles()

    with st.spinner("Loading growth data…"):
        df_growth = load_profile_growth()

    # ── filter to date range ──────────────────────────────────────────────────
    start_ts = pd.Timestamp(start_date, tz="UTC")
    end_ts   = pd.Timestamp(end_date,   tz="UTC") + pd.Timedelta(days=1)
    df_filtered = df_profiles[
        df_profiles["profile_date"].between(start_ts, end_ts, inclusive="left")
    ]

    # ── derive KPIs ───────────────────────────────────────────────────────────
    total = len(df_filtered)
    status_counts = df_filtered["status"].value_counts()
    n_customer = int(status_counts.get("customer", 0))
    n_lead     = int(status_counts.get("lead", 0))
    n_churned  = int(status_counts.get("churned", 0))

    # ── top KPIs ──────────────────────────────────────────────────────────────
    kpi_row([
        {"label": "Total profiles",  "value": f"{total:,}",      "delta": None},
        {"label": "Customers",        "value": f"{n_customer:,}", "delta": f"{n_customer/total*100:.0f}% of total" if total else None, "delta_color": "off"},
        {"label": "Leads",            "value": f"{n_lead:,}",     "delta": f"{n_lead/total*100:.0f}% of total" if total else None, "delta_color": "off"},
        {"label": "Churned",          "value": f"{n_churned:,}",  "delta": f"{n_churned/total*100:.0f}% of total" if total else None, "delta_color": "off"},
    ])

    st.write("")

    # ── row 2: growth + donut ─────────────────────────────────────────────────
    col_growth, col_donut = st.columns([3, 1], gap="medium")

    with col_growth:
        section_label("Weekly new profiles — by status")
        if df_growth.empty:
            st.info("No growth data available.")
        else:
            st.plotly_chart(weekly_growth_chart(df_growth), use_container_width=True, config={"displayModeBar": False})

    with col_donut:
        section_label("Status distribution")
        counts = {
            "customer": n_customer,
            "lead":     n_lead,
            "churned":  n_churned,
        }
        st.plotly_chart(status_donut(counts), use_container_width=True, config={"displayModeBar": False})

        # legend
        for status, color in [("Customer", "#1d9e75"), ("Lead", "#378ADD"), ("Churned", "#D85A30")]:
            n = counts[status.lower()]
            pct = n / total * 100 if total else 0
            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'margin-bottom:4px;">'
                f'<span style="display:flex;align-items:center;gap:6px;font-size:12px;'
                f'color:rgba(255,255,255,0.6);">'
                f'<span style="width:8px;height:8px;border-radius:2px;background:{color};'
                f'display:inline-block;"></span>{status}</span>'
                f'<span style="font-family:monospace;font-size:12px;color:#f0ede4;">'
                f'{n} <span style="color:rgba(255,255,255,0.4);">({pct:.0f}%)</span></span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── row 3: funnel + health checks ─────────────────────────────────────────
    col_funnel, col_health = st.columns([1, 1], gap="medium")

    with col_funnel:
        section_label("Aggregate conversion funnel")

        with st.spinner("Loading source data for funnel…"):
            df_src = load_source_tracking(str(start_date), str(end_date))

        if not df_src.empty:
            visitors  = int(df_src["total_users"].sum())
            leads     = int(df_src["new_leads"].sum())
            signups   = int(df_src["new_signed_up"].sum())
            customers = int(df_src["new_customers"].sum())
            st.plotly_chart(
                conversion_funnel(visitors, leads, signups, customers),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        else:
            st.info("No source tracking data in the last 90 days.")

    with col_health:
        section_label("CDP health checks")

        # --- check 1: profiles without form submissions
        no_forms = df_profiles[
            df_profiles["first_submission_date"].isna()
        ]
        _health_check(
            "Profiles without form submissions",
            len(no_forms),
            total,
            threshold_pct=20,
        )

        # --- check 2: profiles missing channel info
        no_channel = df_profiles[
            df_profiles["initial_channel"].isna() | (df_profiles["initial_channel"] == "")
        ]
        _health_check(
            "Profiles missing initial channel",
            len(no_channel),
            total,
            threshold_pct=15,
        )

        # --- check 3: customers without DAS ID
        cust_no_das = df_profiles[
            (df_profiles["status"] == "customer") & df_profiles["das_id"].isna()
        ]
        _health_check(
            "Customers without DAS ID",
            len(cust_no_das),
            n_customer,
            threshold_pct=10,
        )

        # --- check 4: duplicate emails
        dup_emails = df_profiles["Email"].value_counts()
        n_dups = int((dup_emails > 1).sum())
        _health_check(
            "Duplicate email addresses",
            n_dups,
            total,
            threshold_pct=5,
        )

        # --- check 5: last update recency
        if "last_updated_at" in df_profiles.columns and not df_profiles["last_updated_at"].isna().all():
            last_update = df_profiles["last_updated_at"].max()
            hours_ago = (pd.Timestamp.now(tz="UTC") - last_update).total_seconds() / 3600
            if hours_ago < 24:
                st.success(f"✓ Last updated {hours_ago:.1f}h ago")
            elif hours_ago < 72:
                st.warning(f"⚠ Last updated {hours_ago:.1f}h ago — may be stale")
            else:
                st.error(f"✗ Last updated {hours_ago:.1f}h ago — check pipeline")


def _health_check(label: str, count: int, total: int, threshold_pct: float):
    """Render a single health check row."""
    pct = count / total * 100 if total else 0
    if pct == 0:
        icon, color = "✓", "#1d9e75"
    elif pct <= threshold_pct:
        icon, color = "⚠", "#e8a838"
    else:
        icon, color = "✗", "#D85A30"

    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'background:rgba(255,255,255,0.03);border:0.5px solid rgba(255,255,255,0.07);'
        f'border-radius:8px;padding:10px 14px;margin-bottom:8px;">'
        f'<span style="font-size:12px;color:rgba(255,255,255,0.7);">{label}</span>'
        f'<span style="font-family:monospace;font-size:12px;color:{color};">'
        f'{icon} {count} ({pct:.1f}%)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
