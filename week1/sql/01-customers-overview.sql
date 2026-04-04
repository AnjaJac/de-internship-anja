-- Set a default schema
set search_path to northwind;

-- Exploring each table in the schema
-- Motivation:
-- Understand the raw structure of the table
select * 
from categories;

select *
from customer_customer_demo;

select *
from customer_demographics;

select *
from customers;

select * 
from employees;

select * 
from employee_territories;

select *
from territories;

select * 
from region;

select * 
from us_states;

select *
from orders;

select *
from order_details;

select *
from products;

select * 
from shippers;

select *
from suppliers;

-- Selecting and filtering
/* Selecting specific columns
 * Motivation: Reduce unnecessary data transfer
 * Logic: Only required columns are retrieved*/

select customer_id, company_name
from customers; 

/* SIMPLE EQUALITY FILTER
 * Logic: Filters rows where country exactly matches 'USA'*/
select company_name, country, region 
from customers
where country = 'USA';

/* MULTIPLE CONDITIONS (AND)
 * Motivation: Narrow down results using multiple constraints
 * Logic: AND both conditions must be true
 * We get expensive products that are still active*/
select product_id, product_name, unit_price
from products
where unit_price > 50
and discontinued = 0;

/*MULTIPLE CONDITIONS (OR)
 * Motivation: Sometimes we want data matching ANY condition
 * Logic:OR - at least one condition must be true
 * Returns customers from either country*/
select customer_id, company_name, country
from customers
where country = 'Germany'
or country = 'France';

/*USING IN (CLEANER THAN MULTIPLE ORs)
 * Motivation: Cleaner syntax for multiple possible values
 * Logic: Equivalent to multiple ORs
 * Easier to read and maintain */
select customer_id, company_name, country
from customers
where country in ('USA', 'Germany', 'France');

/*RANGE FILTERING (BETWEEN)
 * Motivation: Useful for numeric ranges (prices, dates, etc.)
 * Logic: BETWEEN is inclusive (20 ≤ price ≤ 50) 
 * Cleaner than using >= AND <= */
select product_id, product_name, unit_price
from products
where unit_price between 20 and 50;

/*PATTERN MATCHING (LIKE)
 * Motivation: Search text using patterns (very common in real apps)
 * Logic: 'A%' → starts with letter A
 * % = wildcard (any number of characters)*/
select company_name, contact_name
from customers
where company_name ilike 'A%';
/*Difference between LIKE and ILIKE is that first is case-sensitive patterna matching, 
 * and the latter is case-insensitive*/

/*FINDING NULL VALUES
 * Motivation: NULL handling is critical in real datasets
 * Logic: NULL '=' comparison - must use IS NULL
 * Finds customers with missing region info */
select customer_id, company_name, region 
from customers
where region is null;

/* SORTING RESULTS (ORDER BY)
 * Motivation: Data is more useful when ordered (e.g., top prices)
 * Logic: DESC - highest first,
 * ASC (default) - lowest first */
select product_name, unit_price
from products
order by unit_price desc;

/* LIMITING RESULTS (TOP N)
 * Motivation: Useful for previews or dashboards
 * Logic: First sort, then limit
 * Returns top 5 most expensive products */
select product_name, unit_price 
from products 
order by unit_price desc 
limit 5;

/* FILTERING BY DATE
 * Motivation: Very common in analytics (orders over time)
 * Logic: Filters orders from 1997 onwards
 * Date comparisons work lexicographically in SQL */
select order_id, customer_id, order_date
from orders
where order_date >= '1997-01-01';

/*COMBINING EVERYTHING
 * Motivation: Real queries combine multiple concepts
 * Logic:
 *  Step-by-step:
 *  1. Filter price range
 *  2. Exclude discontinued products
 *  3. Sort descending
 *  4. Take top 10*/
select product_name, unit_price 
from products
where (unit_price between 20 and 50) and (discontinued = 0) -- = is also logical operator
order by unit_price desc
limit 10;

/*BETWEEN (DATE RANGE)
 * Logic: Filters orders within one year
 * Works because dates are comparable values*/
select order_id, order_date
from orders
where order_date between '1997-01-01' and '1997-12-31';

/*TEXT COMPARISON (CASE SENSITIVE DEPENDS ON DB)
 * Logic: Exact string match
 * In PostgreSQL: case-sensitive*/
select contact_name 
from customers 
where contact_name = 'Maria Anders';

/*USING LOWER() FOR CASE-INSENSITIVE SEARCH
 * Logic: Normalize text before comparison
 * Avoids case mismatch issues*/
select contact_name 
from customers 
where lower(contact_name) = 'maria anders';

/* FILTERING WITH CALCULATED EXPRESSION
 * Logic: Computes total inventory value per product
 * Filters high-value inventory items */
select product_name, unit_price, units_in_stock
from products 
where unit_price * units_in_stock > 500;

/*FILTERING WITH NEGATION
 * Logic: Equivalent to:
 * discontinued = 0
 * Demonstrates NOT operator usage
 * selects products that are not discontinued*/
select product_name
from products
where not discontinued = 1;

/* REAL-WORLD FILTER 
 * Logic:
 * Step-by-step:
 *  1. Only shipped orders
 *  2. Shipped after June 1997
 *  3. Only selected key customers */ 
select order_id, customer_id, shipped_date
from orders
where shipped_date is not null 
and shipped_date > '1997-06-01'
and customer_id in ('ALFKI', 'BONAP', 'CACTU');


