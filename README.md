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
