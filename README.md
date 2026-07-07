# CDP Intelligence Dashboard

A Streamlit application for monitoring and exploring your Customer Data Platforms.

## Data sources

| Table | Purpose |
|-------|---------|
| `prj-data-warehousing.ds_cdp.tab_profiles` | One row per identified profile (customer, lead, churned) |
| `prj-data-warehousing.ds_cdp.vw_source_tracking_enriched` | Weekly aggregated acquisition funnel by channel/source/campaign |

## Pages

| Page | What it shows |
|------|---------------|
| **Overview** | KPI cards, week-over-week profile growth, status donut, conversion funnel, CDP health checks |
| **Profiles** | Filterable/searchable table of all profiles, individual profile detail cards |
| **Source Tracking** | Date-picker-driven channel attribution, leads vs customers per channel, week-over-week trend lines |

## Local setup

### 1. Clone & install

```bash
git clone <your-repo>
cd cdp_dashboard
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure BigQuery credentials

The app uses Application Default Credentials only — no service account key files.

```bash
gcloud auth application-default login
# The app will automatically pick these up
```

### 3. Run

```bash
streamlit run app.py
```

The dashboard opens at [http://localhost:8501](http://localhost:8501).

## Deployment (internal)

### Google Cloud Run

Authentication to BigQuery happens via the service account **attached** to the
Cloud Run service (Application Default Credentials). No exported key files are
used anywhere.

```bash
# One-time: dedicated runtime service account
gcloud iam service-accounts create cdp-dashboard-run \
  --project prj-data-warehousing \
  --display-name "CDP Dashboard (Cloud Run)"

gcloud projects add-iam-policy-binding prj-data-warehousing \
  --member serviceAccount:cdp-dashboard-run@prj-data-warehousing.iam.gserviceaccount.com \
  --role roles/bigquery.jobUser

# Dataset-level read access (BigQuery console → ds_cdp → Sharing → add the SA
# as BigQuery Data Viewer), or via bq:
# bq add-iam-policy-binding --member=serviceAccount:cdp-dashboard-run@prj-data-warehousing.iam.gserviceaccount.com \
#   --role=roles/bigquery.dataViewer prj-data-warehousing:ds_cdp

# Build
gcloud builds submit --tag europe-west4-docker.pkg.dev/prj-data-warehousing/cdp-dashboard/app

# Deploy
gcloud run deploy cdp-dashboard \
  --image europe-west4-docker.pkg.dev/prj-data-warehousing/cdp-dashboard/app \
  --region europe-west4 \
  --no-allow-unauthenticated \
  --service-account cdp-dashboard-run@prj-data-warehousing.iam.gserviceaccount.com \
  --session-affinity \
  --timeout 3600
```

Notes:

- `--session-affinity` and a long `--timeout` keep Streamlit's websocket
  sessions stable behind Cloud Run's load balancer.
- `--no-allow-unauthenticated` blocks anonymous access. Since browsers can't
  send Google identity tokens themselves, enable **Identity-Aware Proxy (IAP)**
  on the service — users then log in with their @brightpensioen.nl account.

### Access control (IAP)

```bash
# One-time: create the IAP service agent and let it invoke the service
gcloud beta services identity create --service=iap.googleapis.com \
  --project=prj-data-warehousing

gcloud run services add-iam-policy-binding cdp-dashboard \
  --region europe-west4 \
  --member='serviceAccount:service-PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com' \
  --role='roles/run.invoker'

# Enable IAP on the service
gcloud run services update cdp-dashboard --region europe-west4 --iap

# Grant access — per user, per Google group, or the whole Workspace domain
gcloud beta iap web add-iam-policy-binding \
  --resource-type=cloud-run \
  --service=cdp-dashboard \
  --region=europe-west4 \
  --member='group:cdp-dashboard-users@brightpensioen.nl' \
  --role='roles/iap.httpsResourceAccessor'
```

Anyone visiting the URL gets a Google sign-in page; only principals with
`roles/iap.httpsResourceAccessor` get through. Manage access by editing the
Google group membership — no redeploys needed.

### CI/CD (Cloud Build)

Pushes to `main` build and deploy automatically via `cloudbuild.yaml`.
One-time setup:

```bash
# Artifact Registry repo for the images
gcloud artifacts repositories create cdp-dashboard \
  --repository-format=docker \
  --location=europe-west4 \
  --project=prj-data-warehousing

# Build service account (used by the trigger) needs to deploy and act as the runtime SA
gcloud iam service-accounts create cdp-dashboard-build \
  --project prj-data-warehousing \
  --display-name "CDP Dashboard (Cloud Build)"

gcloud projects add-iam-policy-binding prj-data-warehousing \
  --member serviceAccount:cdp-dashboard-build@prj-data-warehousing.iam.gserviceaccount.com \
  --role roles/run.admin
gcloud projects add-iam-policy-binding prj-data-warehousing \
  --member serviceAccount:cdp-dashboard-build@prj-data-warehousing.iam.gserviceaccount.com \
  --role roles/artifactregistry.writer
gcloud projects add-iam-policy-binding prj-data-warehousing \
  --member serviceAccount:cdp-dashboard-build@prj-data-warehousing.iam.gserviceaccount.com \
  --role roles/logging.logWriter

gcloud iam service-accounts add-iam-policy-binding \
  cdp-dashboard-run@prj-data-warehousing.iam.gserviceaccount.com \
  --member serviceAccount:cdp-dashboard-build@prj-data-warehousing.iam.gserviceaccount.com \
  --role roles/iam.serviceAccountUser

# Connect the GitHub repo and create the trigger (Console: Cloud Build →
# Triggers → Connect repository), then:
gcloud builds triggers create github \
  --name=deploy-cdp-dashboard \
  --repo-name=CDP_Dashboard \
  --repo-owner=otis-bright \
  --branch-pattern='^main$' \
  --build-config=cloudbuild.yaml \
  --region=europe-west4 \
  --service-account=projects/prj-data-warehousing/serviceAccounts/cdp-dashboard-build@prj-data-warehousing.iam.gserviceaccount.com
```

## IAM requirements

The service account running the app needs:

- `roles/bigquery.dataViewer` on `prj-data-warehousing.ds_cdp`
- `roles/bigquery.jobUser` on the project

## Caching

All BigQuery queries are cached with `@st.cache_data(ttl=300)` (5-minute refresh).
Adjust `ttl` in `utils/data_loader.py` to match your pipeline cadence.

## Project structure

```
cdp_dashboard/
├── app.py                          # Entry point, sidebar navigation
├── requirements.txt
├── Dockerfile                      # Cloud Run container
├── .streamlit/
│   └── config.toml                 # Dark theme + server config
├── pages/
│   ├── overview.py                 # Health KPIs, growth chart, funnel
│   ├── profiles.py                 # Profile table + detail cards
│   └── source_tracking.py          # Attribution by channel, WoW trends
├── components/
│   ├── ui.py                       # CSS injection, KPI row, badges
│   └── charts.py                   # Plotly chart factories
└── utils/
    └── data_loader.py              # BigQuery queries + caching
```
