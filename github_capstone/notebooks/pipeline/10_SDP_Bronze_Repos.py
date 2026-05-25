# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer: Repository Metadata Ingestion
# MAGIC
# MAGIC ## Purpose
# MAGIC Incrementally ingest raw GitHub Repository metadata JSON files from Unity Catalog Volumes
# MAGIC using Spark Declarative Pipelines (SDP) Auto Loader, persisting them in a
# MAGIC bronze-layer Delta table with metadata tracking.
# MAGIC
# MAGIC ## Data Flow
# MAGIC - **Source**: `/Volumes/workspace/gh_dev/raw/repos/` (raw JSON files)
# MAGIC - **Sink**: `st_brz_repos` (bronze Delta table)
# MAGIC - **Processing**: Streaming ingestion with Auto Loader schema inference
# MAGIC - **Metadata**: File path and ingestion timestamp added for lineage
# MAGIC
# MAGIC ## Output Schema
# MAGIC | Column | Type | Description |
# MAGIC |--------|------|-------------|
# MAGIC | raw_payload | STRUCT | All raw JSON repository fields preserved as-is |
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
from pyspark.sql.functions import current_timestamp, struct, to_date, col

# COMMAND ----------

# Configuration parameters for raw data ingestion
RAW_REPOS_PATH = "/Volumes/workspace/gh_dev/raw/repos/"
SCHEMA_LOCATION = "/Volumes/workspace/gh_dev/schemas/bronze_repos/"
CLOUDFILES_FORMAT = "json"

# COMMAND ----------

@dlt.table(
    name="st_brz_repos",
    comment="Bronze layer: Raw GitHub Repository metadata ingested via Auto Loader",
    partition_cols=["ingestion_date"],
    table_properties={
        "quality": "bronze"
    }
)
def st_brz_repos():
    """
    Incrementally ingest raw GitHub Repository metadata from JSON files using Auto Loader.

    Returns:
        Streaming DataFrame with:
        - raw_payload: STRUCT containing all raw JSON repository fields
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
        .option("cloudFiles.maxFilesPerTrigger", "100")
        .load(RAW_REPOS_PATH)
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
# MAGIC - `RAW_REPOS_PATH`: Unity Catalog Volume path containing raw GitHub Repository metadata JSON files
# MAGIC - `SCHEMA_LOCATION`: Auto Loader schema cache directory for automatic evolution across pipeline runs
# MAGIC - `CLOUDFILES_FORMAT`: JSON format parser configuration
# MAGIC
# MAGIC **Why checkpointLocation is Not Set:**
# MAGIC - Checkpoint management is handled exclusively by the DLT/SDP pipeline framework
# MAGIC - Setting it in code causes `CF_UNKNOWN_OPTION_KEYS_ERROR`
# MAGIC - DLT automatically maintains checkpoint state in internal locations
# MAGIC
# MAGIC **Why ingestion_date is Added via withColumn:**
# MAGIC - `_ingested_at` is created in the same `.select()` call
# MAGIC - Self-referencing a column within the same select() causes column resolution errors
# MAGIC - `.withColumn()` after select() ensures the dependency chain is correct
# MAGIC
# MAGIC **Table Properties:**
# MAGIC - Partitioned by `ingestion_date` (derived from `_ingested_at`) for query performance
# MAGIC - `quality: bronze` metadata tag for data lineage tracking
# MAGIC - Managed by DLT framework for automatic refresh and error handling
# MAGIC
# MAGIC **Auto Loader Behavior:**
# MAGIC - **First run**: Scans all existing JSON files in `/Volumes/workspace/gh_dev/raw/repos/`, infers schema
# MAGIC - **Subsequent runs**: Only processes new files added since last checkpoint (incremental)
# MAGIC - **Schema evolution**: Cached at `SCHEMA_LOCATION` and automatically evolved on schema changes
# MAGIC - **Max batch size**: 100 files per trigger for stability on serverless compute
# MAGIC - **Type inference**: Automatically detects numeric/boolean types, not just string columns
# MAGIC
# MAGIC **Metadata Columns:**
# MAGIC - `raw_payload`: STRUCT containing all raw JSON repository data (preserved as-is for lineage)
# MAGIC - `source_file`: Source file path from Auto Loader metadata for traceability
# MAGIC - `_ingested_at`: UTC timestamp when row was processed
# MAGIC - `ingestion_date`: Date portion extracted for table partitioning
# MAGIC
# MAGIC **Processing Logic:**
# MAGIC - Auto Loader reads JSON files incrementally using checkpoints to track state
# MAGIC - All raw JSON fields are wrapped into `raw_payload` struct (preserves hierarchy)
# MAGIC - `source_file` metadata extracted for data lineage tracking
# MAGIC - Ingestion timestamp and partition date added for audit trail
# MAGIC - Streaming DataFrame is returned to DLT for managed table creation and update
