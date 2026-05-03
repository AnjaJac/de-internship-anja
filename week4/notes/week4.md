# Week 4 — Apache Spark & Databricks Lakehouse Fundamentals

## Overview

This project explores distributed data processing using Apache Spark in Databricks. The focus is on understanding both practical usage (PySpark, Spark SQL, Delta Lake) and internal execution (lazy evaluation, DAG, shuffle, execution model).

---

## Architecture — Lakehouse Model

Catalog → Schema → Volume → Data (files)  
                        ↓  
                   Delta Tables  

- Catalog: Top-level container
- Schema: Logical grouping of data
- Volume: File storage (CSV, JSON, Parquet)
- Delta Table: Structured, transactional layer

---

## Data Ingestion

Data was loaded from CSV:

```python
df = spark.read.csv(..., header=True, inferSchema=True)
```

- DataFrame = distributed table
- Schema inferred automatically

---

## Transformations vs Actions

- Transformations (lazy): filter, select, groupBy  
- Actions (execution): show, count, write  

Transformations build a DAG, actions trigger execution.

---

## Lazy Evaluation

Spark does not execute transformations immediately.  
Instead, it builds a DAG and executes it only when an action is called.

Benefits:
- optimization
- reduced computation
- better performance

---

## PySpark Transformations

Used:
- filter
- select
- groupBy + aggregation

Example:

```python
df.groupBy("day").agg(count("*"), avg("total_bill"))
```

---

## Feature Engineering

Created:

```python
tip_pct = tip / total_bill
```

Feature engineering = creating new useful columns.

---

## Window Functions

Used for advanced analytics:

- ranking
- running totals

These operate across rows without collapsing data.

---

## Spark SQL & API Interoperability

DataFrame registered as view:

```python
df.createOrReplaceTempView("tips_table")
```

SQL queries produce the same result as DataFrame API.

Reason:
Both use the Catalyst Optimizer.

---

## Legacy SQL Migration

Example:

```sql
SELECT day, COUNT(*), AVG(total_bill)
FROM tips_table
GROUP BY day
```

Same syntax as traditional SQL, but executed in a distributed system.

---

## Execution Model (df.count())

When an action is called:

1. Driver builds DAG
2. Plan optimized (Catalyst)
3. Split into stages
4. Executors process partitions
5. Results returned

---

## Job, Stage, Task

Job → triggered by action  
Stage → separated by shuffle  
Task → runs on a partition  

---

## File Formats

Used:
- CSV (raw)
- JSON (semi-structured)
- Parquet (optimized)
- Delta (transactional)

---

## Performance Comparison

CSV ~1.77s  
JSON ~1.39s  
Parquet ~1.20s  

Conclusion:

Parquet < JSON < CSV

Reason:
- Parquet is columnar and compressed
- CSV requires full parsing

---

## Delta Lake

Delta adds:
- ACID transactions
- schema enforcement
- time travel
- updates & deletes

Delta = Parquet + transaction log

---

## Time Travel

```sql
SELECT * FROM table VERSION AS OF 0
```

Used for:
- debugging
- recovery
- auditing

---

## Partitioning

```python
.partitionBy("day")
```

Creates:
day=Sun/  
day=Sat/  

Benefits:
- partition pruning
- faster queries

---

## Shuffle

Occurs during GROUP BY.

Definition:
Redistribution of data across partitions so rows with same key are grouped together.

Why expensive:
- network transfer
- disk I/O

---

## Spark UI (Execution Analysis)

Observed:
- DAG (execution plan)
- stages created
- shuffle (Exchange node)

---

## Big Picture — Optimization

Lazy evaluation allows Spark to:
- optimize entire query
- push filters early
- reduce data movement

---

## Resource Management (Databricks)

- Compute = temporary (auto shutdown)
- Data = persistent

---

## Conclusion

This project demonstrates:
- distributed data processing
- hybrid querying (PySpark + SQL)
- storage optimization (Parquet, Delta)
- execution understanding (DAG, shuffle)
- performance awareness

---

## Final Insight

Spark is not just about writing code —  
it is about understanding how data is processed at scale.