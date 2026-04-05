-- seta default schema
set search_path to northwind;

/* ANALYTICAL WINDOW PATTERNS - NORTHWIND
   Goal:
   Apply advanced window functions to detect trends,
   compare rows, and analyze behavior over time
*/



/* 1. Compare each order’s freight to the previous order of the same customer
   Motivation:
   Detect changes in shipping cost behavior */

select o.customer_id,
       o.order_id,
       o.order_date,
       o.freight,
       LAG(o.freight) over (partition by o.customer_id order by o.order_date) as previous_freight
from orders o;

/* Logic:
   LAG() accesses the previous row within the same customer
   Enables comparison between consecutive orders */



/* 2. Identify orders where quantity increased compared to previous order for same product
   Motivation:
   Detect growing demand trends */

select od.product_id,
       o.order_date,
       od.quantity,
       LAG(od.quantity) OVER (partition by od.product_id order by o.order_date) as previous_quantity
from order_details od
join orders o using(order_id);

/* Logic:
   Partition by product
   Compare quantity over time using LAG */



/* 3. Dense ranking of customers by total revenue
   Motivation:
   Handle ties properly in ranking */

select customer_id,
       total_revenue,
       DENSE_RANK() over (order by total_revenue desc) as revenue_rank
from (
    select o.customer_id,
           SUM(od.unit_price * od.quantity * (1 - od.discount)) as total_revenue
    from orders o
    join order_details od using(order_id)
    group by o.customer_id
) sub;

/* Logic:
   Subquery calculates revenue
   DENSE_RANK avoids gaps in ranking when ties occur */



/* 4. Percentage contribution of each product to its category revenue
   Motivation:
   Understand product importance within category */

select p.category_id,
       p.product_name,
       SUM(od.unit_price * od.quantity * (1 - od.discount)) as product_revenue,
       SUM(od.unit_price * od.quantity * (1 - od.discount)) 
       / SUM(SUM(od.unit_price * od.quantity * (1 - od.discount))) over (partition by p.category_id)
       as revenue_share
from products p
join order_details od using(product_id)
group by p.category_id, p.product_name;

/* Logic:
   Inner SUM - product revenue
   Outer SUM OVER - total category revenue
   Division gives percentage contribution */



/* 5. Moving average of freight over last 3 orders per shipper
   Motivation:
   Smooth out fluctuations in shipping cost */

select o.ship_via,
       o.order_id,
       o.freight,
       AVG(o.freight) over (
           partition by o.ship_via
           order by o.order_date
           rows between 2 preceding and current row
       ) as moving_avg_freight
from orders o;

/* Logic:
   Window frame defines last 3 rows
   Calculates rolling average per shipper */