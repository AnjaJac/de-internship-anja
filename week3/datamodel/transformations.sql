/*
   DATE DIMENSION POPULATION
*/

/* 
We truncate fact table first because it references dimension tables.
Then we truncate dim_date safely.
*/
TRUNCATE TABLE ecommerce.fact_sales;
TRUNCATE TABLE ecommerce.dim_date;


/* Populate dim_date with a range of dates */
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
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_key,
    d AS full_date,
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
   AGGREGATED TABLE: DAILY PRODUCT SALES
 */

/* Drop table if it exists (safe re-run) */
DROP TABLE IF EXISTS ecommerce.fact_sales_daily;

/* Create aggregated table at grain:
   one row per product per day */
CREATE TABLE ecommerce.fact_sales_daily AS
SELECT
    date_key,
    product_key,
    SUM(quantity) AS total_quantity,
    SUM(revenue) AS total_revenue
FROM ecommerce.fact_sales
GROUP BY date_key, product_key;



/* 
   INDEX FOR PERFORMANCE
 */

CREATE INDEX idx_fact_sales_daily
ON ecommerce.fact_sales_daily (date_key, product_key);
