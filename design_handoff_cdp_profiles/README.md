# Handoff: CDP Profiles Redesign

## Overview
This is a redesign of the **Profiles** tab in BrightPensioen's internal Customer Data Platform (CDP). It addresses four requests from the product owner:

1. Surface two new data sources — **Calendly** and **WebinarGeek** — so marketing users are aware they now exist as engagement channels.
2. Remove the existing "First form submission" from the per-profile Timeline column.
3. Add a **Pipedrive-style activity timeline** on individual profiles showing every form submission, webinar registration, Calendly booking, signup, and DAS milestone.
4. Create a **dedicated detail page** for a profile instead of the current inline expand.

The intended user is non-technical marketing staff.

## About the Design Files
The files in this bundle are **design references created in HTML/React** — prototypes that show intended look and behavior. They are **not production code to ship directly.**

The task is to recreate these designs inside BrightPensioen's existing CDP frontend, using its established framework, component library, and data-fetching patterns. If no frontend exists yet, pick the most appropriate stack for the team and implement the designs there.

Ignore the in-page "Tweaks" panel and the top-left "Profiles list / Profile detail / Compare both" nav — those are prototype scaffolding, not features.

## Fidelity
**High-fidelity.** Final colors, typography, spacing, and interactions are settled. Recreate pixel-perfectly using real data from the schema shown below.

## Data Schema
The prototype consumes a BigQuery-style row per profile with these columns (subset of what was shared):

```
email, all_client_ids, status, profile_date,
initial_client_id, first_session_date,
initial_source, initial_medium, initial_campaign, initial_channel,
initial_device_category, initial_browser, initial_operating_system,
initial_country, initial_city,
form_submissions (JSON array), form_submissions_count, first_form,
webinar_registrations (JSON array), webinar_registration_count,
calendly_bookings (JSON array), calendly_booking_count,
has_signed_up, signup_date, days_first_session_to_signup,
has_booked_call, has_registered_webinar,
first_engagement_date,
das_id, das_participant_number, das_first_name, das_last_name,
das_member_since, das_cancellation_date, das_paying_since,
das_retirement_date, das_status,
days_first_session_to_customer, days_signup_to_customer,
last_updated_at
```

`status` is one of `lead | signed-up | customer`.

Each array element in `form_submissions`, `webinar_registrations`, `calendly_bookings` is its own event that should be emitted into the activity timeline.

## Screens

### 1. Profiles list (`/profiles`)
Full-page table replacing the current Profiles tab.

**Top bar**
- Title "Profiles" + subtle `tab.profiles` label (fontSize 11, color #6b7682)
- Right-aligned: "Export" ghost button, "New segment" primary button (accent = #4ade80)

**KPI cards** — 4-column grid, 12px gap
- MATCHING PROFILES (total) · CUSTOMERS (green #34d399) · LEADS (blue #60a5fa) · SIGNED UP (amber #fbbf24)
- Card: background #171d24, border #252d36, radius 8, padding 14×16
- Label: 10px uppercase tracked 0.1em, color #6b7682
- Value: 28px, weight 500, letter-spacing -0.02em
- Sub: 11px, color #6b7682

**Source Mix strip** (NEW — key change)
- Horizontal, wrapping, padding 10×12, background #151a20, border 1px #252d36, radius 8
- Label "SOURCE MIX" then one chip per channel including the two new ones
- Calendly chip uses dot color #fb923c on tint rgba(251,146,60,0.14)
- WebinarGeek chip uses dot color #a78bfa on tint rgba(167,139,250,0.14)
- Calendly and WebinarGeek chips carry a bright **NEW** pill (8px, bg=chip dot, text=bg color)
- Clicking a chip filters the table to that channel; click again or "clear" to remove
- Count per channel is shown next to the name

**Filter row**
- Search input with magnifier, 280px wide, placeholder "Search email, name, channel…"
- Segmented control: All / Customers / Leads / Signed up
- "More filters" ghost button
- Right: "N of total" count

**Table** (10 columns, grid layout)
`Email · Status · Profile date · Channel/Source · Location · Engagement · → Signup · → Customer · Name · ›`

- Row height ~40px, padding 10×14, border-bottom #252d36, hover bg rgba(255,255,255,0.025)
- Email cell: 22px circle avatar (initials) + email address
- Status cell: pill — see Components
- Channel cell: ChannelBadge (dot + name + NEW pill if Calendly/WebinarGeek) + dim source text
- **Engagement cell**: replaces the old "First form" column. Up to three small inline badges:
  - Forms (icon=form glyph, color=#22d3ee, bg rgba(34,211,238,0.14))
  - Webinars (icon=video, color=#a78bfa, bg rgba(167,139,250,0.14))
  - Calls (icon=calendar, color=#f472b6, bg rgba(244,114,182,0.14))
  - Each shows icon + count; hide the badge entirely if count=0; show `—` if none.
- Days columns are right-aligned; negative days-to-customer is colored amber (customer predates CDP attribution).
- Any row click navigates to `/profiles/:email`.

**Columns that must be REMOVED vs. current design**
- "First form" column is gone. The "First form submission" data moves into the Engagement column counts AND into the activity timeline on the detail page.

### 2. Profile detail (`/profiles/:email`)
Full-page view. Replaces the current inline expand.

**Sticky top bar** (height ~44, background #151a20, border-bottom #252d36)
- "← Profiles" back button
- Breadcrumb crumb "/ PROFILE DETAIL" (10px, tracked 0.1em, color #6b7682)
- Email, greyed
- Right: "Open in DAS", "Export", "⋯" (all ghost buttons)

**Header card** (padding 24×32, border-bottom)
- 64px avatar
- Name h1 (22px, weight 600, -0.01em tracking) + Status pill + optional DAS participant # pill
- Email on its own line (dim)
- Meta chips row: location / first seen / member since / device·browser·os

**KPI strip** (6 columns, row of mini-stats separated by vertical borders)
Days active · Form submissions · Webinar registrations · Calls booked · → Signup · → Customer

Mini-stat: label 9px uppercase tracked 0.1em, value 22px weight 500 letter-spacing -0.02em.

**Tabs** (padding 0 32px, border-bottom)
`Activity timeline · Engagements · Acquisition · DAS / Member · Raw data`
Active tab has 2px green #4ade80 underline; counts appear as small pills.

**Body** grid: main `1fr` + right rail `340px` with left border #252d36 and bg #151a20.

#### Activity timeline (default tab — the centerpiece)
- Filter chips above the lane: All / Engagement / Forms / Webinars / Calls (Engagement = forms+webinars+calls combined)
- Groups by day. Day header: weekday + date + relative ("Today", "Yesterday", "12d ago", "3mo ago", or "in Nd" if future).
- Vertical rail: 1px line at x=11px running from top to bottom of the group column.
- Each event = 22px circle node (tinted by event type) + a card.
- Card: bg #171d24, border #252d36, radius 6, padding 10×14, left border 2px in the event type's color.
- Card header: title + type pill (e.g., "WEBINAR REGISTRATION", 9px, tracked 0.05em) + right-aligned time.
- Card body (type-specific):
  - `first_session` — two-column: channel/device, source/location, medium/campaign
  - `form_submission` — form name
  - `webinar_registration` — webinar title + scheduled date (in UTC)
  - `calendly_booking` — scheduled time + duration
  - `customer` — participant number
  - `signup`, `paying_started` — no body
- Bottom genesis cap: dashed circle "✦" + "Profile begins".
- Empty state: centered dim "No activities for this filter."

**Event type palette**
| Type | Label | Color | Bg tint |
|---|---|---|---|
| first_session | First session | #9aa3ad | rgba(154,163,173,0.12) |
| form_submission | Form submission | #22d3ee | rgba(34,211,238,0.14) |
| webinar_registration | Webinar registration | #a78bfa | rgba(167,139,250,0.14) |
| calendly_booking | Calendly booking | #f472b6 | rgba(244,114,182,0.14) |
| signup | Signed up | #fbbf24 | rgba(251,191,36,0.12) |
| customer | Became customer | #34d399 | rgba(52,211,153,0.14) |
| paying_started | Started paying | #34d399 | rgba(52,211,153,0.14) |

**Explicitly NOT included (per product feedback)**
- No "Add note" button
- No quick-add composer ("Add a note, call, task…")
- No "Log activity" button

#### Engagements tab
Three stacked cards (Form submissions, Webinar registrations, Calendly bookings). Each card has a coloured icon header with count, then a list of rows. Empty state per card.

#### Acquisition tab
Simple label/value card: Channel, Source, Medium, Campaign, Country, City, Device, Browser, OS.

#### DAS / Member tab
Label/value card: DAS ID, Participant #, Member since, Paying since, Retirement date, Status. Empty-state copy when `das` is null.

#### Raw data tab
`<pre>` dump of the profile JSON (dates serialized to ISO) for power users.

### Right rail (shown on every tab)
- **Snapshot**: Lifecycle (status pill), Lead score (bar + number; customer=92, signed-up=68, lead=34), Last activity (relative time)
- **Upcoming**: auto-populated from any `calendly_booking` with `eventStart > now` or `webinar_registration` with `webinarDate > now`. Each row shows type icon + title + date + relative time. Empty state "Nothing scheduled."
- **Quick stats**: First session, Signed up, Customer, All client IDs
- **Attribution**: channel badge + source/medium/campaign

## Design Tokens

```css
/* Surfaces */
--bg:        #0e1216;  /* page */
--bg2:       #151a20;  /* raised panel */
--bg3:       #1c232b;  /* deepest slot */
--surface:   #171d24;  /* cards */
--surface-hi:#1f262e;  /* active segments */
--border:    #252d36;
--border-hi: #323b45;

/* Text */
--text:      #e6e8eb;
--text-dim:  #9aa3ad;
--text-mute: #6b7682;

/* Semantics */
--accent:    #4ade80;  /* primary green */
--accent-bg: rgba(74,222,128,0.12);
--customer:  #34d399;
--lead:      #60a5fa;
--signed:    #fbbf24;
--webinar:   #a78bfa;  /* also: WebinarGeek channel */
--call:      #f472b6;  /* Calendly events */
--form:      #22d3ee;
--calendly-channel: #fb923c;  /* Calendly as an acquisition channel */

/* Typography */
font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
/* No monospace — marketing users found it too technical. */

/* Radii, spacing */
radius-sm: 4px;
radius-md: 6px;
radius-lg: 8px;
row-padding: 10px 14px;
card-padding: 14px 16px;
```

## Components to build

- `Avatar` — circular, initials, 22/32/64 sizes, green tint
- `StatusPill` — `lead | signed-up | customer`; dot + 10px uppercase label tracked 0.08em
- `ChannelBadge` — dot + channel name; appends a bright `NEW` pill when channel is Calendly or WebinarGeek
- `EngagementBadges` — row of 0–3 icon+count chips (forms/webinars/calls) used in the list table
- `KpiCard`, `MiniStat` — header stats
- `SourceStrip` — filterable chip strip above the table
- `Tabs` — underline style with count pills
- `Timeline` + `TimelineEvent` — day-grouped event rail
- `RightRail` sections — Snapshot / Upcoming / Quick stats / Attribution

## Interactions

- Row click on list → navigate to detail
- Back button on detail → list (preserve filter state ideally)
- Channel chips in Source Mix → toggle single-channel filter on the table
- Status segmented control → filter
- Search → client-side match on email, name, channel, source
- Column headers sortable (asc/desc toggle)
- Activity filter chips on detail → filter timeline
- All hover states: row bg rgba(255,255,255,0.025); ghost buttons subtly brighten

## Files included

- `CDP Profiles Redesign.html` — entry point
- `profiles-data.jsx` — mock data + schema shape
- `profiles-ui.jsx` — design tokens, Icon set, shared primitives (Avatar, StatusPill, ChannelBadge)
- `profiles-list.jsx` — list screen
- `profiles-detail.jsx` — detail screen
- `design-canvas.jsx` — side-by-side compare canvas (prototype scaffolding only; ignore for implementation)

## Implementation notes

- The prototype uses inline React styles for speed — use your codebase's styling system (CSS Modules / Tailwind / styled-components) when porting.
- Activity events are derived from the three JSON array columns plus status/DAS fields. In production, compose them server-side or in a `useMemo` from the raw row so the timeline always reflects the latest BigQuery data.
- Upcoming events are simply events whose date is in the future — filter at render time.
- Negative `days_first_session_to_customer` (customer predates tracking) should render amber, not red.
