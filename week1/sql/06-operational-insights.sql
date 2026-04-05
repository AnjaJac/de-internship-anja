-- set default schema
set search_path to northwind;

/* OPERATIONAL INSIGHTS - NORTHWIND
   Goal:
   Analyze logistics, geography, and operations
   using advanced joins, subqueries, and CTEs
*/



/* 1. Number of territories per region
   Motivation:
   Understand geographic distribution complexity */

select r.region_description,
       COUNT(t.territory_id) as territory_count
from region r
join territories t using(region_id)
group by r.region_description;



/* 2. Employees managing multiple territories
   Motivation:
   Identify employees with broader responsibility */

select et.employee_id,
       COUNT(et.territory_id) as territory_count
from employee_territories et
group by et.employee_id
having COUNT(et.territory_id) > 1;



/* 3. Orders handled per region (via employee territories)
   Motivation:
   Map operational workload geographically */

select r.region_description,
       COUNT(o.order_id) as total_orders
from orders o
join employees e using(employee_id)
join employee_territories et using(employee_id)
join territories t using(territory_id)
join region r using(region_id)
group by r.region_description;



/* 4. Shippers with above-average freight cost
   Motivation:
   Identify expensive shipping partners */

select s.company_name,
       AVG(o.freight) as avg_freight
from shippers s
join orders o on s.shipper_id = o.ship_via
group by s.company_name
having AVG(o.freight) > (
    select AVG(freight) from orders
);



/* 5. Territories with no assigned employees
   Motivation:
   Detect uncovered regions */

select t.territory_id,
       t.territory_description
from territories t
where not exists (
    select 1
    from employee_territories et
    where et.territory_id = t.territory_id
);



/* 6. Regions where all territories have at least one employee
   Motivation:
   Identify fully covered regions */

select r.region_description
from region r
where not exists (
    select 1
    from territories t
    where t.region_id = r.region_id
    and not exists (
        select 1
        from employee_territories et
        where et.territory_id = t.territory_id
    )
);



/* 7. Shippers that handled orders to more than 3 different countries
   Motivation:
   Measure shipping reach */

select s.company_name,
       COUNT(distinct o.ship_country) as country_count
from shippers s
join orders o on s.shipper_id = o.ship_via
group by s.company_name
having COUNT(distinct o.ship_country) > 3;



/* 8. Employees working in regions with high order volume (> 100 orders)
   Motivation:
   Identify employees in busy regions */

with region_orders AS (
    select r.region_id,
           COUNT(o.order_id) as total_orders
    from orders o
    join employees e using(employee_id)
    join employee_territories et using(employee_id)
    join territories t using(territory_id)
    join region r using(region_id)
    group by r.region_id
)
select distinct e.employee_id, e.last_name
from employees e
join employee_territories et using(employee_id)
join territories t using(territory_id)
join region_orders ro using(region_id)
where ro.total_orders > 100;



/* 9. Orders shipped by the least-used shipper
   Motivation:
   Identify underutilized logistics partner */

with shipper_usage as (
    select ship_via,
           COUNT(order_id) as total_orders
    from orders
    group by ship_via
)
select o.order_id, s.company_name
from orders o
join shippers s ON o.ship_via = s.shipper_id
where o.ship_via = (
    select ship_via
    from shipper_usage
    order by total_orders asc    -- another way of finding a minimum
    limit 1
);



/* 10. Territories contributing to above-average revenue
    Motivation:
    Identify high-performing geographic areas */

with territory_revenue as (
    select t.territory_id,
           SUM(od.unit_price * od.quantity * (1 - od.discount)) as revenue
    from orders o
    join order_details od using(order_id)
    join employees e using(employee_id)
    join employee_territories et using(employee_id)
    join territories t using(territory_id)
    group by t.territory_id
)
select territory_id, revenue
FROM territory_revenue
where revenue > (
    select AVG(revenue) from territory_revenue
);



/* 11. Shippers that never handled late deliveries
    Motivation:
    Identify reliable shipping partners */

select s.company_name
FROM shippers s
where not exists (
    select 1
    from orders o
    where o.ship_via = s.shipper_id
    and o.shipped_date > o.required_date
);



/* 12. Regions with customers but no orders
    Motivation:
    Detect untapped markets */

select distinct r.region_description
from region r
join territories using(region_id)
join employee_territories et using(territory_id)
join employees e using(employee_id)
join orders o using(employee_id)
right join customers c on c.country = o.ship_country
where o.order_id is null;

