-- set a default schema
set search_path to northwind;

/*FILTERING CONDITIONS - NORTHWIND
 * Goal:
 * Apply complex filtering across multiple tables
 * to extract non-trivial business insights
 */

/*1. Orders with unusually high discount (> 20%)
 * Motivation: Detect aggressive discounting patterns
 * Logic: Filters line items where discount exceeds 20%
*/
select o.order_id, od.product_id, od.discount
from orders o
join order_details od using(order_id)
where od.discount > 0.2;

/* 2. Customers who only ever ordered 1 product type per order
 * Motivation: Identify simple vs complex purchasing behavior
 * Logic:
 *  Count distinct products per order
 *  Keep only single-product orders
*/
select o.order_id, 
       o.customer_id,
       count(distinct od.product_id) as unique_products
from orders o 
join order_details od using(order_id)
group by o.order_id, o.customer_id 
having count(distinct od.product_id) = 1;

/* 3. Products never ordered in large quantities (>50 units in a single order)
 * Motivation: Identify products that are never bulk-purchased
 * Logic:
 *  For each product, check its largest order quantity
 *  Keep those that never exceeded 50 units
*/
select p.product_id,
       p.product_name
from products p 
join order_details od using(product_id)
group by p.product_id, p.product_name 
having MAX(od.quantity)<= 50;

/* 4. Orders where total discount amount exceeded total freight
 * Motivation: Detect orders where discounts outweigh shipping costs
 * Logic: Compare aggregated discount value vs freight per order
*/
select o.order_id,
       SUM(od.unit_price * od.quantity * od.discount) as total_discount,
       o.freight
from orders o
join order_details od using(order_id)
group by o.order_id, o.freight 
having SUM(od.unit_price * od.quantity * od.discount) > o.freight;

/* 5. Customers who ordered products from more than 3 different suppliers
 * Motivation: Identify diverse purchasing behavior
 * Logic:
 *  Trace supplier through products
 *  Count distinct suppliers per customer
*/

select o.customer_id,
       count(distinct p.supplier_id) as supplier_count
from orders o 
join order_details od using(order_id) 
join products p using(product_id)
group by o.customer_id
having count(distinct p.supplier_id) > 3;

/* 6. Employees who handled orders with average item quantity > 20
 * Motivation: Detect employees working on bulk orders
 * Logic: Average quantity per line handled by employee
*/
select e.employee_id,
       AVG(od.quantity) as avg_quantity
from employees e
join orders o using(employee_id)
join order_details od using(order_id)
group by e.employee_id
having AVG(od.quantity) > 20;

/* 7. Categories where no product costs less than 10
 * Motivation: Identify exclusively mid/high-priced categories
 * Logic: Minimum price per category must be ≥ 10
*/
select c.category_id,
       c.category_name,
       MIN(p.unit_price )as product_cost
from categories c
join products p using(category_id)
group by c.category_id, c.category_name
having MIN(p.unit_price ) >= 10;

/* 8. Orders containing both cheap (<10) AND expensive (>100) products
 * Motivation: Detect mixed-value baskets
 * Logic: Use conditional aggregation to check presence of both extremes 
*/
select o.order_id,
       MIN(p.unit_price ) as cheapest_product_in_order,
       MAX(p.unit_price ) as most_expensive_in_order
from orders o
join order_details od using(order_id)
join products p using(product_id)
group by o.order_id
having (  
    SUM(case when p.unit_price < 10 then 1 else 0 end) > 0
and SUM(case when p.unit_price > 100 then 1 else 0 end) > 0);

/* 9. Suppliers whose products were never discounted
 * Motivation:
 * Identify premium/no-discount suppliers
 * Logic:
 * If max discount is 0 - never discounted
*/
select s.company_name
from suppliers s
join products p using(supplier_id)
join order_details od using(product_id)
group by s.company_name
having MAX(od.discount) = 0;

/* 10. Customers with decreasing order frequency (less than 3 orders total)
 * Motivation:
 * Identify low-engagement customers
 * Logic:
 * Simple segmentation: low-frequency customers 
*/

select c.company_name,
       count(o.order_id) as num_of_orders
from customers c
join orders o using(customer_id)
group by c.company_name 
having count(o.order_id) < 3;
having
