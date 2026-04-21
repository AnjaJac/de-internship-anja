# Week 2 – Python Data Pipeline

## Overview

In this week, I built a data pipeline using Python that ingests, cleans, transforms, and saves data in multiple formats. The goal was to simulate a real-world data engineering workflow with modular, testable code.

---

## Dataset

Netflix Movies and TV Shows dataset stored as a CSV file.

---

## Pipeline Steps

### 1. Data Ingestion
- Load raw CSV data into a Pandas DataFrame

### 2. Data Cleaning
- Standardize column names (snake_case)
- Strip whitespace from string columns
- Handle missing values (fill with "Unknown")
- Convert date columns to datetime format
- Remove duplicate records

### 3. Data Transformation
- Extract duration into:
  - `duration_value` (numeric)
  - `duration_unit` (min / season)
- Normalize duration units
- Split genres into lists
- Create derived column `is_movie`

### 4. Data Export
Processed data is saved in:
- CSV
- JSON
- Parquet

---

## Project Structure
week2/
├── ingest_api.py
├── tests/
│ └── test_ingest.py
├── data/
│ ├── raw/ (ignored in Git)
│ └── processed/ (ignored in Git)
├── notes/
│ └── week2.md

---

---

## How to Run

- source de_env/bin/activate
- python week2/ingest_api.py
## How to Run test
- pytest

