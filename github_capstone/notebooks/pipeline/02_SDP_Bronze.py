# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer: Incremental Ingestion
# MAGIC
# MAGIC ## Purpose
# MAGIC Incrementally ingest raw GitHub Events JSON files from Unity Catalog Volumes
# MAGIC using Spark Declarative Pipelines (SDP) Auto Loader, persisting them in a
# MAGIC bronze-layer Delta table with metadata tracking.
# MAGIC
# MAGIC ## Data Flow
# MAGIC - **Source**: `/Volumes/workspace/gh_dev/raw/` (raw JSON files)
# MAGIC - **Sink**: `st_brz_events` (bronze Delta table)
# MAGIC - **Processing**: Streaming ingestion with Auto Loader schema inference
# MAGIC - **Metadata**: File path and ingestion timestamp added for lineage
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
RAW_DATA_PATH = spark.conf.get("raw_data_path")
SCHEMA_LOCATION = spark.conf.get("bronze_schema_path")
CLOUDFILES_FORMAT = "json"

# COMMAND ----------

@dlt.table(
    name="st_brz_events",
    comment="Bronze layer: Raw GitHub Events ingested via Auto Loader",
    partition_cols=["ingestion_date"],
    table_properties={ 
        "quality": "bronze"
    }
)
def st_brz_events():
    """
    Incrementally ingest raw GitHub Events from JSON files using Auto Loader.
    
    Returns:
        Streaming DataFrame with:
        - raw_payload: STRUCT containing all raw JSON event fields
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
        .load(RAW_DATA_PATH)
        .select(
            struct("*").alias("raw_payload"),
            col("_metadata.file_path").alias("source_file"),
            current_timestamp().alias("_ingested_at")
        ).withColumn("ingestion_date", to_date(col("_ingested_at"))
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC **Configuration Parameters:**
# MAGIC - `RAW_DATA_PATH`: Unity Catalog Volume path containing raw GitHub Events JSON files
# MAGIC - `SCHEMA_LOCATION`: Auto Loader schema cache directory for automatic evolution across pipeline runs
# MAGIC - `CHECKPOINT_LOCATION`: State tracking directory storing list of processed files
# MAGIC - `CLOUDFILES_FORMAT`: JSON format parser configuration
# MAGIC
# MAGIC **Table Properties:**
# MAGIC - Partitioned by `ingestion_date` (derived from `_ingested_at`) for query performance
# MAGIC - `quality: bronze` metadata tag for data lineage tracking
# MAGIC - Managed by DLT framework for automatic refresh and error handling
# MAGIC
# MAGIC **Auto Loader Behavior:**
# MAGIC - **First run**: Scans all existing JSON files in `/Volumes/workspace/gh_dev/raw/`, infers schema
# MAGIC - **Subsequent runs**: Only processes new files added since last checkpoint (incremental)
# MAGIC - **Schema evolution**: Cached at `SCHEMA_LOCATION` and automatically evolved on schema changes
# MAGIC - **Max batch size**: 100 files per trigger for stability on serverless compute
# MAGIC - **Type inference**: Automatically detects numeric/boolean types, not just string columns
# MAGIC
# MAGIC **Metadata Columns:**
# MAGIC - `raw_payload`: STRUCT containing all raw JSON event data (preserved as-is for lineage)\n
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