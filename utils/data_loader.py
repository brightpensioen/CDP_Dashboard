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


@st.cache_data(ttl=300, show_spinner=False)
def load_profiles() -> pd.DataFrame:
    """
    Load all rows from tab_profiles.
    Cached for 5 minutes.
    """
    client = get_bq_client()
    query = f"""
        SELECT
            Email,
            status,
            profile_date,
            initial_client_id,
            first_session_date,
            initial_source,
            initial_medium,
            initial_campaign,
            initial_channel,
            initial_device_category,
            initial_browser,
            initial_operating_system,
            initial_country,
            initial_city,
            form_submissions,
            first_submission_date,
            last_submission_date,
            first_form,
            has_signed_up,
            signup_date,
            days_first_session_to_signup,
            das_id,
            das_participant_number,
            das_first_name,
            das_last_name,
            das_member_since,
            das_cancellation_date,
            das_paying_since,
            das_retirement_date,
            das_status,
            days_first_session_to_customer,
            days_signup_to_customer,
            last_updated_at
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
