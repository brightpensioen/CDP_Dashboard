"""
Source Tracking page — week-over-week attribution from vw_source_tracking_enriched.
Date picker, leads + customers split, channel comparison line charts.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from components.ui import (
    inject_global_css, page_header, section_label, kpi_row,
    pct_delta, channel_color, CHANNEL_COLORS,
)
from components.charts import source_bar_chart, wow_comparison_chart
from utils.data_loader import load_source_tracking


DEFAULT_LOOKBACK_DAYS = 56  # 8 weeks


def render():
    inject_global_css()
    page_header("Source Tracking", subtitle="vw_source_tracking_enriched")

    # ── date picker in sidebar ────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Date range")
        start_date = st.date_input("Start date", value=date.today() - timedelta(days=DEFAULT_LOOKBACK_DAYS))
        end_date   = st.date_input("End date",   value=date.today())

        if start_date >= end_date:
            st.error("Start date must be before end date.")
            return

    metric = "new_leads"

    # ── load data ─────────────────────────────────────────────────────────────
    with st.spinner("Loading source tracking data…"):
        df = load_source_tracking(str(start_date), str(end_date))

    if df.empty:
        st.info("No source tracking data found for the selected date range.")
        return

    # ── clean channel column ──────────────────────────────────────────────────
    df["initial_channel"] = df["initial_channel"].fillna("(Other)").replace("", "(Other)")

    # ── KPIs: totals for date range ───────────────────────────────────────────
    total_users     = int(df["total_users"].sum())
    total_leads     = int(df["new_leads"].sum())
    total_customers = int(df["new_customers"].sum())
    total_churned   = int(df["new_churned"].sum())

    # split into two halves to compute WoW-style delta
    weeks_sorted = sorted(df["activity_week"].unique())
    mid = len(weeks_sorted) // 2
    first_half  = df[df["activity_week"].isin(weeks_sorted[:mid])]
    second_half = df[df["activity_week"].isin(weeks_sorted[mid:])]

    leads_delta     = pct_delta(second_half["new_leads"].sum(),     first_half["new_leads"].sum())
    customers_delta = pct_delta(second_half["new_customers"].sum(), first_half["new_customers"].sum())
    users_delta     = pct_delta(second_half["total_users"].sum(),   first_half["total_users"].sum())

    kpi_row([
        {"label": "Total users",     "value": f"{total_users:,}",     "delta": users_delta},
        {"label": "New leads",       "value": f"{total_leads:,}",      "delta": leads_delta},
        {"label": "New customers",   "value": f"{total_customers:,}",  "delta": customers_delta},
    ])

    st.write("")

    # ── date range label ──────────────────────────────────────────────────────
    n_weeks = len(weeks_sorted)
    st.markdown(
        f'<p style="font-size:12px;color:rgba(255,255,255,0.4);margin-bottom:16px;">'
        f'Showing <b style="color:#e8a838;">{n_weeks} weeks</b> from '
        f'<b style="color:#f0ede4;">{start_date}</b> to '
        f'<b style="color:#f0ede4;">{end_date}</b></p>',
        unsafe_allow_html=True,
    )

    # ── tabs: Leads | Customers | Both ────────────────────────────────────────
    tab_leads, tab_customers, tab_compare = st.tabs(
        ["📥 Leads by source", "🎯 Customers by source", "📈 Week-over-week trend"]
    )

    with tab_leads:
        _render_source_breakdown(df, "new_leads", "New leads by channel")

    with tab_customers:
        _render_source_breakdown(df, "new_customers", "New customers by channel")

    with tab_compare:
        _render_wow_trend(df, metric, weeks_sorted)

    st.divider()

    # ── raw data table ────────────────────────────────────────────────────────
    with st.expander("Raw source tracking data", expanded=False):
        section_label(f"{len(df):,} rows")

        display = df.copy()
        display["activity_week"] = display["activity_week"].dt.strftime("%Y-%m-%d")

        # round float rates
        rate_cols = ["visitor_to_lead_rate", "lead_to_signup_rate",
                     "signup_to_customer_rate", "visitor_to_customer_rate"]
        for col in rate_cols:
            if col in display.columns:
                display[col] = display[col].apply(lambda x: f"{x:.3f}" if x else "—")

        st.dataframe(
            display,
            use_container_width=True,
            height=400,
            hide_index=True,
        )


def _render_source_breakdown(df: pd.DataFrame, metric: str, title: str):
    """Bar chart + week-by-channel pivot table for one metric."""
    col_bar, col_pivot = st.columns([1, 1], gap="medium")

    with col_bar:
        section_label("By channel — full period")
        fig = source_bar_chart(df, metric, title)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_pivot:
        section_label("By channel × week")

        pivot = (
            df.groupby(["initial_channel", "activity_week"])[metric]
            .sum()
            .unstack(level="activity_week")
            .fillna(0)
            .astype(int)
        )
        pivot.columns = [c.strftime("%b %d") if hasattr(c, "strftime") else str(c) for c in pivot.columns]
        pivot.index.name = "Channel"
        pivot["Total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("Total", ascending=False)

        st.dataframe(
            pivot,
            use_container_width=True,
            height=380,
            column_config={
                col: st.column_config.NumberColumn(col, format="%d")
                for col in pivot.columns
            },
        )

    # ── conversion rates for selected metric ──────────────────────────────────
    st.write("")
    section_label("Conversion rates by channel")

    rate_col = "visitor_to_customer_rate" if metric == "new_customers" else "visitor_to_lead_rate"
    rate_agg = (
        df[df[rate_col] > 0]
        .groupby("initial_channel")[[metric, rate_col]]
        .agg({metric: "sum", rate_col: "mean"})
        .reset_index()
        .sort_values(metric, ascending=False)
        .head(10)
    )
    rate_agg[rate_col] = (rate_agg[rate_col] * 100).round(2)
    rate_agg.columns = ["Channel", metric.replace("_", " ").title(), "Avg rate (%)"]
    st.dataframe(rate_agg, use_container_width=True, hide_index=True)


def _render_wow_trend(df: pd.DataFrame, metric: str, weeks_sorted):
    """Line chart showing metric over weeks by top channels."""
    agg = (
        df.groupby(["activity_week", "initial_channel"])[metric]
        .sum()
        .reset_index()
    )

    # determine top channels by total volume
    top_channels = (
        agg.groupby("initial_channel")[metric]
        .sum()
        .sort_values(ascending=False)
        .head(6)
        .index.tolist()
    )

    selected_channels = top_channels

    if not selected_channels:
        st.info("Select at least one channel in the sidebar.")
        return

    filtered_agg = agg[agg["initial_channel"].isin(selected_channels)]

    section_label(f"{metric.replace('_', ' ').title()} by channel · weekly")
    fig = wow_comparison_chart(filtered_agg, metric, selected_channels)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # totals summary below the chart
    st.write("")
    section_label("Period totals per channel")
    totals = (
        filtered_agg.groupby("initial_channel")[metric]
        .sum()
        .reset_index()
        .sort_values(metric, ascending=False)
    )
    totals.columns = ["Channel", metric.replace("_", " ").title()]
    totals["Share %"] = (totals[totals.columns[1]] / totals[totals.columns[1]].sum() * 100).round(1)

    st.dataframe(totals, use_container_width=True, hide_index=True)
