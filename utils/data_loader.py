"""
BigQuery data loading utilities with Streamlit caching.

Setup:
    1. Set GCP credentials via st.secrets or GOOGLE_APPLICATION_CREDENTIALS env var.
    2. Update PROJECT_ID and DATASET below.
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import json

PROJECT_ID = "prj-data-warehousing"
DATASET = "ds_cdp"

SESSIONS_PROJECT_ID = "prj-data-ingestion-435806"
SESSIONS_DATASET    = "superform_outputs_482420450"
SESSIONS_TABLE      = "ga4_sessions"
EVENTS_TABLE        = "ga4_events"


def get_bq_client() -> bigquery.Client:
    """
    Returns a BigQuery client.
    Priority:
      1. st.secrets["gcp_service_account"]  (recommended for Streamlit Cloud)
      2. Application Default Credentials      (local dev / GCE / Cloud Run)
    """
    if "gcp_service_account" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(credentials=credentials, project=PROJECT_ID)

    return bigquery.Client(project=PROJECT_ID)


@st.cache_data(ttl=3600, show_spinner=False)
def _profile_columns() -> list[str]:
    """Return column names for tab_profiles (cached 1 h)."""
    client = get_bq_client()
    query = f"""
        SELECT column_name
        FROM `{PROJECT_ID}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'tab_profiles'
        ORDER BY ordinal_position
    """
    return [r.column_name for r in client.query(query).result()]


@st.cache_data(ttl=300, show_spinner=False)
def load_profiles() -> pd.DataFrame:
    """
    Load all rows from tab_profiles.
    Cached for 5 minutes.
    """
    client = get_bq_client()
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET}.tab_profiles`
        WHERE initial_client_id IS NOT NULL
        ORDER BY profile_date DESC
    """
    df = client.query(query).to_dataframe()

    # --- type coercions ---
    date_cols = [
        "profile_date", "first_session_date", "first_submission_date",
        "last_submission_date", "signup_date", "das_member_since",
        "das_cancellation_date", "das_paying_since", "das_retirement_date",
        "last_updated_at",
        # webinar / calendly dates
        "first_webinar_registration_date", "last_webinar_registration_date",
        "first_calendly_booking_date",     "last_calendly_booking_date",
        "first_engagement_date",
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    int_cols = ["days_first_session_to_signup", "days_first_session_to_customer", "days_signup_to_customer"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_source_tracking(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Load source tracking data for a given date range.
    start_date / end_date: 'YYYY-MM-DD' strings.
    """
    client = get_bq_client()
    query = f"""
        SELECT
            activity_week,
            initial_channel,
            initial_source,
            initial_medium,
            initial_campaign,
            total_users,
            new_users,
            returning_users,
            new_anonymous_visitors,
            new_leads,
            new_signed_up,
            new_customers,
            new_churned,
            visitor_to_lead_rate,
            lead_to_signup_rate,
            signup_to_customer_rate,
            visitor_to_customer_rate,
            avg_days_to_signup,
            avg_days_to_customer
        FROM `{PROJECT_ID}.{DATASET}.vw_source_tracking_enriched`
        WHERE activity_week BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY activity_week DESC, total_users DESC
    """
    df = client.query(query).to_dataframe()
    df["activity_week"] = pd.to_datetime(df["activity_week"], errors="coerce")
    numeric_cols = [
        "total_users", "new_users", "returning_users", "new_anonymous_visitors",
        "new_leads", "new_signed_up", "new_customers", "new_churned",
        "visitor_to_lead_rate", "lead_to_signup_rate", "signup_to_customer_rate",
        "visitor_to_customer_rate", "avg_days_to_signup", "avg_days_to_customer",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_profile_growth() -> pd.DataFrame:
    """
    Week-over-week growth in profile count by status.
    Uses profile_date bucketed to Monday of each week.
    """
    client = get_bq_client()
    query = f"""
        SELECT
            DATE_TRUNC(DATE(profile_date), WEEK(MONDAY)) AS week,
            status,
            COUNT(*) AS new_profiles
        FROM `{PROJECT_ID}.{DATASET}.tab_profiles`
        WHERE initial_client_id IS NOT NULL
          AND profile_date IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1
    """
    df = client.query(query).to_dataframe()
    df["week"] = pd.to_datetime(df["week"], errors="coerce")
    df["new_profiles"] = pd.to_numeric(df["new_profiles"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=600, show_spinner=False)
def load_all_sessions() -> pd.DataFrame:
    """
    All GA4 sessions for all known profiles, joined via tab_profiles.all_client_ids.
    Cached 10 minutes. One bulk query at startup; per-profile views are in-memory filters.
    """
    client = get_bq_client()
    query = f"""
        SELECT
            s.session_id,
            s.user_pseudo_id,
            s.time.session_start_timestamp_utc,
            s.time.session_duration_s,
            s.landing_page.landing_page_path,
            s.exit_page.exit_page_path,
            s.session_source.source,
            s.session_source.medium,
            s.session_source.campaign,
            s.session_source.default_channel_grouping AS channel,
            s.device.category                         AS device_category,
            s.device.web_info.browser                 AS browser,
            s.geo.city,
            s.geo.country,
            s.session_info.is_engaged_session
        FROM `{SESSIONS_PROJECT_ID}.{SESSIONS_DATASET}.{SESSIONS_TABLE}` s
        INNER JOIN (
            SELECT DISTINCT cid AS user_pseudo_id
            FROM `{PROJECT_ID}.{DATASET}.tab_profiles`,
            UNNEST(all_client_ids) AS cid
            WHERE cid IS NOT NULL
        ) p ON s.user_pseudo_id = p.user_pseudo_id
        ORDER BY s.time.session_start_timestamp_utc DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df["session_start_timestamp_utc"] = pd.to_datetime(
            df["session_start_timestamp_utc"], errors="coerce", utc=True
        )
        df["session_duration_s"] = pd.to_numeric(df["session_duration_s"], errors="coerce")
        df["session_id"]         = pd.to_numeric(df["session_id"],         errors="coerce")
    return df


@st.cache_data(ttl=600, show_spinner=False)
def load_all_page_views() -> pd.DataFrame:
    """
    All page-view events (one row per page visit per session) for all known profiles.
    Groups by session_id + page_number to deduplicate reprocessing runs while
    preserving revisits to the same URL within a session.
    Includes page_number and page_duration_s computed in pandas after loading.
    Cached 10 minutes.
    """
    client = get_bq_client()
    query = f"""
        SELECT
            e.session_id,
            CAST(e.session_info.page_number AS INT64) AS page_number_raw,
            ANY_VALUE(e.page.path)                   AS path,
            ANY_VALUE(e.page.title)                  AS title,
            MIN(e.time.event_timestamp_utc)          AS first_visit
        FROM `{SESSIONS_PROJECT_ID}.{SESSIONS_DATASET}.{EVENTS_TABLE}` e
        INNER JOIN (
            SELECT DISTINCT cid AS user_pseudo_id
            FROM `{PROJECT_ID}.{DATASET}.tab_profiles`,
            UNNEST(all_client_ids) AS cid
            WHERE cid IS NOT NULL
        ) p ON e.user_pseudo_id = p.user_pseudo_id
        WHERE e.event_name IN ('page_view', 'user_engagement')
          AND e.session_id IS NOT NULL
          AND e.session_info.page_number IS NOT NULL
          AND e.page.path IS NOT NULL
        GROUP BY e.session_id, e.session_info.page_number
        ORDER BY e.session_id, first_visit
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df["session_id"]    = pd.to_numeric(df["session_id"],       errors="coerce")
        df["page_number"]   = pd.to_numeric(df["page_number_raw"],  errors="coerce")
        df["first_visit"]   = pd.to_datetime(df["first_visit"],     errors="coerce", utc=True)
        df.drop(columns=["page_number_raw"], inplace=True)
        df = df.sort_values(["session_id", "page_number"]).reset_index(drop=True)
        df["next_visit"]      = df.groupby("session_id")["first_visit"].shift(-1)
        df["page_duration_s"] = (
            (df["next_visit"] - df["first_visit"]).dt.total_seconds().round(0)
        )
        df.drop(columns=["next_visit"], inplace=True)
    return df
