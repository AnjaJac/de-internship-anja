# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer: Enriched Semantic Analytics Views
# MAGIC
# MAGIC ## Purpose
# MAGIC Build enriched Gold-layer analytical projections by combining immutable event facts
# MAGIC with canonical repository and user dimensions from Silver.
# MAGIC
# MAGIC ## Data Flow
# MAGIC - **Fact Source**: `tbl_slv_events`
# MAGIC - **Dimension Sources**: `tbl_slv_repos`, `tbl_slv_users`
# MAGIC - **Gold Outputs**:
# MAGIC   - `mv_gld_repo_enriched`
# MAGIC   - `mv_gld_language_distribution`
# MAGIC   - `mv_gld_user_enriched`
# MAGIC   - `mv_gld_activity_summary`
# MAGIC
# MAGIC ## Semantic Modeling
# MAGIC - **Events** are immutable facts (activity records)
# MAGIC - **Repositories** and **Users** are mutable entities represented as latest canonical state in Silver
# MAGIC - Gold views provide semantic analytical projections, not ingestion logic
# MAGIC
# MAGIC ## Fact vs Dimension Joins
# MAGIC - Event fact rows are enriched with current dimension attributes through key-based joins
# MAGIC - `repo_name` joins events to repository dimension
# MAGIC - `actor_login` joins events to user dimension
# MAGIC
# MAGIC ## Analytical Grain
# MAGIC - Enriched event views preserve event-level grain: **1 event row = 1 analytical event row**
# MAGIC - Aggregated language distribution intentionally changes grain to language-level metrics
# MAGIC
# MAGIC ## Join Semantics
# MAGIC - LEFT joins are used to retain all event facts even when dimension context is missing
# MAGIC - Join cardinality is safe because:
# MAGIC   - `tbl_slv_repos` is deduplicated to one row per `repo_name`
# MAGIC   - `tbl_slv_users` is deduplicated to one row per `actor_login`
# MAGIC - This avoids accidental event row multiplication
# MAGIC
# MAGIC ## Gold Layer Philosophy
# MAGIC - Gold models are business-ready and analytics-oriented
# MAGIC - They are optimized for BI and downstream consumption
# MAGIC - They intentionally separate semantic serving logic from Bronze/Silver operational processing
# MAGIC
# MAGIC ## Compatibility
# MAGIC - Databricks Free Edition
# MAGIC - Unity Catalog
# MAGIC - Serverless compute
# MAGIC - SDP/DLT declarative pipeline framework

# COMMAND ----------

import dlt
from pyspark.sql.functions import (
    col, 
    coalesce,
    count, 
    countDistinct, 
    avg,
    round,
    lit
)

# COMMAND ----------

@dlt.materialized_view(
    name="mv_gld_repo_enriched",
    comment="Gold materialized view: Event-level facts enriched with repository metadata",
    partition_cols=["created_at_date"],
    table_properties={
        "quality": "gold"
    }
)
def mv_gld_repo_enriched():
    """
    Enrich immutable event facts with repository dimension attributes.

    Grain:
        One row per event_id (event-level, non-aggregated).

    Returns:
        Event rows augmented with repository analytical context.
    """

    events_df = dlt.read("tbl_slv_events").alias("ev")
    repos_df = dlt.read("tbl_slv_repos").alias("rp")

    return (
        events_df
        .join(
            repos_df,
            col("ev.repo_name") == col("rp.repo_name"),
            "left"
        )
        .select(
            col("ev.event_id").alias("event_id"),
            col("ev.event_type").alias("event_type"),
            col("ev.actor_login").alias("actor_login"),
            col("ev.repo_name").alias("repo_name"),
            col("ev.created_at").alias("created_at"),
            col("ev.created_at_date").alias("created_at_date"),
            col("rp.stars").alias("stars"),
            col("rp.forks").alias("forks"),
            col("rp.primary_language").alias("primary_language"),
            col("rp.open_issues").alias("open_issues")
        )
    )

# COMMAND ----------

@dlt.materialized_view(
    name="mv_gld_language_distribution",
    comment="Gold materialized view: Repository activity distribution by primary language",
    table_properties={
        "quality": "gold"
    }
)
def mv_gld_language_distribution():
    """
    Aggregate enriched event data by repository primary language.

    Grain:
        One row per primary_language.

    Returns:
        Language-level activity and diversity metrics for analytical reporting.
    """

    return (
        dlt.read("mv_gld_repo_enriched")
        .withColumn(
            "primary_language",
            coalesce(col("primary_language"), lit("Unknown"))
        )
        .groupBy("primary_language")
        .agg(
            count("*").alias("event_count"),
            countDistinct(col("repo_name")).alias("repo_count"),
            countDistinct(col("actor_login")).alias("distinct_contributors"),
            round(avg(col("stars")), 2).alias("avg_stars"),
            round(avg(col("forks")), 2).alias("avg_forks"),
            round(avg(col("open_issues")), 2).alias("avg_open_issues")
        )
    )

# COMMAND ----------

@dlt.materialized_view(
    name="mv_gld_user_enriched",
    comment="Gold materialized view: Event-level facts enriched with contributor profile metadata",
    partition_cols=["created_at_date"],
    table_properties={
        "quality": "gold"
    }
)
def mv_gld_user_enriched():
    """
    Enrich immutable event facts with user dimension attributes.

    Grain:
        One row per event_id (event-level, non-aggregated).

    Returns:
        Event rows augmented with contributor profile context.
    """

    events_df = dlt.read("tbl_slv_events").alias("ev")
    users_df = dlt.read("tbl_slv_users").alias("us")

    return (
        events_df
        .join(
            users_df,
            col("ev.actor_login") == col("us.actor_login"),
            "left"
        )
        .select(
            col("ev.event_id").alias("event_id"),
            col("ev.event_type").alias("event_type"),
            col("ev.actor_login").alias("actor_login"),
            col("ev.repo_name").alias("repo_name"),
            col("ev.created_at").alias("created_at"),
            col("ev.created_at_date").alias("created_at_date"),
            col("us.company").alias("company"),
            col("us.location").alias("location"),
            col("us.followers").alias("followers"),
            col("us.public_repos").alias("public_repos")
        )
    )

# COMMAND ----------

@dlt.materialized_view(
    name="mv_gld_activity_summary",
    comment="Gold materialized view: Fully enriched event analytics across events, repositories, and users",
    partition_cols=["created_at_date"],
    table_properties={
        "quality": "gold"
    }
)
def mv_gld_activity_summary():
    """
    Build a unified event-level analytical dataset across all core domains.

    Grain:
        One row per event_id (event-level, non-aggregated).

    Returns:
        Fully enriched event analytics view combining fact and both dimensions.
    """

    events_df = dlt.read("tbl_slv_events").alias("ev")
    repos_df = dlt.read("tbl_slv_repos").alias("rp")
    users_df = dlt.read("tbl_slv_users").alias("us")

    return (
        events_df
        .join(
            repos_df,
            col("ev.repo_name") == col("rp.repo_name"),
            "left"
        )
        .join(
            users_df,
            col("ev.actor_login") == col("us.actor_login"),
            "left"
        )
        .select(
            col("ev.event_id").alias("event_id"),
            col("ev.event_type").alias("event_type"),
            col("ev.repo_name").alias("repo_name"),
            col("ev.actor_login").alias("actor_login"),
            col("ev.created_at").alias("created_at"),
            col("ev.created_at_date").alias("created_at_date"),
            col("rp.primary_language").alias("primary_language"),
            col("rp.stars").alias("stars"),
            col("rp.forks").alias("forks"),
            col("rp.open_issues").alias("open_issues"),
            col("us.followers").alias("followers"),
            col("us.location").alias("location"),
            col("us.company").alias("company"),
            col("us.public_repos").alias("public_repos")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC **Processing Logic:**
# MAGIC - `mv_gld_repo_enriched`: LEFT join events with repository dimension on `repo_name`
# MAGIC - `mv_gld_language_distribution`: aggregate enriched repository activity by `primary_language`
# MAGIC - `mv_gld_user_enriched`: LEFT join events with user dimension on `actor_login`
# MAGIC - `mv_gld_activity_summary`: LEFT join events with both repository and user dimensions
# MAGIC
# MAGIC **Analytical Grain Guarantees:**
# MAGIC - Event-enriched views remain event-level with one row per event_id
# MAGIC - No aggregations are applied in event-enriched views
# MAGIC - Aggregation appears only in `mv_gld_language_distribution` by design
# MAGIC
# MAGIC **Why Joins Are Safe:**
# MAGIC - `tbl_slv_repos` is deduplicated to a unique `repo_name`
# MAGIC - `tbl_slv_users` is deduplicated to a unique `actor_login`
# MAGIC - Event-to-dimension joins are many-to-one, preventing row explosion
# MAGIC
# MAGIC **Fact and Dimension Semantics:**
# MAGIC - `tbl_slv_events`: immutable fact records
# MAGIC - `tbl_slv_repos`, `tbl_slv_users`: mutable entity dimensions (latest canonical state)
# MAGIC - Gold views combine both for consumable semantic analytics
# MAGIC
# MAGIC **Partition Strategy:**
# MAGIC - Event-level Gold views are partitioned by `created_at_date` inherited from event facts
# MAGIC - Supports efficient pruning for time-bounded analytics queries
# MAGIC
# MAGIC **Connection to Future Gold Analytics:**
# MAGIC - These enriched views provide a reusable semantic base for dashboards
# MAGIC - New domain-specific Gold KPIs can build on top of this layer without re-implementing joins
# MAGIC - Clean separation of fact/dimension modeling enables consistent governance and interpretation
