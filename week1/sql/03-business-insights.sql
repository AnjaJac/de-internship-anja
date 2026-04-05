-- set a default schema
set search_path to northwind;

/*BUSINESS INSIGHTS - NORTHWIND
 * Goal:
 * Combine tables and use different join types
 * to extract meaningful business insights
 * Includes INNER, LEFT, RIGHT, CROSS joins
 * and some aggregations
 */

/* 1. All customers and their orders (including those with no orders)
 * Motivation: Identify customers who never placed an order
 * Logic: LEFT JOIN keeps ALL customers
 * Orders will be NULL if none exist
 */
select c.customer_id, c.company_name, o.order_id
from customers c
left join orders o using(customer_id);

/* 2. Customers without orders
 * Motivation: Find inactive customers
 * Logic: After LEFT JOIN, filter rows where no match exists
*/
--checking
select c.company_name, o.order_id
from customers c 
left join orders o using(customer_id); -- in order to see if those companies exist

select c.company_name
from customers c
left join orders o using(customer_id)
where o.order_id is null;

/* 3. All orders and their customers (RIGHT JOIN)
 * Motivation: Show all orders even if customer data is missing
 * Logic:
 *  RIGHT JOIN keeps ALL orders
 *  Rarely used in practice, but good to understand
*/
select c.company_name, o.order_id
from customers c
right join orders o using(customer_id);

/* 4. Total number of orders per customer (including zero)
 * Motivation: Customer activity analysis
 * Logic:
 * LEFT JOIN ensures customers with 0 orders are included
 * COUNT ignores NULL values
*/
select c.company_name,
       count(o.order_id)
from customers c
left join orders o using(customer_id)
group by c.company_name;            -- we can see that the query does what it was supposed to do in ex. 2


/*5. Total revenue per customer (including those with no purchases)
 * Motivation: Identify high-value vs inactive customers 
 * Logic:
 * Multi-level LEFT JOIN keeps all customers
 * Revenue will be NULL for inactive ones
*/
select c.company_name,
       SUM(od.unit_price * od.quantity *(1 - od.discount)) as total_revenue
from customers c
left join orders o using(customer_id)
left join order_details od using(order_id)
group by c.company_name;     -- similar assignment as in 02 script

/*6. Products that have never been ordered
 * Motivation: Detect unsold inventory
 * Logic: If no match in order_details - never sold 
*/
select p.product_name, p.product_id
from products p
left join order_details od using(product_id)
where od.order_id is null; -- products that have never been ordered do not exist

/*7. Employees and total revenue they generated
 * Motivation: Measure employee performance
 * Logic: INNER JOIN - only employees with orders included
*/
select e.employee_id,
      SUM(od.unit_price * od.quantity *(1 - od.discount)) as revenue_employee
from employees e 
join orders o using(employee_id)
join order_details od using(order_id)
group by employee_id;

/*8. Cross join: all combinations of products and categories
 *  Motivation: Understand theoretical combinations (rare but useful conceptually)
 * Logic: 
 * Every product paired with every category
 *  Total rows = products × categories 
*/
select * 
from products p
cross join categories c;

--the same result we get if we write like this
select * 
from products, categories;

/*9. Cross join with filter (simulate matching)
 * Motivation: Show how CROSS JOIN + WHERE can behave like INNER JOIN 
 * Logic:
 *  CROSS JOIN creates all combinations
 *  WHERE filters to matching ones
 *  Equivalent to INNER JOIN
*/
select p.product_name, p.product_id, c.category_name, c.category_id
from products p, categories c
where p.category_id = c.category_id;

/*10. Suppliers and total revenue of their products
 *  Motivation: Evaluate supplier importance
 * Logic:
 *  LEFT JOIN ensures all suppliers are included
 *  Even those with no sales
*/
select s.company_name,
       SUM(od.unit_price * od.quantity *(1 - od.discount)) as revenue_per_supplier
from suppliers s 
left join products p using(supplier_id)
left join order_details od using(product_id)
group by s.company_name;
