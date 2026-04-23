/* 
   TRANSFORMATIONS AND DATA POPULATION
 */

/* 
This script performs:
1. Safe data refresh for dependent tables
2. Date dimension population
3. Aggregated table creation

Important:
fact_sales depends on dim_date via foreign key.
We must handle truncation in correct dependency order.
*/

/* 
We truncate fact table first because it references dimension tables.
Then we truncate dim_date safely.
*/
TRUNCATE TABLE ecommerce.fact_sales;
TRUNCATE TABLE ecommerce.dim_date;

/* 
CASCADE could be used, but explicit order is clearer and safer.
*/

/* 
   DATE DIMENSION POPULATION
*/
/* 
Populate dim_date using generate_series.
This creates a continuous range of dates independent of transactional data.
*/

INSERT INTO ecommerce.dim_date (
    date_key,
    full_date,
    day,
    month,
    year,
    quarter,
    day_of_week,
    day_name,
    is_weekend
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER,
    d,
    EXTRACT(DAY FROM d),
    EXTRACT(MONTH FROM d),
    EXTRACT(YEAR FROM d),
    EXTRACT(QUARTER FROM d),
    EXTRACT(ISODOW FROM d),
    TRIM(TO_CHAR(d, 'Day')),
    CASE 
        WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE
        ELSE FALSE
    END
FROM generate_series(
    '2020-01-01'::DATE,
    '2030-12-31'::DATE,
    INTERVAL '1 day'
) AS d;

/* 
   AGGREGATED TABLE CREATION
*/

/* 
We recreate the aggregated table each run to ensure consistency.
This table summarizes data at grain:
one row per product per day.
*/

DROP TABLE IF EXISTS ecommerce.fact_sales_daily;

CREATE TABLE ecommerce.fact_sales_daily AS
SELECT
    date_key,
    product_key,
    SUM(quantity) AS total_quantity,
    SUM(revenue) AS total_revenue
FROM ecommerce.fact_sales
GROUP BY date_key, product_key;

/* 
   PERFORMANCE OPTIMIZATION
 */

/* 
Index improves query performance on common filters and joins.
*/

CREATE INDEX idx_fact_sales_daily
ON ecommerce.fact_sales_daily (date_key, product_key);
