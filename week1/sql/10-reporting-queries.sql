-- set a default schema
set search_path to northwind;

/* REPORTING QUERIES - NORTHWIND
   Goal:
   Generate unique business insights by combining
   all SQL concepts in non-trivial ways
*/



/* 1. Customers who rely heavily on a single product
   Motivation:
   Identify customers with low product diversity */

with customer_product_counts as (
    select o.customer_id,
           od.product_id,
           COUNT(*) as product_orders
    from orders o
    join order_details od using(order_id)
    group by o.customer_id, od.product_id
),
total_orders as (
    select customer_id,
           SUM(product_orders) as total_orders
    from customer_product_counts
    group by customer_id
)
select cpc.customer_id,
       cpc.product_id,
       cpc.product_orders,
       cpc.product_orders * 1.0 / t.total_orders as dependency_ratio
from customer_product_counts cpc
join total_orders t using(customer_id)
where cpc.product_orders * 1.0 / t.total_orders > 0.5;

/* Logic:
   Calculates how much a customer depends on one product
   High ratio  risky dependency */



/* 2. Orders where one product dominates the basket (>70% of value)
   Motivation:
   Detect skewed orders dominated by a single item */

with order_product_values as (
    select od.order_id,
           od.product_id,
           od.unit_price * od.quantity * (1 - od.discount) as product_value
    from order_details od
),
order_totals as (
    select order_id,
           SUM(product_value) as total_value
    from order_product_values
    group by order_id
)
select opv.order_id,
       opv.product_id,
       opv.product_value,
       opv.product_value / ot.total_value as share
from order_product_values opv
join order_totals ot on opv.order_id = ot.order_id
where opv.product_value / ot.total_value > 0.7;

/* Logic:
   Compares product contribution to total order value */



/* 3. Employees handling increasingly complex orders (more products per order)
   Motivation:
   Measure growth in operational complexity */

with order_complexity as (
    select o.order_id,
           o.employee_id,
           COUNT(DISTINCT od.product_id) as product_count
    from orders o
    join order_details od ON o.order_id = od.order_id
    group by o.order_id, o.employee_id
)
select employee_id,
       order_id,
       product_count,
       LAG(product_count) over (partition by employee_id order by order_id) as previous_complexity
from order_complexity;

/* Logic:
   Uses LAG to compare order complexity over time */



/* 4. Customers ordering from increasingly distant suppliers (cross-country behavior)
   Motivation:
   Detect expansion in customer sourcing patterns */

select o.customer_id,
       o.order_id,
       o.ship_country,
       s.country as supplier_country,
       case when o.ship_country <> s.country then 1 else 0 end as cross_country_flag
from orders o
join order_details od on o.order_id = od.order_id
join products p on od.product_id = p.product_id
join suppliers s on p.supplier_id = s.supplier_id;

/* Logic:
   Compares customer location with supplier location */



/* 5. Territories with highly concentrated employee workload
   Motivation:
   Detect imbalance in resource allocation */

select t.territory_id,
       COUNT(o.order_id) as total_orders,
       COUNT(distinct e.employee_id) as employee_count,
       COUNT(o.order_id) * 1.0 / COUNT(distinct e.employee_id) as orders_per_employee
from territories t
join employee_territories et using(territory_id)
join employees e using(employee_id)
join orders o using(employee_id)
group by t.territory_id;

/* Logic:
   Measures workload concentration */



/* 6. Shippers used inconsistently across countries
   Motivation:
   Detect lack of standardization in logistics */

select o.ship_country,
       s.company_name,
       COUNT(o.order_id) as usage_count,
       COUNT(o.order_id) * 1.0 /
       SUM(COUNT(o.order_id)) over (partition by o.ship_country) as usage_share
from orders o
join shippers s on o.ship_via = s.shipper_id
group by o.ship_country, s.company_name;

/* Logic:
   Calculates share of each shipper per country */



/* 7. Customers whose order values are highly volatile
   Motivation:
   Identify inconsistent purchasing behavior */

with order_values as (
    select o.order_id,
           o.customer_id,
           SUM(od.unit_price * od.quantity * (1 - od.discount)) as total_value
    from orders o
    join order_details od on o.order_id = od.order_id
    group by o.order_id, o.customer_id
)
select customer_id,
       MAX(total_value) - MIN(total_value) as value_range
from order_values
group by customer_id
having MAX(total_value) - MIN(total_value) > 500;

/* Logic:
   Measures spread between smallest and largest order */