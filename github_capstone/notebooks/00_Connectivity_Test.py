# Databricks notebook source
# MAGIC %md
# MAGIC # Connectivity & Network Validation
# MAGIC
# MAGIC ## Purpose
# MAGIC Validate outbound connectivity from Databricks Free Edition serverless compute to the GitHub Events API.
# MAGIC
# MAGIC ## Validation Goals
# MAGIC - Verify external API access
# MAGIC - Verify GitHub authentication
# MAGIC - Verify Databricks Secret Scope access
# MAGIC - Confirm serverless runtime outbound connectivity

# COMMAND ----------

import requests

token = dbutils.secrets.get(
    scope="github_scope",
    key="api_token"
)
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}"
}
try:
    response = requests.get(
        "https://api.github.com/events",
        headers=headers,
        timeout=10
    )
    print("Status code:", response.status_code)
    print("Response preview:")
    print(response.text[:500])
except Exception as e:
    print(f"Connection failed - use manual upload path. Error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Extended Endpoint Validation
# MAGIC
# MAGIC ## Validate all GitHub API endpoints used later in the pipeline:
# MAGIC  - Events API
# MAGIC  - Repository Metadata API
# MAGIC  - User Profile API
# MAGIC
# MAGIC ## This ensures:
# MAGIC  - endpoint accessibility
# MAGIC  - authentication validity
# MAGIC  - schema availability
# MAGIC  - future enrichment pipeline readiness
# MAGIC
# MAGIC

# COMMAND ----------

test_endpoints = {
    "events": "https://api.github.com/events",
    "repo_metadata": "https://api.github.com/repos/apache/spark",
    "user_profile": "https://api.github.com/users/torvalds"
}
for name, url in test_endpoints.items():
    print("=" *60)
    print(f"Testing endpoint: {name}")
    print(f"URL: {url}")

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Connection successfull")
            json_preview = response.text[:500]
            print("Response preview:")
            print(json_preview)
        elif response.status_code == 403:
            print("Rate limit reached or access forbidden")
        else:
            print(f"Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"Connection failed - use manual upload path. Error: {e}")
    print("=" * 60)