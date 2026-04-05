# SQL Assignments – Northwind Database

## Overview
This project contains SQL assignments performed on the Northwind database using PostgreSQL. The goal was to practice querying, data manipulation, reporting, and understanding database relationships.

## Key Features
- Ranking customers by total revenue.
- Daily and monthly order summaries.
- Combining multiple tables with different join types.
- Using window functions (RANK, ROW_NUMBER) for business reporting.
- Implementing aggregation and grouping for analytics.

## Tools & Technologies
- **PostgreSQL**: Relational database used for all queries.
- **Docker**: To run a local PostgreSQL environment.
- **DBeaver**: GUI to connect and query the database.
- **Git**: Version control to manage assignment files.

## How to Run
1. Start PostgreSQL container via Docker Compose.
2. Connect using DBeaver or psql CLI.
3. Set the schema:  
   ```sql
   SET search_path TO northwind;