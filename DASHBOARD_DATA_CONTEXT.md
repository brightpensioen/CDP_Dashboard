# CDP Dashboard — Data Model Context

This document describes the current state of the Dataform data model powering the CDP dashboard. Read this before making any changes to dashboard queries.

---

## What changed

A new pre-materialized `tab_sessions` table has been added to the `ds_cdp` dataset. It replaces any direct joins to raw GA4 tables at dashboard query time.

---

## Tables to use

### `ds_cdp.tab_profiles`
One row per profile (email). The spine of the CDP dashboard.

Key columns relevant to the dashboard:
- `Email` — primary key
- `all_client_ids` — ARRAY<STRING> of GA4 client IDs linked to this profile
- `status` — `'customer'` | `'lead'` | `'churned'`
- `profile_date` — partition key (DATE)
- `first_session_date` — DATE of the earliest known session
- `initial_source`, `initial_medium`, `initial_campaign`, `initial_channel` — first-touch attribution
- `initial_device_category`, `initial_browser`, `initial_operating_system`
- `initial_country`, `initial_city`
- `form_submissions` — ARRAY<STRUCT<FormName, SubmissionDate, Kortingspartner, Referrer, ReferrerOther>>
- `calendly_bookings` — ARRAY<STRUCT<EventTypeName, EventStartTime, BookedAt, EventDuration>>
- `webinar_registrations` — ARRAY<STRUCT<WebinarTitle, WebinarDate, RegistrationDate>>
- Various derived counts and dates (`calendly_booking_count`, `first_engagement_date`, etc.)
- DAS fields prefixed `das_` (member data from the pension administration system)

---

### `ds_cdp.tab_sessions`
One row per session per profile. Use this for the sessions tab on a profile detail view.

Partitioned by `session_date`. Clustered by `Email`, `session_type`.

Key columns:
- `Email` — foreign key to `tab_profiles`
- `session_type` — `'website'` or `'portal'`
- `client_id` — GA4 `user_pseudo_id` that generated this session
- `session_id` — INTEGER, unique GA4 session identifier
- `session_date` — DATE (partition key)
- `session_start_timestamp_utc` — TIMESTAMP, use for ordering sessions chronologically
- `source`, `medium`, `campaign`, `default_channel_grouping` — session-level attribution
- `device_category`, `browser`, `operating_system`
- `country`, `city`
- `events` — ARRAY<STRUCT<event_name STRING, event_timestamp TIMESTAMP, page_location STRING, page_path STRING, page_title STRING>>, ordered by timestamp ASC

#### How to query sessions for a profile
```sql
SELECT *
FROM `ds_cdp.tab_sessions`
WHERE Email = 'user@example.com'
ORDER BY session_start_timestamp_utc ASC
```

#### How to query sessions of a specific type
```sql
WHERE Email = 'user@example.com'
  AND session_type = 'website'   -- or 'portal'
```

#### How to access events within a session
Events are nested inside each session row. To display them, read the `events` array directly from the row — no second query needed. If you need to filter or flatten:
```sql
SELECT session_id, ev.event_name, ev.event_timestamp, ev.page_path
FROM `ds_cdp.tab_sessions`,
UNNEST(events) AS ev
WHERE Email = 'user@example.com'
ORDER BY ev.event_timestamp ASC
```

---

## Session sources

`tab_sessions` contains sessions from two sources, distinguished by `session_type`:

| `session_type` | Source dataset | Description |
|---|---|---|
| `'website'` | `superform_outputs_482420450` | Public-facing website (brightpensioen.nl) |
| `'portal'` | `superform_outputs_493050710` | Customer portal (logged-in members) |

---

## What NOT to do

- **Do not join directly to raw `ga4_sessions` or `ga4_events`** for dashboard queries. `tab_sessions` is the pre-joined, pre-materialized version — use that.
- **Do not join `tab_profiles.all_client_ids` to `ga4_sessions`** using `UNNEST` at query time. This is what `tab_sessions` already does at pipeline build time.
- **Do not query `tab_sessions` without a `WHERE Email = ...` filter** when loading a single profile — the table is clustered on `Email` so filtered queries are fast; full scans are expensive.

---

## Recommended query pattern for a profile detail page

```sql
-- 1. Load the profile
SELECT *
FROM `ds_cdp.tab_profiles`
WHERE Email = 'user@example.com';

-- 2. Load all sessions (separate query, on demand)
SELECT
  session_type,
  session_id,
  session_date,
  session_start_timestamp_utc,
  source,
  medium,
  default_channel_grouping,
  device_category,
  country,
  events  -- full events array per session
FROM `ds_cdp.tab_sessions`
WHERE Email = 'user@example.com'
ORDER BY session_start_timestamp_utc ASC;
```

Load sessions lazily (only when the user opens the sessions tab) rather than eagerly with the profile, to keep the initial page load fast.
