"""
Profiles page — scrollable, filterable table of tab_profiles rows.
"""

import streamlit as st
import pandas as pd

from components.ui import inject_global_css, page_header, section_label, status_badge
from components.charts import form_submission_timeline
from utils.data_loader import load_profiles


DISPLAY_COLS = [
    "Email", "status", "profile_date", "initial_channel", "initial_source",
    "initial_country", "initial_city", "first_form", "has_signed_up",
    "days_first_session_to_signup", "days_first_session_to_customer",
    "das_first_name", "das_last_name", "das_status",
]


def render():
    inject_global_css()
    page_header("Profiles", subtitle="tab_profiles")

    with st.spinner("Loading profiles…"):
        df = load_profiles()

    if df.empty:
        st.warning("No profiles found.")
        return

    # ── sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Filters")

        statuses = ["All"] + sorted(df["status"].dropna().unique().tolist())
        selected_status = st.selectbox("Status", statuses)

        channels = ["All"] + sorted(df["initial_channel"].dropna().unique().tolist())
        selected_channel = st.selectbox("Initial channel", channels)

        countries = ["All"] + sorted(df["initial_country"].dropna().unique().tolist())
        selected_country = st.selectbox("Country", countries)

        search = st.text_input("Search email / name", placeholder="e.g. jan@example.com")

        st.divider()
        st.caption(f"{len(df):,} profiles total")

    # ── apply filters ─────────────────────────────────────────────────────────
    filtered = df.copy()

    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]

    if selected_channel != "All":
        filtered = filtered[filtered["initial_channel"] == selected_channel]

    if selected_country != "All":
        filtered = filtered[filtered["initial_country"] == selected_country]

    if search.strip():
        q = search.strip().lower()
        mask = (
            filtered["Email"].str.lower().str.contains(q, na=False) |
            filtered["das_first_name"].str.lower().str.contains(q, na=False) |
            filtered["das_last_name"].str.lower().str.contains(q, na=False)
        )
        filtered = filtered[mask]

    # ── KPI strip ─────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Matching profiles",  f"{len(filtered):,}")
    col2.metric("Customers",  int(filtered["status"].eq("customer").sum()))
    col3.metric("Leads",      int(filtered["status"].eq("lead").sum()))
    col4.metric("Signed up",  int(filtered["has_signed_up"].eq(True).sum()) if "has_signed_up" in filtered.columns else "—")

    st.write("")

    # ── profile table ─────────────────────────────────────────────────────────
    section_label(f"Showing {len(filtered):,} of {len(df):,} profiles")

    display = filtered[[c for c in DISPLAY_COLS if c in filtered.columns]].copy()

    # format dates
    for col in ["profile_date", "first_submission_date"]:
        if col in display.columns:
            display[col] = display[col].dt.strftime("%Y-%m-%d").fillna("—")

    # shorten numeric columns
    for col in ["days_first_session_to_signup", "days_first_session_to_customer"]:
        if col in display.columns:
            display[col] = display[col].apply(lambda x: "—" if pd.isna(x) else str(int(x)))

    # rename for display
    display = display.rename(columns={
        "profile_date":                    "Profile date",
        "initial_channel":                 "Channel",
        "initial_source":                  "Source",
        "initial_country":                 "Country",
        "initial_city":                    "City",
        "first_form":                      "First form",
        "has_signed_up":                   "Signed up",
        "days_first_session_to_signup":    "Days → signup",
        "days_first_session_to_customer":  "Days → customer",
        "das_first_name":                  "First name",
        "das_last_name":                   "Last name",
        "das_status":                      "DAS status",
    })

    st.dataframe(
        display,
        use_container_width=True,
        height=480,
        column_config={
            "status": st.column_config.TextColumn("Status", width="small"),
            "Email":  st.column_config.TextColumn("Email", width="medium"),
            "Channel": st.column_config.TextColumn("Channel", width="medium"),
        },
        hide_index=True,
    )

    # ── form submission timeline ───────────────────────────────────────────────
    st.divider()
    section_label("First form submission timeline")
    if "first_submission_date" in df.columns:
        st.plotly_chart(
            form_submission_timeline(filtered if len(filtered) > 0 else df),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.info("No submission date data available.")

    # ── profile detail expander ───────────────────────────────────────────────
    st.divider()
    section_label("Profile detail — click to expand")

    email_options = filtered["Email"].dropna().tolist()
    if email_options:
        selected_email = st.selectbox(
            "Select a profile to inspect",
            email_options,
            label_visibility="collapsed",
        )
        if selected_email:
            row = filtered[filtered["Email"] == selected_email].iloc[0]
            _render_profile_detail(row)


def _render_profile_detail(row: pd.Series):
    """Render a detailed card for a single profile."""
    status = str(row.get("status", "")).lower()
    status_colors = {
        "customer": ("#1d9e75", "rgba(29,158,117,0.15)"),
        "lead":     ("#378ADD", "rgba(55,138,221,0.15)"),
        "churned":  ("#D85A30", "rgba(216,90,48,0.15)"),
    }
    fg, bg = status_colors.get(status, ("#888780", "rgba(136,135,128,0.1)"))

    first = str(row.get("das_first_name", "") or "")
    last  = str(row.get("das_last_name",  "") or "")
    initials = (first[:1] + last[:1]).upper() or "?"
    full_name = f"{first} {last}".strip() or row.get("Email", "")
    email = str(row.get("Email", ""))

    col_avatar, col_info, col_badge = st.columns([1, 8, 2])
    with col_avatar:
        st.markdown(
            f'<div style="width:48px;height:48px;border-radius:50%;'
            f'background:{bg};border:1.5px solid {fg};'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:16px;font-weight:600;color:{fg};">{initials}</div>',
            unsafe_allow_html=True,
        )
    with col_info:
        st.markdown(f'<div style="font-size:16px;font-weight:600;color:#f0ede4;">{full_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:12px;color:rgba(255,255,255,0.5);">{email}</div>', unsafe_allow_html=True)
    with col_badge:
        st.markdown(
            f'<div style="text-align:right;"><span style="background:{bg};color:{fg};'
            f'padding:3px 10px;border-radius:4px;font-size:11px;font-family:monospace;">{status}</span></div>',
            unsafe_allow_html=True,
        )

    with st.expander("Full profile data", expanded=True):
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown("**Acquisition**")
            _detail_row("Channel",  row.get("initial_channel"))
            _detail_row("Source",   row.get("initial_source"))
            _detail_row("Medium",   row.get("initial_medium"))
            _detail_row("Campaign", row.get("initial_campaign"))
            _detail_row("Country",  row.get("initial_country"))
            _detail_row("City",     row.get("initial_city"))
            _detail_row("Device",   row.get("initial_device_category"))
            _detail_row("Browser",  row.get("initial_browser"))

        with col_b:
            st.markdown("**Timeline**")
            _detail_row("Profile date",    row.get("profile_date"))
            _detail_row("First session",   row.get("first_session_date"))
            _detail_row("First form",      row.get("first_form"))
            _detail_row("First sub date",  row.get("first_submission_date"))
            _detail_row("Last sub date",   row.get("last_submission_date"))
            _detail_row("Signup date",     row.get("signup_date"))
            _detail_row("Days → signup",   row.get("days_first_session_to_signup"))
            _detail_row("Days → customer", row.get("days_first_session_to_customer"))

        with col_c:
            st.markdown("**DAS / Member**")
            _detail_row("DAS ID",          row.get("das_id"))
            _detail_row("Participant #",    row.get("das_participant_number"))
            _detail_row("DAS status",       row.get("das_status"))
            _detail_row("Member since",     row.get("das_member_since"))
            _detail_row("Paying since",     row.get("das_paying_since"))
            _detail_row("Retirement date",  row.get("das_retirement_date"))
            _detail_row("Cancellation",     row.get("das_cancellation_date"))


def _detail_row(label: str, value):
    """Render a key-value detail row."""
    val = "—"
    if value is not None and not (isinstance(value, float) and pd.isna(value)):
        if hasattr(value, "strftime"):
            val = str(value)[:10]
        else:
            val = str(value) if str(value) not in ("", "nan", "None", "NaT") else "—"

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;'
        f'padding:4px 0;border-bottom:0.5px solid rgba(255,255,255,0.04);">'
        f'<span style="font-size:11px;color:rgba(255,255,255,0.45);">{label}</span>'
        f'<span style="font-size:11px;font-family:monospace;color:rgba(240,237,228,0.85);'
        f'max-width:160px;overflow:hidden;text-overflow:ellipsis;">{val}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
