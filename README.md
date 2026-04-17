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