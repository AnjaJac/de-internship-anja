# Databricks notebook source
import requests
import json
import uuid
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Retrieve GitHub token securely from Databricks Secret Scope
token = dbutils.secrets.get(
    scope="github_scope",
    key="api_token"
)

# Configure API authentication headers
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}
# Create reusable HTTP session
session = requests.Session()
session.headers.update(headers)
# Configure retry logic for transient 5xx errors
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
# Generate unique batch identifier
batch_id = (
    f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_"
    f"{uuid.uuid4().hex[:8]}"
)
# Define raw output path
output_path = (
    f"/Volumes/workspace/gh_dev/raw/"
    f"events_{batch_id}.json"
) 

try:
    # Request GitHub Events API data
    response = session.get(
        "https://api.github.com/events",
        params={"per_page": 100},
        timeout=15
    )
    # Handle GitHub rate limiting
    if response.status_code == 403:
        print(f"Rate limited = skipping batch {batch_id}")
        dbutils.notebook.exit("RATE_LIMITED")
    # Raise exception for failed HTTP responses 
    response.raise_for_status()
    # Parse JSON payload
    events = response.json()
    #Write raw JSON file into Unity Catalog Volume
    dbutils.fs.put(
        output_path,
        json.dumps(events),
        overwrite=False
    )
    print(f"Written {len(events)} events to {output_path}")
    dbutils.notebook.exit("SUCCESS")
except requests.exceptions.RetryError as e:
    print(f"Transient error after retries: {e}")
    dbutils.notebook.exit("TRANSIENT_ERROR")
except Exception as e:
    print(f"Unexpected error: {e}")
    dbutils.notebook.exit("FAILED")

