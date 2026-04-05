-- set a default schema
set search_path to northwind;

/* WINDOW FUNCTIONS - NORTHWIND
   Goal:
   Use window functions for ranking, running totals,
   and partitioned analysis across business entities
 */



/* 1. Rank products by price within each category
   Motivation:
   Identify most expensive products per category */

select p.category_id,
       p.product_name,
       p.unit_price,
       RANK() over (partition by p.category_id order by p.unit_price desc) as price_rank
from products p;



/* 2. Running total of orders per customer
   Motivation:
   Track customer spending over time */

select o.customer_id,
       o.order_id,
       o.order_date,
       SUM(o.freight) over (partition by o.customer_id order by o.order_date) as running_freight
from orders o;



/* 3. Row number of orders per employee
   Motivation:
   Sequence employee activity */

select employee_id,
       order_id,
       order_date,
       ROW_NUMBER() over (partition by employee_id order by order_date) as order_sequence
from orders;



/* 4. Average product price within each supplier
   Motivation:
   Compare product price to supplier average */

select p.product_name,
       p.unit_price,
       AVG(p.unit_price) over (partition by p.supplier_id) as avg_supplier_price
from products p;



/* 5. Compare each order freight to average freight per country
   Motivation:
   Detect unusually expensive shipments */

select ship_country,
       order_id,
       freight,
       AVG(freight) over (partition by ship_country) as avg_country_freight
from orders;



/* 6. Rank employees by number of orders handled
   Motivation:
   Identify most active employees */

select e.employee_id,
       COUNT(o.order_id) as total_orders,
       RANK() over (order by COUNT(o.order_id) desc) as employee_rank
from employees e
join orders o using(employee_id)
group by e.employee_id;



/* 7. Running quantity sold per product
   Motivation:
   Track product demand over time */

select od.product_id,
       o.order_date,
       SUM(od.quantity) over (partition by od.product_id order by o.order_date) as running_quantity
from order_details od
join orders o using(order_id);



/* 8. Rank suppliers by total revenue
   Motivation:
   Identify top-performing suppliers */

select s.company_name,
       SUM(od.unit_price * od.quantity * (1 - od.discount)) as total_revenue,
       RANK() over (order by SUM(od.unit_price * od.quantity * (1 - od.discount)) desc) as supplier_rank
from suppliers s
join products p using(supplier_id)
join order_details od using(product_id)
group by s.company_name;



/* 9. Row number of customers within each country
   Motivation:
   Organize customers geographically */

select customer_id,
       country,
       ROW_NUMBER() over (partition by country order by customer_id) as country_row
from customers;



/* 10. Average quantity per order compared to overall average
    Motivation:
    Understand order size differences */

select o.order_id,
       AVG(od.quantity) as avg_quantity,
       AVG(AVG(od.quantity)) over () as overall_avg_quantity
from orders o
join order_details od using(order_id)
group by o.order_id;



/* 11. Rank territories by number of assigned employees
    Motivation:
    Identify heavily managed areas */

select t.territory_id,
       COUNT(et.employee_id) as employee_count,
       RANK() over (order by COUNT(et.employee_id) desc) as territory_rank
from territories t
join employee_territories et using(territory_id)
group by t.territory_id;



/* 12. Rank shippers by total freight handled
    Motivation:
    Compare logistics partner performance */

select s.company_name,
       SUM(o.freight) as total_freight,
       RANK() over (order by SUM(o.freight) desc) as shipper_rank
from shippers s
join orders o on s.shipper_id = o.ship_via
group by s.company_name;