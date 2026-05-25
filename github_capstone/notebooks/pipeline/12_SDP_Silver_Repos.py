# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer: Repository Metadata Cleaning & Deduplication
# MAGIC
# MAGIC ## Purpose
# MAGIC Clean and deduplicate GitHub Repository metadata from the bronze layer, extracting
# MAGIC key fields into a flat schema and ensuring data quality through deduplication.
# MAGIC
# MAGIC ## Data Flow
# MAGIC - **Source**: `st_brz_repos` (bronze Delta table)
# MAGIC - **Sink**: `tbl_slv_repos` (silver materialized view)
# MAGIC - **Processing**: Field extraction, type casting, deduplication
# MAGIC - **Quality**: No duplicate repo_name records, flat schema
# MAGIC
# MAGIC ## Schema
# MAGIC | Column | Type | Source Field |
# MAGIC |--------|------|--------------|
# MAGIC | repo_name | STRING | full_name |
# MAGIC | stars | INT | stargazers_count |
# MAGIC | forks | INT | forks_count |
# MAGIC | primary_language | STRING | language |
# MAGIC | open_issues | INT | open_issues_count |
# MAGIC | repo_created_at | TIMESTAMP | created_at (cast via to_timestamp()) |
# MAGIC | _ingested_at | TIMESTAMP | _ingested_at (ingestion timestamp) |
# MAGIC
# MAGIC ## Compatibility
# MAGIC - Databricks Free Edition
# MAGIC - Unity Catalog
# MAGIC - Serverless compute
# MAGIC - SDP/DLT declarative pipeline framework

# COMMAND ----------

import dlt
from pyspark.sql.functions import (
    col, to_timestamp, row_number, to_date
)
from pyspark.sql.window import Window

# COMMAND ----------

@dlt.expect_or_fail("repo_name not null", "repo_name IS NOT NULL")
@dlt.expect_or_drop("stars not null", "stars IS NOT NULL")
@dlt.materialized_view(
    name="tbl_slv_repos",
    comment="Silver layer: Cleaned and deduplicated GitHub Repository metadata",
    partition_cols=["ingestion_date"],
    table_properties={
        "quality": "silver"
    }
)
def tbl_slv_repos():
    """
    Clean and deduplicate GitHub Repository metadata from bronze layer.

    Processing Steps:
    1. Extract specific fields from raw_payload struct
    2. Cast numeric fields to INT, timestamps to TIMESTAMP
    3. Apply window function to deduplicate by repo_name (latest ingestion)
    4. Filter for row_number == 1 to keep only latest record per repo_name
    5. Add ingestion_date partition column derived from _ingested_at

    Returns:
        DataFrame with flat schema and no duplicate repo_name records
    """

    # Define window specification for deduplication
    # Partition by repo_name, order by ingestion timestamp descending (latest first)
    # NOTE: Order by _ingested_at (ingestion time) not repo_created_at, since
    # repositories don't have a meaningful event timestamp; we deduplicate by freshness of ingestion
    dedup_window = Window.partitionBy("repo_name").orderBy(col("_ingested_at").desc())

    return (
        dlt.read("st_brz_repos")
        .select(
            col("raw_payload.full_name").alias("repo_name"),
            col("raw_payload.stargazers_count").cast("int").alias("stars"),
            col("raw_payload.forks_count").cast("int").alias("forks"),
            col("raw_payload.language").alias("primary_language"),
            col("raw_payload.open_issues_count").cast("int").alias("open_issues"),
            to_timestamp(col("raw_payload.created_at")).alias("repo_created_at"),
            col("_ingested_at")
        )
        .withColumn(
            "ingestion_date",
            to_date(col("_ingested_at"))
        )
        .withColumn(
            "row_num",
            row_number().over(dedup_window)
        )
        .filter(col("row_num") == 1)
        .drop("row_num", "_ingested_at")  # Remove temporary columns
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC **Why dlt.read() instead of dlt.read_stream():**
# MAGIC - Repository metadata is not an event stream; it's a snapshot dataset
# MAGIC - ROW_NUMBER() window function is unsupported on streaming DataFrames
# MAGIC - Using @dlt.materialized_view with batch reads is the correct pattern for non-streaming sources
# MAGIC
# MAGIC **Deduplication Logic:**
# MAGIC - Uses window function partitioned by `repo_name` (unique identifier)
# MAGIC - Orders by `_ingested_at` descending (latest ingestion first)
# MAGIC - NOTE: Orders by ingestion timestamp, NOT `repo_created_at`, because
# MAGIC   repositories have no event timestamp; we deduplicate by ingestion freshness
# MAGIC - Assigns row numbers within each partition
# MAGIC - Filters for `row_num == 1` to keep only the latest version
# MAGIC
# MAGIC **Data Quality Expectations:**
# MAGIC - `@dlt.expect_or_fail("repo_name not null")`: Ensures every repo has a name (critical)
# MAGIC - `@dlt.expect_or_drop("stars not null")`: Drops rows with missing star counts (recoverable quality issue)
# MAGIC - These run before the materialized view is created, preventing invalid data downstream
# MAGIC
# MAGIC **Field Extraction:**
# MAGIC - Accesses nested fields using dot notation: `raw_payload.field`
# MAGIC - `stargazers_count`, `forks_count`, `open_issues_count` cast to INT
# MAGIC - `repo_created_at` cast to TIMESTAMP using `to_timestamp()`
# MAGIC - `ingestion_date` derived as DATE type for efficient partitioning
# MAGIC - All fields flattened to top-level columns
# MAGIC
# MAGIC **Partition Strategy:**
# MAGIC - Partitioned by `ingestion_date` to align with how the Gold layer queries repos
# MAGIC - Enables efficient filtering by ingestion recency
# MAGIC
# MAGIC **Connection to Gold Layer:**
# MAGIC - This materialized view provides clean, deduplicated repo context for enrichment
# MAGIC - Gold layer joins this with Events to track repo metrics over time
# MAGIC - Deduplication ensures no double-counting of fork/star metrics in aggregations