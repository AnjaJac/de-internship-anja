# Northwind SQL Analysis – Week 1

## Project Overview
This project explores the Northwind database using PostgreSQL to answer real business questions related to customers, orders, revenue, and operational performance.

The focus is not only on writing SQL queries, but on **deriving meaningful insights** using:
- Aggregations
- Joins
- Subqueries and CTEs
- Window functions
- Analytical patterns

---

## Environment Setup

### Stack
- PostgreSQL (Docker container)
- DBeaver (query interface)
- Git/GitHub (version control)

### Setup Steps

1. Start PostgreSQL:
`docker-compose up -d`

2. Connect via DBeaver.

3. Set schema:
`SET search_path TO northwind;`

---

## Data Model Understanding
The analysis is based on:
- Customers
- Orders
- Order Details
- Products

**Core relationship:**
`Customers → Orders → Order Details → Products`

This allows tracking who bought what, when, and for how much.

---

## SQL Analysis by File

### 01 – Customers Overview
**Goal:** Understand the customer base.
* Lists customers and key attributes.
* Identifies distribution by country/region.
* 👉 **Business Question:** Who are our customers and where are they located?

### 02 – Orders Aggregations
**Goal:** Measure sales performance.
* Total revenue calculation (`Quantity * UnitPrice`).
* Aggregations by customer and time.
* 👉 **Business Question:** How much revenue are we generating?

### 03 – Business Insights
**Goal:** Extract high-value insights.
* Combines multiple tables.
* Identifies top customers and products.
* 👉 **Business Question:** Who are the most valuable customers?

### 04 – Filtering Conditions
**Goal:** Focus analysis on specific segments.
* Uses `WHERE`, `BETWEEN`, `IN`.
* Filters by country, date, or product.
* 👉 **Business Question:** What happens in specific scenarios or subsets?

### 05 – Subqueries & CTEs
**Goal:** Structure complex logic.
* Subqueries for nested filtering.
* CTEs for readability and modular logic.
* 👉 **Business Question:** How can we break down complex analysis into steps?

### 06 – Operational Insights
**Goal:** Analyze day-to-day operations.
* Order frequency.
* Sales trends.
* 👉 **Business Question:** How is the business performing operationally?

### 07 – Window Functions
**Goal:** Add advanced analytics without losing detail.
* `RANK()` – ranking customers/products.
* `ROW_NUMBER()` – unique ordering.
* `SUM() OVER()` – running totals.
* 👉 **Business Question:** How do entities compare within groups?

### 08 – Analytical Window Patterns
**Goal:** Perform deeper analysis.
* Running totals.
* Partition-based comparisons.
* 👉 **Business Question:** How do metrics evolve over time?

### 09 – Views and Aggregates
**Goal:** Improve reusability.
* Creates views for repeated logic.
* Simplifies complex queries.
* 👉 **Business Question:** How can we standardize common analyses?

### 10 – Reporting Queries
**Goal:** Deliver business-ready outputs.
* **Example:** Customer revenue ranking, Sales summaries.
* 👉 **Business Question:** What insights can decision-makers act on?

---

## Key Learnings
* **SQL is not just querying — it's thinking in data.**
* **Small differences in functions matter:** `RANK()` vs `ROW_NUMBER()` changes results significantly.
* **`INNER JOIN` vs `LEFT JOIN`** affects completeness.
* **CTEs** improve readability for complex queries.
* **Window functions** unlock advanced analytics.

---

## Challenges
* Choosing *what* to analyze (not just how).
* Managing time for complex queries.
* Understanding subtle differences between similar SQL functions.
* Debugging joins and aggregations.

---

## Conclusion
This project builds a foundation for:
* Analytical thinking
* Writing production-level SQL
* Translating business questions into data queries
EOF

## How to Run
1. Start PostgreSQL container via Docker Compose.
2. Connect using DBeaver or psql CLI.
3. Set the schema:  
   ```sql
   SET search_path TO northwind;