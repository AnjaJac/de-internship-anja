# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer: User Metadata Cleaning & Deduplication
# MAGIC
# MAGIC ## Purpose
# MAGIC Clean and deduplicate GitHub User profile metadata from the bronze layer,
# MAGIC extracting key fields into a flat canonical schema and enforcing quality
# MAGIC constraints for downstream analytics.
# MAGIC
# MAGIC ## Data Flow
# MAGIC - **Source**: `st_brz_users` (bronze Delta table)
# MAGIC - **Sink**: `tbl_slv_users` (silver materialized view)
# MAGIC - **Processing**: Field extraction, type casting, Type 1-style deduplication
# MAGIC - **Quality**: No null actor_login records, one latest record per user
# MAGIC
# MAGIC ## Schema
# MAGIC | Column | Type | Source Field |
# MAGIC |--------|------|--------------|
# MAGIC | actor_login | STRING | login |
# MAGIC | company | STRING | company |
# MAGIC | location | STRING | location |
# MAGIC | followers | INT | followers |
# MAGIC | public_repos | INT | public_repos |
# MAGIC | user_created_at | TIMESTAMP | created_at (cast via to_timestamp()) |
# MAGIC | ingestion_date | DATE | derived from _ingested_at |
# MAGIC
# MAGIC ## Compatibility
# MAGIC - Databricks Free Edition
# MAGIC - Unity Catalog
# MAGIC - Serverless compute
# MAGIC - SDP/DLT declarative pipeline framework

# COMMAND ----------

import dlt
from pyspark.sql.functions import col, row_number, to_date, to_timestamp
from pyspark.sql.window import Window

# COMMAND ----------

@dlt.expect_or_fail("actor_login not null", "actor_login IS NOT NULL")
@dlt.materialized_view(
    name="tbl_slv_users",
    comment="Silver layer: Cleaned and deduplicated GitHub User profile metadata",
    partition_cols=["ingestion_date"],
    table_properties={
        "quality": "silver"
    }
)
def tbl_slv_users():
    """
    Clean and deduplicate GitHub User profile metadata from bronze layer.

    Processing Steps:
    1. Extract user entity fields from raw_payload struct
    2. Cast numeric fields to INT and created_at to TIMESTAMP
    3. Derive ingestion_date from _ingested_at
    4. Apply window function to deduplicate by actor_login (latest ingestion)
    5. Filter for row_number == 1 to keep only latest canonical user state

    Returns:
        DataFrame with flat schema and one latest record per actor_login.
    """

    # Deduplicate mutable user entities by latest ingestion timestamp.
    # IMPORTANT: Order by _ingested_at, not user_created_at.
    # user_created_at is account creation time; _ingested_at is enrichment freshness.
    dedup_window = Window.partitionBy("actor_login").orderBy(col("_ingested_at").desc())

    return (
        dlt.read("st_brz_users")
        .select(
            col("raw_payload.login").alias("actor_login"),
            col("raw_payload.company").alias("company"),
            col("raw_payload.location").alias("location"),
            col("raw_payload.followers").cast("int").alias("followers"),
            col("raw_payload.public_repos").cast("int").alias("public_repos"),
            to_timestamp(col("raw_payload.created_at")).alias("user_created_at"),
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
        .drop("row_num", "_ingested_at")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC **Deduplication Logic:**
# MAGIC - Uses `ROW_NUMBER()` partitioned by `actor_login`
# MAGIC - Orders by `_ingested_at` descending (latest ingestion first)
# MAGIC - Keeps only `row_num == 1` as the canonical current-state user record
# MAGIC - This implements Type 1 SCD-style behavior for mutable entities
# MAGIC
# MAGIC **Data Quality Expectations:**
# MAGIC - `@dlt.expect_or_fail("actor_login not null")` enforces presence of the canonical user key
# MAGIC - A missing `actor_login` is a hard quality failure because deduplication and joins depend on it
# MAGIC
# MAGIC **Why `dlt.read()` Instead of `dlt.read_stream()`:**
# MAGIC - This table uses `ROW_NUMBER()` window logic, which requires batch semantics
# MAGIC - User profiles are modeled as mutable snapshots, not append-only event facts
# MAGIC - `@dlt.materialized_view` with `dlt.read()` is the correct Silver pattern for entity-state materialization
# MAGIC
# MAGIC **Mutable Entity Semantics:**
# MAGIC - GitHub users are mutable entities whose attributes can change over time
# MAGIC - Bronze preserves all raw snapshots; Silver surfaces only the latest observable state per user
# MAGIC - This separation supports auditability plus clean current-state analytics
# MAGIC
# MAGIC **Type 1 SCD-Style Behavior:**
# MAGIC - Newer snapshots supersede older snapshots for the same `actor_login`
# MAGIC - Silver does not store multiple active versions per user key
# MAGIC - Historical versioning can be added later in downstream dimensions if required
# MAGIC
# MAGIC **Processing Logic:**
# MAGIC - Flatten nested JSON from `raw_payload` into analytics-ready columns
# MAGIC - Cast `followers` and `public_repos` to INT for metric aggregations
# MAGIC - Cast `user_created_at` to TIMESTAMP for temporal analysis
# MAGIC - Derive `ingestion_date` from `_ingested_at` for partition pruning
# MAGIC
# MAGIC **Partition Strategy:**
# MAGIC - Partitioning by `ingestion_date` aligns with ingestion recency filters
# MAGIC - Supports efficient incremental maintenance and query performance on serverless compute
# MAGIC
# MAGIC **Connection to Future Gold Analytics:**
# MAGIC - `tbl_slv_users` provides canonical user context for Gold joins with events and repositories
# MAGIC - Enables contributor profiling, activity segmentation, and follower/repo-correlated analytics
# MAGIC - Deterministic deduplication prevents duplicated user-state inflation in aggregates
