# Data Engineering Internship – Projects

This repository contains weekly assignments completed as part of a Data Engineering Internship program. Each week focuses on building practical skills in SQL, Python, and data pipeline design.

---

## Week 1 – SQL Fundamentals

### Overview
Worked with the Northwind database to practice SQL queries and data analysis.

### Key Topics
- SELECT queries and filtering  
- JOINs (INNER, LEFT)  
- Aggregations (SUM, COUNT, AVG)  
- Window functions (RANK)  
- Business-oriented reporting queries  

### Outcome
- Wrote analytical queries to extract business insights  
- Structured SQL files by topic  
- Practiced writing clean, readable queries  

---

## Week 2 – Python Data Pipeline

### Overview
Built a modular data pipeline in Python to ingest, clean, transform, and export data.

### Pipeline Steps

#### 1. Data Ingestion
- Load CSV dataset into a pandas DataFrame  

#### 2. Data Cleaning
- Standardized column names (snake_case)  
- Removed duplicates  
- Handled missing values  
- Converted date columns  

#### 3. Data Transformation
- Extracted duration into:
  - `duration_value`
  - `duration_unit`  
- Normalized duration units  
- Split genres into lists  
- Created derived column `is_movie`  

#### 4. Data Export
- Saved processed data as:
  - CSV  
  - JSON  
  - Parquet  

---

## Testing

- Implemented unit tests using pytest  
- Covered cleaning and transformation functions  
- Handled edge cases (missing values, parsing issues)  

---

## Setup

### Create virtual environment

```bash
python3 -m venv de_env
source de_env/bin/activate
```
### Install dependencies
```bash
pip install pandas pyarrow pytest
```
## How to Run
```bash
python week2/ingest_api.py
```
## How to Test
```bash
pytest
```
---

## Week 3 – Data Modeling and Warehouse Concepts

### Overview

Designed and implemented a data warehouse model for an e-commerce scenario using a star schema.

---

### Key Concepts

- OLTP vs OLAP systems  
- Star schema design  
- Fact table grain definition  
- Slowly Changing Dimensions (SCD Type 2)  
- Medallion architecture (Bronze, Silver, Gold)  

---

### Implementation

#### Star Schema

- `fact_sales` → one row per order item  
- `dim_product` → SCD Type 2  
- `dim_customer` → SCD Type 2  
- `dim_date` → generated date dimension  

---

#### SCD Type 2

- Implemented using:
  - `start_date`
  - `end_date`
  - `is_current`
- Enforced using partial unique indexes  

---

#### Transformations

- Populated `dim_date` using `generate_series`  
- Created aggregated table `fact_sales_daily`  
  - Grain: one row per product per day  
  - Used for performance optimization  

---

### Data Model Files

- `week3/datamodel/ecommerce_star_schema.sql`  
- `week3/datamodel/transformations.sql`  
- `week3/datamodel/ecommerce.dbml`  
- `week3/datamodel/ecommerce_star_schema.png`  

---

### Key Takeaways

- Grain defines the correctness of the model  
- Star schema simplifies analytical queries  
- SCD Type 2 preserves historical accuracy  
- Aggregations improve performance but reduce detail  

##  Week 4 — Apache Spark & Databricks

###  Setup

- Created a Databricks Free Edition account  
- Set up workspace and explored the UI  
- Used serverless compute for running notebooks  
- Created a structured environment using:
  - Catalog  
  - Schema  
  - Volume (for file storage)  

---

###  What was done

####  Data Processing
- Loaded dataset using `spark.read.csv`
- Performed transformations using PySpark:
  - `filter`, `select`, `groupBy`, `agg`
- Created derived columns (feature engineering)

---

####  Advanced Transformations
- Implemented window functions:
  - ranking (`rank`)
  - aggregations over partitions

---

####  Spark SQL
- Created temporary views  
- Rewrote DataFrame logic using SQL  
- Demonstrated equivalence between PySpark and Spark SQL  

---

####  Legacy Migration
- Rewrote traditional SQL queries (from Week 1) into Spark SQL  
- Executed them in a distributed environment  

---

####  File Formats & Storage
- Worked with:
  - CSV (raw ingestion)
  - JSON (semi-structured format)
  - Parquet (columnar, optimized)
- Compared performance across formats  

---

####  Delta Lake
- Created Delta tables  
- Demonstrated:
  - ACID transactions  
  - Time travel (versioning)  
- Performed updates and queried previous versions  

---

####  Partitioning
- Partitioned data by `day`  
- Verified partition structure  
- Demonstrated partition pruning  

---

####  Performance Analysis
- Compared execution time:
  - CSV vs JSON vs Parquet  
- Observed Parquet as the most efficient format  

---

####  Spark UI & Execution
- Used Query Profile (Spark UI equivalent)  
- Analyzed:
  - DAG (Directed Acyclic Graph)
  - stages and tasks  
- Identified shuffle during `GROUP BY` operations  

---

####  Core Concepts Learned
- Transformations vs Actions  
- Lazy Evaluation  
- DAG execution model  
- Shuffle and its cost  
- Distributed processing (Driver vs Executors)  

---

###  Project Structure
week4/
├── notebooks/
└── notes/


---

### Dataset Note

The dataset used in this project is **not included in the repository**.

This follows best practices:
- datasets can be large  
- data is often external  
- repositories should focus on code and logic  

To reproduce the project:
1. Use a similar dataset (e.g., tips or sales dataset)
2. Upload it to Databricks
3. Update file paths in notebooks