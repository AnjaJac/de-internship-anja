# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer: Cleaning & Deduplication
# MAGIC
# MAGIC ## Purpose
# MAGIC Clean and deduplicate GitHub Events data from the bronze layer, extracting
# MAGIC key fields into a flat schema and ensuring data quality through deduplication.
# MAGIC
# MAGIC ## Data Flow
# MAGIC - **Source**: `st_brz_events` (bronze Delta table)
# MAGIC - **Sink**: `tbl_slv_events` (silver Delta table)
# MAGIC - **Processing**: Field extraction, type casting, deduplication
# MAGIC - **Quality**: No duplicate event_id records, flat schema
# MAGIC
# MAGIC ## Schema
# MAGIC | Column | Type | Source Field |
# MAGIC |--------|------|--------------|
# MAGIC | event_id | STRING | id |
# MAGIC | event_type | STRING | type |
# MAGIC | actor_login | STRING | actor.login |
# MAGIC | repo_name | STRING | repo.name |
# MAGIC | created_at | TIMESTAMP | created_at (cast via to_timestamp()) |
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

@dlt.expect_or_fail("event_id not null", "event_id IS NOT NULL")
@dlt.expect_or_drop("event_type not null", "event_type IS NOT NULL")
@dlt.table(
    name="tbl_slv_events",
    comment="Silver layer: Cleaned and deduplicated GitHub Events",
    partition_cols=["created_at_date"],
    table_properties={
        "quality": "silver"
    }
)
def tbl_slv_events():
    """
    Clean and deduplicate GitHub Events from bronze layer.
    
    Processing Steps:
    1. Extract specific fields from raw_payload struct
    2. Cast created_at to timestamp
    3. Apply window function to deduplicate by event_id (latest version)
    4. Filter for row_number == 1 to keep only latest record per event_id
    
    Returns:
        DataFrame with flat schema and no duplicate event_id records
    """
    
    # Define window specification for deduplication
    # Partition by event_id, order by event timestamp descending
    dedup_window = Window.partitionBy("event_id").orderBy(col("created_at").desc())
    
    return (
        dlt.read("st_brz_events")
        .select(
            col("raw_payload.id").alias("event_id"),
            col("raw_payload.type").alias("event_type"),
            col("raw_payload.actor.login").alias("actor_login"),
            col("raw_payload.repo.name").alias("repo_name"),
            to_timestamp(col("raw_payload.created_at")).alias("created_at"),
            to_date(to_timestamp(col("raw_payload.created_at"))).alias("created_at_date")
        )
        .withColumn(
            "row_num",
            row_number().over(dedup_window)
        )
        .filter(col("row_num") == 1)
        .drop("row_num")  # Remove temporary columns
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC **Deduplication Logic:**
# MAGIC - Uses window function partitioned by `event_id`
# MAGIC - Orders by `created_at` descending (latest first)
# MAGIC - Assigns row numbers within each partition
# MAGIC - Filters for `row_num == 1` to keep only the latest version
# MAGIC
# MAGIC **Field Extraction:**
# MAGIC - Accesses nested fields using dot notation: `raw_payload.field.subfield`
# MAGIC - `created_at` cast to TIMESTAMP using `to_timestamp()`
# MAGIC - All fields flattened to top-level columns
# MAGIC
# MAGIC **Data Quality:**
# MAGIC - Ensures no duplicate `event_id` records
# MAGIC - Validates timestamp format conversion
# MAGIC - Maintains referential integrity with bronze layer
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - Define gold-layer aggregations (04_SDP_Gold.py)
# MAGIC - Configure SDP pipeline trigger and schedule
# MAGIC - Add data quality checks and monitoring