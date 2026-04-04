--Set a default schema
set search_path to northwind;

/* AGGREGATIONS & GROUPING - NORTHWIND 
 * Goal:
 *  Learn how to summarize data and extract insights
 *  using GROUP BY, JOIN, and HAVING
 */

/* 1. Total revenue per product
 *  Motivation:
 *  Understand which products generate the most money 
 * Logic:
 *  Revenue = price * quantity * (1 - discount)
 *  Aggregated per product */
select p.product_name, sum(od.unit_price * od.quantity * (1 - od.discount)) as "Total Revenue"
from order_details od
join products p using(product_id)
group by p.product_name;
 --used USING() because the column name is the same in both tables

/* 2. Number of orders handled by each employee
 * Motivation:
 * Measure employee workload
 * Logic: Count how many orders each employee processed */
select e.employee_id, e.last_name, 
	   count(o.order_id) as total_orders
from employees e
join orders o using(employee_id)
group by e.employee_id, e.last_name;

/* 3. Total revenue per customer
 *  Motivation:
 *  Identify most valuable customers
 * Logic: Sum revenue across all orders per customer */
select o.customer_id, c.company_name,
       sum(od.unit_price * od.quantity * (1 - od.discount)) as total_spent
from customers c 
join orders o using(customer_id)
join order_details od using(order_id)
group by o.customer_id, c.company_name; -- did a double join in order to get a company name

/*4. Customers with total spending above 5000
 *  Motivation: Segment high-value customers 
 * Logic: HAVING filters AFTER aggregation */
select o.customer_id, c.company_name,
       SUM(od.unit_price * od.quantity * (1 - od.discount)) as total_spent
from customers c 
join orders o using(customer_id)
join order_details od using(order_id)
group by o.customer_id, c.company_name
having SUM(od.unit_price * od.quantity * (1 - od.discount)) >= 5000
order by total_spent desc; -- we can use alias because of logical order of execution

/* 5. Average product price per category
 *  Motivation: Understand pricing differences across categories 
 *  Logic: Groups products by category and averages price */
select c.category_name,
       AVG(p.unit_price) as average_unit_price
from categories c
join products p using(category_id)
group by c.category_name;

/* 6. Number of products per supplier
 * Motivation: Understand supplier contribution 
 * Logic: Count how many products each supplier provides*/

select s.company_name,
       COUNT(p.product_id) as product_count
from products p
join suppliers s using(supplier_id)
group by s.company_name;

/*7. Total quantity sold per category
 * Motivation: Identify most popular product categories
 *  Logic: 
 * Join chain: Order Details - Products - Categories*/
select c.category_name,
       SUM(od.quantity) as sold_per_category
from order_details od
join products p using(product_id)
join categories c using(category_id)
group by c.category_name;

/* 8. Average discount per product
 * Motivation: Analyze discounting strategy
 * Logic: Average discount applied per product */
select p.product_name,
       AVG(od.discount) * 100 as "Average Discount" --average discount percentages
from order_details od
join products p using(product_id)
group by p.product_name
order by "Average Discount" desc;

/* 9. Orders per shipper
 * Motivation: Measure shipping company usage
 * Logic: Ship-via links Orders - Shippers */
select s.company_name,
       count(o.order_id) as num_of_orders
from orders o
join shippers s on o.ship_via = s.shipper_id
group by s.company_name;

/* 10. Total freight cost per shipper
 * Motivation: Analyze shipping expenses
 * Logic: Sum freight costs per shipping company */
select s.company_name,
       SUM(o.freight) as total_freight_cost
from orders o
join shippers s on o.ship_via = s.shipper_id
group by s.company_name;

/* 11. Number of customers per country
 * Motivation: Understand geographic distribution 
 * Logic: Simple grouping without joins */
select country,
       count(*) as num_customers_per_country -- generally more efficient and prefered way of counting rows
from customers 
group by country;

/* 12. Employees hired per year
 * Motivation: Analyze hiring trends
 * Logic: Extract year from date and group */
select employee_id, first_name, last_name,
      extract(year from hire_date) as hire_year
from employees
group by employee_id, first_name, last_name;

/* 13. Average order value per order
 * Motivation: Understand order size
 * Logic: Average value of line items per order */
select o.order_id,
       AVG(od.unit_price * od.quantity * (1 - od.discount)) as average_order_value
from orders o
join order_details od using(order_id)
group by o.order_id;

/* 15. Total stock per category
 * Motivation:
 * Inventory analysis
 * Logic: Aggregate stock levels by category */
select c.category_name,
       SUM(p.units_in_stock) as "In stocks"
from categories c
join products p using(category_id)
group by c.category_name;

/* 16. Suppliers with more than 3 products
 * Motivation: Identify major suppliers
 * Logic: Filter grouped results using HAVING */
select s.company_name,
       count(p.product_id) as num_of_products
from suppliers s
join products p using(supplier_id)
group by s.company_name
having count(p.product_id) > 3;

