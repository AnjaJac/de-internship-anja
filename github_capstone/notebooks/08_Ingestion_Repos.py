# Databricks notebook source
# MAGIC %md
# MAGIC # Repository Metadata Ingestion
# MAGIC
# MAGIC ## Purpose
# MAGIC This notebook enriches the Medallion Architecture pipeline by retrieving
# MAGIC repository-level metadata from the GitHub REST API for repositories
# MAGIC referenced in the Silver events layer.
# MAGIC
# MAGIC ## Data Flow
# MAGIC Silver Events Table
# MAGIC → Distinct repo_name extraction
# MAGIC → GitHub Repository API requests
# MAGIC → Raw repository metadata JSON
# MAGIC → Unity Catalog Volume storage
# MAGIC
# MAGIC ## Compatibility
# MAGIC - Databricks Free Edition
# MAGIC - Unity Catalog Volumes
# MAGIC - Serverless Compute
# MAGIC - Standalone Databricks Job task

# COMMAND ----------

import json
import uuid
from datetime import datetime
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# COMMAND ----------

# Configuration constants

RAW_REPOS_PATH = "/Volumes/workspace/gh_dev/raw/repos/"
API_BASE_URL = "https://api.github.com/repos"
SOURCE_TABLE = "workspace.gh_dev.tbl_slv_events"
REQUEST_TIMEOUT_SECONDS = 15
THROTTLE_SECONDS = 0.4

# COMMAND ----------

# Retrieve GitHub API token securely from Databricks Secret Scope

token = dbutils.secrets.get(
    scope="github_scope",
    key="api_token"
)

# Configure GitHub API authentication headers

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

# COMMAND ----------

# Create reusable HTTP session

session = requests.Session()
session.headers.update(headers)

# Configure retry behavior for transient 5xx server failures

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"]
)

# Attach retry-enabled adapters to session

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)


# COMMAND ----------

exit_code = "FAILED"

try:

    # Read distinct repositories from Silver events table

    repo_df = spark.sql(f"""
        SELECT DISTINCT repo_name
        FROM {SOURCE_TABLE}
        WHERE repo_name IS NOT NULL
    """)

    repo_rows = repo_df.collect()

    print(f"Found {len(repo_rows)} repositories to process")

    # Generate unique batch identifier

    batch_id = (
        datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        + "_"
        + uuid.uuid4().hex[:8]
    )

    # Create logical batch directory path

    batch_output_dir = (
        f"{RAW_REPOS_PATH}"
        f"{batch_id}/"
    )

    # Track successfully written repository count

    processed_repos = 0
    skipped_repos = 0
    failed_repos = 0

    # Process repositories individually

    for row in repo_rows:

        repo_name = row["repo_name"]

        # Validate owner/repo format

        parts = repo_name.split("/", 1)

        if len(parts) != 2 or not parts[0] or not parts[1]:

            print(f"Skipping invalid repo_name: {repo_name}")
            skipped_repos += 1

            continue

        owner, repo = parts

        # Sanitize repository filename components

        safe_owner = owner.replace("/", "_").strip()
        safe_repo = repo.replace("/", "_").strip()

        # Construct GitHub repository endpoint

        repo_url = f"{API_BASE_URL}/{owner}/{repo}"

        print(f"Processing repository: {repo_name}")

        try:

            # Execute GitHub API request

            response = session.get(
                repo_url,
                timeout=REQUEST_TIMEOUT_SECONDS
            )

            # Handle GitHub rate limits explicitly

            if response.status_code == 403:

                print(
                    f"GitHub API rate limit reached "
                    f"while processing {repo_name}"
                )

                exit_code = "RATE_LIMITED"
                break

            # Raise exception for failed responses

            response.raise_for_status()

            # Parse repository metadata JSON

            repo_payload = response.json()

            # Define output path for repository payload

            output_path = (
                f"{batch_output_dir}"
                f"{safe_owner}__{safe_repo}.json"
            )

            # Persist repository metadata immediately

            dbutils.fs.put(
                output_path,
                json.dumps(repo_payload),
                overwrite=False
            )

            processed_repos += 1

        except requests.exceptions.HTTPError as http_error:

            print(
                f"HTTP error for repository "
                f"{repo_name}: {http_error}"
            )
            failed_repos += 1
            continue
        except requests.exceptions.RetryError as retry_error:
            print(
                f"Transient retry error for repository "
                f"{repo_name}: {retry_error}"
            )
            failed_repos += 1
            continue

        except Exception as repo_error:
            print(
                f"Unexpected repository-level failure "
                f"{repo_name}: {repo_error}"
            )
            failed_repos += 1
            continue

        finally:
            time.sleep(THROTTLE_SECONDS)

    # Print operational run summary for observability

    print(f"Batch path: {batch_output_dir}")
    print(f"Repositories processed: {processed_repos}")
    print(f"Repositories skipped: {skipped_repos}")
    print(f"Repositories failed: {failed_repos}")

    # Mark successful completion when run was not interrupted by rate limits
    if exit_code != "RATE_LIMITED":
        print("Repository enrichment ingestion completed")

        exit_code = "SUCCESS"

    else:
        print("Repository enrichment ingestion stopped due to rate limiting") 

except requests.exceptions.RetryError as retry_error:

    print(
    f"Ingestion framework transient retry failure occurred: "
    f"{retry_error}"
)

    exit_code = "TRANSIENT_ERROR"

except Exception as e:

    print(f"Fatal ingestion failure: {e}")

    exit_code = "FAILED"

# Controlled notebook termination

dbutils.notebook.exit(exit_code)

# COMMAND ----------

# MAGIC %md
# MAGIC # Operational Notes
# MAGIC
# MAGIC ## Why repo_name is split on "/"
# MAGIC GitHub repository API endpoints require:
# MAGIC
# MAGIC https://api.github.com/repos/{owner}/{repo}
# MAGIC
# MAGIC The Silver events table stores repositories in canonical GitHub format:
# MAGIC
# MAGIC owner/repo
# MAGIC
# MAGIC Therefore the notebook splits repo_name into:
# MAGIC - owner
# MAGIC - repository name
# MAGIC
# MAGIC before constructing the API request path.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Rate Limit Risk
# MAGIC This notebook performs one API request per repository.
# MAGIC
# MAGIC As repository counts increase:
# MAGIC - request volume grows
# MAGIC - GitHub API rate limits become more likely
# MAGIC
# MAGIC Future optimizations may include:
# MAGIC - incremental enrichment
# MAGIC - repository caching
# MAGIC - GraphQL batching
# MAGIC - enrichment deduplication
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Why overwrite=False is used
# MAGIC overwrite=False enforces append-only ingestion behavior.
# MAGIC
# MAGIC Benefits:
# MAGIC - prevents accidental overwrites
# MAGIC - preserves historical ingestion batches
# MAGIC - supports immutable raw-zone architecture
# MAGIC - enables ingestion traceability
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Exit Codes
# MAGIC
# MAGIC | Exit Code | Meaning |
# MAGIC |---|---|
# MAGIC | SUCCESS | Repository ingestion completed successfully |
# MAGIC | RATE_LIMITED | GitHub API rate limit encountered |
# MAGIC | TRANSIENT_ERROR | Retry attempts exhausted |
# MAGIC | FAILED | Fatal notebook-level failure |