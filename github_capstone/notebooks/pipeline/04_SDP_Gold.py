# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer: Materialized Views
# MAGIC
# MAGIC ## Purpose
# MAGIC Create aggregated Gold tables for downstream analytics and visualization.
# MAGIC The Gold layer provides hourly repo velocity and distinct user statistics
# MAGIC based on the cleaned Silver events.
# MAGIC
# MAGIC ## Data Flow
# MAGIC - **Source**: `tbl_slv_events` (Silver layer)
# MAGIC - **Sinks**:
# MAGIC   - `mv_gld_repo_velocity`
# MAGIC   - `mv_gld_user_stats`
# MAGIC   - `mv_gld_event_distribution`
# MAGIC - **Processing**: Aggregations and materialized refresh behavior
# MAGIC
# MAGIC ## Compatibility
# MAGIC - Databricks Free Edition
# MAGIC - Unity Catalog
# MAGIC - Serverless compute
# MAGIC - SDP/DLT declarative pipeline framework

# COMMAND ----------

import dlt
from pyspark.sql.functions import window, col, count, countDistinct, hour, to_date

# COMMAND ----------

@dlt.materialized_view(
    name="mv_gld_repo_velocity",
    comment="Gold materialized view: Event volume by hour of day",
    partition_cols=["window_date"],
    table_properties={
        "quality": "gold"
    }
)
def repo_velocity():
    """
    Compute 1-hour event counts per repository from the Silver layer.

    Returns:
        DataFrame with one row per repo and one-hour window:
        - repo_name
        - event_hour
        - event_count
    """

      
    return (
        dlt.read("tbl_slv_events")
        .groupBy(window("created_at", "1 hour"), "repo_name")
        .agg(count("*").alias("event_count"))
        .withColumn("event_hour", col("window.start"))
        .withColumn("window_date", to_date(col("window.start")))
        .drop("window")
    )

# COMMAND ----------

@dlt.materialized_view(
    name="mv_gld_user_stats",
    comment="Gold materialized view: Unique contributor count per repository",
    table_properties={
        "quality": "gold"
    }
)
def user_stats():
    """
    Compute distinct actor counts per repository from the Silver layer.

    Returns:
        DataFrame with one row per repository:
        - repo_name
        - unique_contributors
    """

    return (
        dlt.read("tbl_slv_events")
        .groupBy("repo_name")
        .agg(
            countDistinct(col("actor_login")).alias("unique_contributors")
        )
    )

@dlt.materialized_view(
    name="mv_gld_event_distribution",
    comment="Gold materialized view: Event volume by hour of day",
    table_properties={
        "quality": "gold"
    }
)
def event_distribution():
    """
    Compute event count distribution by hour of day from the Silver layer.

    Returns:
        DataFrame with one row per hour of day:
        - hour_of_day (0-23)
        - event_count
    """
    return(
        dlt.read("tbl_slv_events")
        .groupBy(hour("created_at").alias("hour_of_day"))
        .agg(count("*").alias("event_count"))
    )
# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC **Gold Aggregations:**
# MAGIC - `mv_gld_repo_velocity` computes repo-level event volume in 1-hour windows
# MAGIC - `mv_gld_user_stats` computes distinct contributor count per repository
# MAGIC - `mv_gld_event_distribution` computes event volume by hour of day (0-23)
# MAGIC
# MAGIC **Materialized Views:**
# MAGIC - These tables are defined as DLT materialized views and refresh automatically when
# MAGIC   the Silver source changes
# MAGIC - `mv_gld_repo_velocity` partitioned by `event_hour` for time-based query performance
# MAGIC - All tables tagged with `quality: gold` for data lineage tracking
# MAGIC
# MAGIC **Visualization Use Cases:**
# MAGIC - Repo activity timeline charts (mv_gld_repo_velocity)
# MAGIC - Repository contributor analysis (mv_gld_user_stats)
# MAGIC - Daily activity patterns by hour (mv_gld_event_distribution)
