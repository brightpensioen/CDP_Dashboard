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

PROJECT_ID = "prj-data-warehousing"
DATASET = "ds_cdp"


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


@st.cache_data(ttl=900, show_spinner=False)
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




@st.cache_data(ttl=900, show_spinner=False)
def load_profile_sessions(email: str) -> pd.DataFrame:
    """
    All sessions for a single profile from ds_cdp.tab_sessions.
    Includes the nested events array for page-level detail.
    Cached 5 minutes.
    """
    client = get_bq_client()
    query = f"""
        SELECT
            session_type,
            session_id,
            session_date,
            session_start_timestamp_utc,
            source,
            medium,
            campaign,
            default_channel_grouping,
            device_category,
            browser,
            operating_system,
            country,
            city,
            events
        FROM `{PROJECT_ID}.{DATASET}.tab_sessions`
        WHERE Email = @email
        ORDER BY session_start_timestamp_utc ASC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
    )
    df = client.query(query, job_config=job_config).to_dataframe()
    if not df.empty:
        df["session_start_timestamp_utc"] = pd.to_datetime(
            df["session_start_timestamp_utc"], errors="coerce", utc=True
        )
        df["session_id"] = pd.to_numeric(df["session_id"], errors="coerce")
    return df
