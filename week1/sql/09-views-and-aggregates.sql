--set a default schema
set search_path to northwind;

/* VIEWS AND AGGREGATES - NORTHWIND
   Goal:
   Create reusable views to simplify complex queries
   and enable consistent aggregation logic
*/



/* 1. Create a view for total sales per customer
   Motivation:
   This calculation is used frequently (customer value),
   so we store it once instead of rewriting the query */

create or replace view customer_total_sales as
select c.customer_id,
       c.company_name,
       SUM(od.quantity * od.unit_price * (1 - od.discount)) as total_sales
from customers c
join orders o ON c.customer_id = o.customer_id
join order_details od ON o.order_id = od.order_id
group by c.customer_id, c.company_name;

select * from customer_total_sales;

/* Logic:
   Aggregates revenue per customer
   Encapsulates business logic inside a reusable object */



/* 2. Retrieve high-value customers (sales > 5000)
   Motivation:
   Segment customers based on value without rewriting aggregation */

select *
from customer_total_sales
where total_sales > 5000;

/* Logic:
   Filtering becomes simple because aggregation is precomputed */



/* 3. Create a view for order-level totals
   Motivation:
   Useful for analyzing order size, trends, and comparisons */

create or replace view order_total_values as
select o.order_id,
       o.customer_id,
       o.order_date,
       SUM(od.unit_price * od.quantity * (1 - od.discount)) as total_value
from orders o
join order_details od using(order_id)
group by o.order_id, o.customer_id, o.order_date;

/* Logic:
   Moves repeated SUM logic into a reusable view */



/* 4. Find orders above average order value
   Motivation:
   Identify unusually large transactions */

select order_id, total_value
from order_total_values
where total_value > (
    select AVG(total_value) from order_total_values
);

/* Logic:
   Combines view + subquery
   Avoids recomputing totals multiple times */



/* 5. Create a view for product sales performance
   Motivation:
   Central place for product-level metrics */

create or replace view product_sales_summary as
select p.product_id,
       p.product_name,
       SUM(od.quantity) as total_quantity_sold,
       SUM(od.unit_price * od.quantity * (1 - od.discount)) as total_revenue
from products p
join order_details od using(product_id)
group by p.product_id, p.product_name;

/* Logic:
   Combines volume and revenue metrics per product */



/* 6. Retrieve products with high revenue but low quantity
   Motivation:
   Identify premium products (high price, low volume) */

select *
from product_sales_summary
where total_revenue > 2000
and total_quantity_sold < 100;

/* Logic:
   Uses aggregated metrics for segmentation */



/* 7. Create a view for supplier performance
   Motivation:
   Evaluate suppliers based on revenue contribution */

create or replace view supplier_performance as
select s.supplier_id,
       s.company_name,
       SUM(od.unit_price * od.quantity * (1 - od.discount)) as total_revenue
from suppliers s
join products p using(supplier_id)
join order_details od using(product_id)
group by s.supplier_id, s.company_name;

/* Logic:
   Links supplier - products - sales */



/* 8. Retrieve suppliers performing above average
   Motivation:
   Identify top suppliers */

select *
from supplier_performance
where total_revenue > (
    select AVG(total_revenue) from supplier_performance
);

/* Logic:
   View simplifies comparison across suppliers */



/* 9. Create a view for shipping performance
   Motivation:
   Analyze shipping efficiency */

create or replace view shipping_performance as
select ship_via,
       COUNT(order_id) as total_orders,
       AVG(freight) as avg_freight,
       AVG(case when shipped_date > required_date then 1 else 0 end) as late_ratio
from orders
group by ship_via;

/* Logic:
   Calculates:
   - total orders
   - average cost
   - percentage of late deliveries */



/* 10. Retrieve reliable shippers (low late ratio)
    Motivation:
    Identify best logistics partners */

select *
from shipping_performance
where late_ratio < 0.1;

/* Logic:
   Filters based on aggregated performance metric */