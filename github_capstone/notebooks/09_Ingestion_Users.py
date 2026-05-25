# Databricks notebook source
# MAGIC %md
# MAGIC # User Metadata Ingestion
# MAGIC
# MAGIC ## Purpose
# MAGIC This notebook enriches the GitHub lakehouse by retrieving user-profile
# MAGIC metadata for contributors observed in the Silver events layer.
# MAGIC
# MAGIC The ingestion captures current-state user snapshots (mutable entity data),
# MAGIC not immutable event streams.
# MAGIC
# MAGIC ## Data Flow
# MAGIC Silver Events Table
# MAGIC → Distinct actor_login extraction
# MAGIC → GitHub Users API requests
# MAGIC → Raw user profile JSON snapshots
# MAGIC → Unity Catalog Volume storage
# MAGIC
# MAGIC ## Compatibility
# MAGIC - Databricks Free Edition
# MAGIC - Unity Catalog Volumes
# MAGIC - Serverless Compute
# MAGIC - Standalone Databricks Job task

# COMMAND ----------

import json
import re
import time
import uuid
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# COMMAND ----------

# Configuration constants

RAW_USERS_PATH = "/Volumes/workspace/gh_dev/raw/users/"
API_BASE_URL = "https://api.github.com/users"
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

# Configure retry behavior for transient 5xx server failures only

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

    # Read distinct contributor usernames from Silver events table

    user_df = spark.sql(f"""
        SELECT DISTINCT actor_login
        FROM {SOURCE_TABLE}
        WHERE actor_login IS NOT NULL
    """)

    user_rows = user_df.collect()

    print(f"Found {len(user_rows)} users to process")

    # Generate unique batch identifier

    batch_id = (
        datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        + "_"
        + uuid.uuid4().hex[:8]
    )

    # Create logical batch directory path

    batch_output_dir = (
        f"{RAW_USERS_PATH}"
        f"{batch_id}/"
    )



    # Track ingestion outcomes for operational logging

    processed_users = 0
    skipped_users = 0
    failed_users = 0

    # Process users individually for append-only entity enrichment

    for row in user_rows:

        username = str(row["actor_login"]).strip()

        # Validate malformed or unsupported usernames

        if not username:

            print("Skipping malformed username: <empty>")

            skipped_users += 1
            continue

        if not re.match(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$", username):

            print(f"Skipping malformed username: {username}")

            skipped_users += 1
            continue

        # Sanitize username for safe output file naming

        safe_username = username.replace("/", "_").strip()

        # Construct GitHub user-profile endpoint

        user_url = f"{API_BASE_URL}/{username}"

        print(f"Processing user: {username}")

        try:

            # Execute GitHub API request for user profile metadata

            response = session.get(
                user_url,
                timeout=REQUEST_TIMEOUT_SECONDS
            )

            # Handle GitHub rate limits explicitly

            if response.status_code == 403:

                print(
                    f"GitHub API rate limit reached "
                    f"while processing {username}"
                )

                exit_code = "RATE_LIMITED"
                break

            # Raise exception for failed responses

            response.raise_for_status()

            # Parse user-profile metadata JSON snapshot

            user_payload = response.json()

            # Define output path for user snapshot payload

            output_path = (
                f"{batch_output_dir}"
                f"{safe_username}.json"
            )

            # Persist user metadata immediately into raw storage

            dbutils.fs.put(
                output_path,
                json.dumps(user_payload),
                overwrite=False
            )

            processed_users += 1

        except requests.exceptions.HTTPError as http_error:

            print(
                f"HTTP error for user "
                f"{username}: {http_error}"
            )

            failed_users += 1
            continue

        except requests.exceptions.RetryError as retry_error:

            print(
                f"Transient retry failure for user "
                f"{username}: {retry_error}"
            )

            failed_users += 1
            continue


        except Exception as user_error:

            print(
                f"Unexpected user-level failure "
                f"for {username}: {user_error}"
            )

            failed_users += 1
            continue

        finally:

            # Apply lightweight throttling to reduce API burst pressure

            time.sleep(THROTTLE_SECONDS)

    # Print operational run summary for observability

    print(f"Batch path: {batch_output_dir}")
    print(f"Users processed: {processed_users}")
    print(f"Users skipped: {skipped_users}")
    print(f"Users failed: {failed_users}")

    # Mark successful completion when run was not interrupted by rate limits

    if exit_code != "RATE_LIMITED":

        print("User enrichment ingestion completed")

        exit_code = "SUCCESS"
    else:
        print("User enrichment ingestion stopped due to rate limiting")

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
# MAGIC # Notes
# MAGIC
# MAGIC ## Processing Logic
# MAGIC - Distinct `actor_login` values are read from Silver events and treated as
# MAGIC   contributor identities that require external enrichment.
# MAGIC - Each username triggers a direct GitHub API call to
# MAGIC   `https://api.github.com/users/{username}`.
# MAGIC - Responses are written immediately as independent JSON files to preserve
# MAGIC   append-only raw ingestion behavior.
# MAGIC
# MAGIC ## Operational Considerations
# MAGIC - User profiles are mutable entities, so raw files represent point-in-time
# MAGIC   snapshots for downstream Bronze/Silver harmonization.
# MAGIC - A unique `batch_id` creates nested batch folders for traceable ingestion
# MAGIC   boundaries and replay-friendly lineage.
# MAGIC - `overwrite=False` protects historical snapshots from accidental mutation.
# MAGIC - Lightweight `time.sleep()` throttling reduces burst pressure and lowers
# MAGIC   the chance of early GitHub API rate-limit exhaustion.
# MAGIC - User-level request failures are isolated so processing continues for
# MAGIC   remaining users in the same run.
# MAGIC
# MAGIC ## Exit Codes
# MAGIC - `SUCCESS`: notebook completed user ingestion and wrote raw snapshots.
# MAGIC - `RATE_LIMITED`: GitHub returned HTTP 403 and processing was stopped.
# MAGIC - `TRANSIENT_ERROR`: retry logic exhausted for a transient failure path.
# MAGIC - `FAILED`: fatal notebook-level failure outside handled transient cases.