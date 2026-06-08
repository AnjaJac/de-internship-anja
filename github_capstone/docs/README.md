# GitHub Events Data Pipeline
## Real-Time Data Pipeline on Databricks Free Edition

A production-style, serverless data pipeline built on Databricks Free Edition that ingests 
public GitHub event data incrementally, transforms it through the Medallion Architecture 
(Bronze → Silver → Gold), enforces data quality, and produces analytical datasets for 
business insights.

---
## Key Features

- Incremental GitHub event ingestion from the GitHub REST API
- Medallion Architecture implementation (Bronze → Silver → Gold)
- Auto Loader streaming ingestion with schema inference
- Delta Live Tables orchestration
- External repository and contributor enrichment workflows
- Cross-domain semantic analytical layer
- Data quality enforcement with DLT expectations
- Idempotent Silver-layer deduplication
- Workflow orchestration using Databricks Jobs
- Analytical validation and semantic quality checks

## Architecture Overview

```text
GitHub Events API
│
│  Incremental event ingestion
▼
/Volumes/workspace/gh_dev/raw/events/
│
│  Auto Loader
▼
st_brz_events (Bronze)
│
│  Deduplication + flattening
▼
tbl_slv_events (Silver)
│
├───────────────────────────────────────────────┐
│                                               │
│ Repository enrichment                         │ User enrichment
│ GitHub Repos API                              │ GitHub Users API
▼                                               ▼
/raw/repos/                                     /raw/users/
│                                               │
▼                                               ▼
st_brz_repos                                    st_brz_users
│                                               │
▼                                               ▼
tbl_slv_repos                                   tbl_slv_users
│                                               │
└───────────────────────────────────────────────┘
                        │
                        │ Cross-domain joins
                        ▼
                Enriched Gold Layer
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
mv_gld_repo_enriched    mv_gld_user_enriched
mv_gld_language_distribution
mv_gld_activity_summary
```

---

## Project Structure


```

/github_capstone/
├── notebooks/
│   ├── archive/
│   │   └── 01_volume_validation
│   ├── 00_Connectivity_Test       → Network validation; one-time run
│   ├── 01_Ingestion_Job           → GitHub Events API → Volume
│   ├── 05_Dashboard_Refresh       → Post-pipeline maintenance
│   ├── 08_Ingestion_Repos         → Repository enrichment ingestion
│   ├── 09_Ingestion_Users         → User enrichment ingestion
│   └── pipeline/
│       ├── 02_SDP_Bronze          → Auto Loader → st_brz_events
│       ├── 03_SDP_Silver          → st_brz_events → tbl_slv_events
│       └── 04_SDP_Gold            → tbl_slv_events → Gold views
│       ├── 11_SDP_Bronze_Users    → Auto Loader → st_brz_users
│       ├── 12_SDP_Bronze_Repos    → Auto Loader → st_brz_repos
│       ├── 13_SDP_Silver_Users    → User enrichment Silver layer
│       ├── 13_SDP_Silver_Repos    → Repository enrichment Silver layer
│       └── 14_SDP_Gold_Enriched   → Cross-domain semantic Gold views

├── sql/
│   ├── 08_Query_Repo_Velocity
│   ├── 09_Query_User_Stats
│   ├── 10_Query_Event_Distribution
│   ├── 11_Query_Event_Type_Breakdown
│   ├── 12_Query_Most_Active_Contributors
│   └── 13_Query_Pipeline_Health
│   ├── 14_Query_Repo_Enriched
│   ├── 15_Query_Language_Distribution
│   ├── 16_Query_User_Enriched
│   ├── 17_Query_Activity_Summary
└── tests/
├── 06_Test_Idempotency
└── 07_Test_Deduplication
└── 18_Validation_Check_Queries

```

---

## Environment Requirements

- Databricks Free Edition workspace
- Unity Catalog enabled (provisioned automatically)
- Serverless compute (only compute option in Free Edition)
- GitHub personal access token

---

## First-Time Setup

### Step 1 — Connectivity Test

Before anything else, confirm that Databricks Free Edition can reach the GitHub API.
Open `00_Connectivity_Test` and run it. You will see one of two outcomes:

- **200 OK** — API is reachable, proceed normally
- **Connection failed** — API is blocked. In this case, run `01_Ingestion_Job` locally 
  or in Google Colab and manually upload the resulting JSON files to the Volume via 
  Databricks UI: Data → Volumes → raw → Upload

### Step 2 — Initialise Storage

Run the following SQL in the Databricks SQL Editor once before the first pipeline run:

```sql
CREATE SCHEMA IF NOT EXISTS workspace.gh_dev;
CREATE VOLUME IF NOT EXISTS workspace.gh_dev.raw;
CREATE VOLUME IF NOT EXISTS workspace.gh_dev.checkpoints;
CREATE VOLUME IF NOT EXISTS workspace.gh_dev.schemas;

```

Verify all three Volumes are visible in Catalog → workspace → gh_dev.

### Step 3 — Configure GitHub Token

Store your GitHub personal access token in a Databricks secret scope using the
Databricks CLI:

```bash
databricks secrets create-scope --scope github_scope
databricks secrets put --scope github_scope --key api_token

```

Verify the secret exists by running this in any notebook:

```python
dbutils.secrets.get(scope="github_scope", key="api_token")
# Should return [REDACTED]

```

### Step 4 — Configure the SDP Pipeline

1. Go to Jobs & Pipelines in the left sidebar
2. Click Create → ETL Pipeline
3. Configure with these settings:

| Setting | Value |
| --- | --- |
| Pipeline name | sdp_gh_medallion |
| Pipeline mode | Triggered |
| Default catalog | workspace |
| Default schema | gh_dev |
| Compute | Serverless |
| Root folder | `/github_capstone/notebooks/pipeline/` |
| Source code paths | `02_SDP_Bronze`, `03_SDP_Silver`, `04_SDP_Gold`, `10_SDP_Bronze_Repos`, '11_SDP_Bronze_Users`, `12_SDP_Silver_Repos`, `13_SDP_Silver_Users`, `14_SDP_Gold_Enriched` |

### Step 5 — Configure the Job

1. Go to Jobs & Pipelines → Create → Job
2. Name the job: `gh_pipeline_job`
3. Add tasks in this order:

| Task              | Type     | Source                 | Depends On   |
| ----------------- | -------- | ---------------------- | ------------ |
| Ingest_API        | Notebook | `01_Ingestion_Job`     | None         |
| Ingest_Repos      | Notebook | `08_Ingestion_Repos`   | Ingest_API   |
| Ingest_Users      | Notebook | `09_Ingestion_Users`   | Ingest_Repos |
| Process_SDP       | Pipeline | `sdp_gh_medallion`     | Ingest_Users |
| Dashboard_Refresh | Notebook | `05_Dashboard_Refresh` | Process_SDP  |


4. Set Maximum concurrent runs to 1
5. Schedule to run once daily (optional)
The orchestration workflow implements a sequential dependency chain ensuring:
- event ingestion completes before enrichment begins
- repository enrichment completes before user enrichment
- all raw enrichment snapshots land before SDP processing
- the Medallion pipeline executes only after all raw layers are updated

This guarantees deterministic enrichment joins and stable Silver-layer deduplication.
---

## Running the Pipeline

### Manual Run

1. Go to Jobs & Pipelines
2. Find `gh_pipeline_job`
3. Click Run Now
4. Monitor progress in the Runs tab

### What Happens Each Run

1. `01_Ingestion_Job` fetches up to 100 new GitHub events and writes a JSON file to the Volume
2. `sdp_gh_medallion` pipeline runs:
* Bronze picks up the new file via Auto Loader
* Silver reads all Bronze data, deduplicates, and produces a clean flat table
* Gold materialized views recompute from Silver


3. `05_Dashboard_Refresh` runs post-pipeline maintenance

---

## Data Quality

The pipeline enforces two automatic data quality rules at the Silver layer:

| Rule | Field | Behaviour |
| --- | --- | --- |
| `event_id IS NOT NULL` | `event_id` | Halts the entire pipeline |
| `event_type IS NOT NULL` | `event_type` | Silently drops the row |

Expectation pass/fail metrics are visible in the pipeline UI under the Pipeline graph tab.

---
## Idempotency & Data Quality Guarantees

The platform is designed for stable repeated execution.

### Raw & Bronze Behaviour

Raw ingestion layers are append-only:
- repeated runs create new snapshot files
- historical raw payloads are preserved
- Bronze tables incrementally ingest all raw snapshots

### Silver-Layer Deduplication

Silver tables enforce logical idempotency using deterministic business keys:
- `event_id` for events
- `repo_name` for repositories
- `actor_login` for users

ROW_NUMBER window deduplication guarantees:
- no duplicate Silver entities
- stable semantic joins
- repeatable Gold-layer analytics

### Validation Suite

The validation suite verifies:
- table materialization
- semantic join completeness
- deduplication correctness
- enrichment coverage
- stable row counts across repeated runs

## Validation & Testing

### Idempotency Test — `06_Test_Idempotency`

```sql
SELECT COUNT(*) as silver_count
FROM workspace.gh_dev.tbl_slv_events;

```

Run before and after a duplicate file upload. Count should only increase by
genuinely new unique events.

### Deduplication Test — `07_Test_Deduplication`

```sql
-- Should return 0 rows
SELECT event_id, COUNT(*) as count
FROM workspace.gh_dev.tbl_slv_events
GROUP BY event_id
HAVING COUNT(*) > 1;

-- unique_events and total_rows should be equal
SELECT COUNT(DISTINCT event_id) as unique_events,
COUNT(*) as total_rows
FROM workspace.gh_dev.tbl_slv_events;

```

---

## Gold Layer Queries

All queries are saved in `/sql/` and can be run from the Databricks SQL Editor.

| Query | Description |
| --- | --- |
| 08_Query_Repo_Velocity | Top 10 most active repositories |
| 09_Query_User_Stats | Top 10 repositories by unique contributors |
| 10_Query_Event_Distribution | GitHub activity by hour of day |
| 11_Query_Event_Type_Breakdown | Distribution of event types |
| 12_Query_Most_Active_Contributors | Top 10 most active contributors |
| 13_Query_Pipeline_Health | Daily ingestion volume and coverage |

---

## Constraints & Known Limitations

* **GitHub API rate limit** — 5,000 authenticated requests per hour. If hit, the
ingestion notebook exits with `RATE_LIMITED` and the pipeline is skipped for that run.
* **Databricks compute quota** — Free Edition has a daily compute limit. If reached,
compute resumes the next day with no data loss.
* **Silver deduplication scope** — Deduplication uses a full batch read of all Bronze
data. This correctly handles duplicates across all runs but means Silver recomputes
fully on each pipeline execution.
* **OPTIMIZE not currently applied** — Silver is a materialized view and does not
support `OPTIMIZE`. This will be revisited when the Silver layer is refactored to a
streaming table.

---

## Pipeline Lineage

Full lineage is visible in the Databricks UI under the Pipeline graph tab of
`sdp_gh_medallion`. Every row in Gold can be traced back to Bronze via the
`source_file` and `_ingested_at` metadata columns preserved through the pipeline.

```

```
## Enrichment Architecture

The platform extends beyond raw GitHub event ingestion by incrementally enriching
events with external repository and contributor metadata from the GitHub REST API.

### Repository Enrichment

The repository enrichment workflow:
1. Extracts distinct `repo_name` values from `tbl_slv_events`
2. Calls the GitHub `/repos/{owner}/{repo}` endpoint
3. Stores raw repository snapshots in `/raw/repos/`
4. Processes snapshots through Bronze → Silver Medallion layers

Repository enrichment captures:
- primary language
- stars
- forks
- open issues
- repository creation timestamp

### User Enrichment

The user enrichment workflow:
1. Extracts distinct `actor_login` values from `tbl_slv_events`
2. Calls the GitHub `/users/{username}` endpoint
3. Stores raw user-profile snapshots in `/raw/users/`
4. Processes snapshots through Bronze → Silver Medallion layers

User enrichment captures:
- followers
- public repositories
- company
- geographic location
- account creation timestamp

### Enriched Semantic Gold Layer

The enriched Gold layer joins:
- GitHub events
- repository metadata
- contributor metadata

into unified analytical materialized views supporting:
- ecosystem analytics
- contributor influence analysis
- repository popularity analysis
- organizational participation analysis
- temporal activity analysis
## Platform Summary

Final validated platform metrics:

| Metric | Value |
| --- | --- |
| Total enriched events | 1229 |
| Unique repositories | 698 |
| Unique contributors | 601 |
| Unique languages | 39 |
| Avg repository stars | 613.68 |
| Avg contributor followers | 109.39 |

The completed platform demonstrates:
- incremental ingestion
- Medallion Architecture
- Auto Loader streaming ingestion
- Delta Live Tables orchestration
- external API enrichment
- semantic analytical modeling
- workflow orchestration
- data quality enforcement
- idempotent Silver-layer processing
- cross-domain business analytics
## Technologies Used

| Technology | Purpose |
| --- | --- |
| Databricks Free Edition | Cloud data platform |
| Delta Live Tables (DLT) | Declarative Medallion pipelines |
| Auto Loader | Incremental file ingestion |
| Unity Catalog | Governance and storage |
| PySpark | Distributed transformations |
| Delta Lake | Storage layer |
| GitHub REST API | Source and enrichment data |
| Databricks Workflows | Orchestration |
| SQL | Analytical and validation queries |

## CI/CD Implementation

This project includes a Continuous Integration (CI) pipeline implemented with GitHub Actions.

### CI Workflow

The workflow is defined in:

```plaintext
.github/workflows/databricks-ci.yml
```

The pipeline is triggered on:

* Pushes to feature branches
* Pull requests targeting `main`
* Manual execution through `workflow_dispatch`

The CI pipeline performs the following steps:

1. Checkout repository source code
2. Configure Python 3.11 environment
3. Install project dependencies
4. Install Databricks CLI
5. Validate the Databricks Asset Bundle
6. Execute automated tests

### Automated Tests

The project contains automated validation tests covering:

* Databricks bundle configuration
* Job and pipeline resource definitions
* Notebook path validation
* Bundle resource references

Current test coverage includes:

```plaintext
tests/test_bundle_config.py
tests/test_bundle_references.py
tests/test_notebook_paths.py
tests/test_pipeline_structure.py
```

Total automated tests:

```plaintext
11
```

### Deployment Strategy

Bundle deployment is performed manually from the local development environment using OAuth authentication:

```bash
databricks bundle deploy --target dev
```

Deployment through GitHub Actions was investigated but is not supported in the Databricks Free Edition environment due to account-level authentication limitations. Additional details are documented in `docs/decisions/0001-free-edition-cicd-limitations.md`.
