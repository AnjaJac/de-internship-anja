# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer: User Metadata Ingestion
# MAGIC
# MAGIC ## Purpose
# MAGIC Incrementally ingest raw GitHub User profile metadata JSON files from Unity Catalog Volumes
# MAGIC using Spark Declarative Pipelines (SDP) Auto Loader, persisting them in a
# MAGIC bronze-layer Delta table with metadata tracking.
# MAGIC
# MAGIC This Bronze table stores mutable user-profile snapshots as historical raw records
# MAGIC to preserve replayability and support future SCD-style modeling downstream.
# MAGIC
# MAGIC ## Data Flow
# MAGIC - **Source**: `/Volumes/workspace/gh_dev/raw/users/` (raw JSON snapshot files)
# MAGIC - **Sink**: `st_brz_users` (bronze Delta table)
# MAGIC - **Processing**: Streaming ingestion with Auto Loader schema inference
# MAGIC - **Metadata**: File path and ingestion timestamp added for lineage
# MAGIC
# MAGIC ## Output Schema
# MAGIC | Column | Type | Description |
# MAGIC |--------|------|-------------|
# MAGIC | raw_payload | STRUCT | All raw JSON user profile fields preserved as-is |
# MAGIC | source_file | STRING | Source file path from Auto Loader metadata for traceability |
# MAGIC | _ingested_at | TIMESTAMP | UTC timestamp when row was processed |
# MAGIC | ingestion_date | DATE | Date portion for table partitioning |
# MAGIC
# MAGIC ## Compatibility
# MAGIC - Databricks Free Edition
# MAGIC - Unity Catalog
# MAGIC - Serverless compute
# MAGIC - SDP/DLT declarative pipeline framework

# COMMAND ----------

import dlt
from pyspark.sql.functions import col, current_timestamp, struct, to_date

# COMMAND ----------

# Configuration parameters for raw user snapshot ingestion
RAW_USERS_PATH = "/Volumes/workspace/gh_dev/raw/users/"
SCHEMA_LOCATION = "/Volumes/workspace/gh_dev/schemas/bronze_users/"
CLOUDFILES_FORMAT = "json"
MAX_FILES_PER_TRIGGER = "100"

# COMMAND ----------

@dlt.table(
    name="st_brz_users",
    comment="Bronze layer: Raw GitHub User profile metadata ingested via Auto Loader",
    partition_cols=["ingestion_date"],
    table_properties={
        "quality": "bronze"
    }
)
def st_brz_users():
    """
    Incrementally ingest raw GitHub User profile snapshots from JSON files using Auto Loader.

    Returns:
        Streaming DataFrame with:
        - raw_payload: STRUCT containing all raw JSON user profile fields
        - source_file: Source file path from Auto Loader metadata
        - _ingested_at: Processing timestamp in UTC
        - ingestion_date: Date for partitioning
    """
    return (
        spark
        .readStream
        .format("cloudFiles")
        .option("cloudFiles.format", CLOUDFILES_FORMAT)
        .option("cloudFiles.schemaLocation", SCHEMA_LOCATION)
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.maxFilesPerTrigger", MAX_FILES_PER_TRIGGER)
        .load(RAW_USERS_PATH)
        .select(
            struct("*").alias("raw_payload"),
            col("_metadata.file_path").alias("source_file"),
            current_timestamp().alias("_ingested_at")
        ).withColumn("ingestion_date", to_date(col("_ingested_at")))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC **Configuration Parameters:**
# MAGIC - `RAW_USERS_PATH`: Unity Catalog Volume path containing raw GitHub User profile JSON snapshots
# MAGIC - `SCHEMA_LOCATION`: Auto Loader schema cache directory for automatic evolution across pipeline runs
# MAGIC - `CLOUDFILES_FORMAT`: JSON format parser configuration
# MAGIC - `MAX_FILES_PER_TRIGGER`: Limits each micro-batch to control serverless load
# MAGIC
# MAGIC **Why checkpointLocation is Not Set:**
# MAGIC - Checkpoint management is handled exclusively by the DLT/SDP pipeline framework
# MAGIC - Setting checkpoint options in code conflicts with managed pipeline behavior
# MAGIC - DLT automatically stores and maintains checkpoint state in internal managed locations
# MAGIC
# MAGIC **Why ingestion_date is Added via withColumn:**
# MAGIC - `_ingested_at` is created in the same `.select()` call
# MAGIC - Referencing a newly created alias inside the same select chain can cause resolution errors
# MAGIC - `.withColumn()` after select() guarantees correct dependency order
# MAGIC
# MAGIC **Table Properties:**
# MAGIC - Partitioned by `ingestion_date` (derived from `_ingested_at`) for query performance
# MAGIC - `quality: bronze` metadata tag for data lineage tracking
# MAGIC - Managed by DLT framework for automatic refresh and operational resilience
# MAGIC
# MAGIC **Auto Loader Behavior:**
# MAGIC - **First run**: Scans all existing JSON files in `/Volumes/workspace/gh_dev/raw/users/`, infers schema
# MAGIC - **Subsequent runs**: Only processes new files since last managed checkpoint (incremental)
# MAGIC - **Schema evolution**: Cached at `SCHEMA_LOCATION` and evolved automatically as new fields appear
# MAGIC - **Batch sizing**: Processes up to 100 files per trigger for stable throughput on serverless compute
# MAGIC - **Type inference**: Detects numeric/boolean/date-like types beyond raw string defaults
# MAGIC
# MAGIC **Metadata Columns:**
# MAGIC - `raw_payload`: STRUCT containing all raw JSON user profile data (full fidelity preserved)
# MAGIC - `source_file`: Source file path from Auto Loader metadata for traceability
# MAGIC - `_ingested_at`: UTC timestamp when row was processed
# MAGIC - `ingestion_date`: Date portion extracted for table partitioning
# MAGIC
# MAGIC **Processing Logic:**
# MAGIC - Auto Loader incrementally ingests append-only raw snapshot files
# MAGIC - Entire source JSON is wrapped into `raw_payload` using `struct("*")` to preserve raw fidelity
# MAGIC - Lineage metadata is added uniformly to align with `st_brz_events` and `st_brz_repos`
# MAGIC - Bronze data remains immutable and replayable for future SCD and conformance modeling
