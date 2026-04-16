# CDP Intelligence Dashboard

A Streamlit application for monitoring and exploring your Customer Data Platform.

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

**Option A — Service account key (recommended for local dev):**

```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Fill in your service account credentials in secrets.toml
```

**Option B — Application Default Credentials:**

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

```bash
# Build
gcloud builds submit --tag gcr.io/prj-data-warehousing/cdp-dashboard

# Deploy
gcloud run deploy cdp-dashboard \
  --image gcr.io/prj-data-warehousing/cdp-dashboard \
  --region europe-west4 \
  --no-allow-unauthenticated \
  --service-account your-sa@prj-data-warehousing.iam.gserviceaccount.com
```

Use `--no-allow-unauthenticated` and restrict access to your internal users via IAM (`roles/run.invoker`).

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
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
├── .streamlit/
│   ├── config.toml                 # Dark theme + server config
│   └── secrets.toml.template       # Copy → secrets.toml, fill in SA key
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
