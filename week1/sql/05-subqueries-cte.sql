-- set default schema
set search_path to northwind;


/* SUBQUERIES & CTEs - NORTHWIND
   Goal:
   Use subqueries, CTEs, and EXISTS to solve
   more complex analytical problems
*/



/* 1. Products that have never been ordered
   Motivation:
   Identify dead inventory */

select product_id, product_name
from products p
where not exists (
    select 1
    FROM order_details od
    where od.product_id = p.product_id
);

/* Logic:
   NOT EXISTS - no matching rows in order_details - product was never ordered */



/* 2. Customers who have placed at least one large order (> 1000 value)
   Motivation:
   Identify high-value customers */

select distinct o.customer_id
from orders o
where exists (
    select 1
    from order_details od
    where od.order_id = o.order_id
    group by od.order_id
    having SUM(od.unit_price * od.quantity * (1 - od.discount)) > 1000
);

/* Logic: EXISTS ensures at least one qualifying order per customer */



/* 3. Products priced above their category average
   Motivation:
   Detect premium products within categories */

select p.product_name,
       p.unit_price
from products p
where p.unit_price > (
    select AVG(p2.unit_price)
    from products p2
    where p2.category_id = p.category_id
);

/* Logic:
   Correlated subquery:
   average is calculated per category */



/* 4. Customers who ordered ALL products from category_id = 1
   Motivation:
   Identify highly engaged customers */

select c.customer_id
from customers c
where not exists (
    select p.product_id
    from products p
    where p.category_id = 1
    and not exists (
        select 1
        from orders o
        join  order_details od on o.order_id = od.order_id
        where o.customer_id = c.customer_id
        and od.product_id = p.product_id
    )
);

/* Logic:
   Double NOT EXISTS = "for all" condition
   Ensures customer ordered every product in that category */



/* 5. Orders with total value above average order value
   Motivation:
   Identify above-average transactions */

with order_totals as (
    select o.order_id,
           SUM(od.unit_price * od.quantity * (1 - od.discount)) as total_value
    from orders o
    join order_details od on o.order_id = od.order_id
    group by o.order_id
),
avg_total as (
    select AVG(total_value) as avg_value
    from order_totals
)
select order_id, total_value
from order_totals
where total_value > (select avg_value from avg_total);

/* Logic:
   Step 1: compute order totals
   Step 2: compute average
   Step 3: filter above average */



/* 6. Employees who have never handled an order
   Motivation:
   Detect inactive employees */

select employee_id, first_name, last_name
from employees e
where not exists (
    select 1
    from orders o
    where o.employee_id = e.employee_id
);

/* Logic:
   No matching order - employee never handled orders */



/* 7. Suppliers whose products are all above average price
   Motivation:
   Identify consistently premium suppliers */

select supplier_id, company_name
from suppliers s
where not exists (
    select 1
    from products p
    where p.supplier_id = s.supplier_id
    and p.unit_price <= (
        select AVG(unit_price) from products
    )
);

/* Logic:
   If ANY product is below average → supplier excluded
   Remaining suppliers - all products above average */



/* 8. Customers who have only ordered discounted products
   Motivation:
   Detect discount-driven customers */

select customer_id
from customers c
where not exists (
    select 1
    from orders o
    join order_details od using(order_id)
    where o.customer_id = c.customer_id
    and od.discount = 0
);

/* Logic:
   No full-price purchases - always discounted */



/* 9. Most recent order per customer
   Motivation:
   Understand latest activity */

with latest_orders as (
    select customer_id,
           MAX(order_date) AS last_order_date
    from orders
    group by customer_id
)
select o.customer_id,
       o.order_id,
       o.order_date
from orders o
join  latest_orders lo
  on o.customer_id = lo.customer_id
 and o.order_date = lo.last_order_date;

/* Logic:
   Find max date per customer, then join back */



/* 10. Most expensive product per supplier
   Motivation:
   Identify top-priced items per supplier */

select p.product_id,
       p.product_name,
       p.unit_price
from products p
where p.unit_price = (
    select MAX(p2.unit_price)
    from products p2
    where p2.supplier_id = p.supplier_id
);

/* Logic:
   Correlated subquery finds max price per supplier */