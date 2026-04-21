# Data Warehousing: OLTP vs OLAP

## Why You Should NOT Run Analytics on a Production Database

Running complex analytical queries directly on a live production database (OLTP) is a dangerous practice that can severely impact business operations. Separate systems (like an OLAP Data Warehouse) are strictly needed to ensure that heavy data analysis does not degrade the performance of the transactional system.

**Impact of running analytical queries on an OLTP database:**
* **System Slowdown:** Analytical queries often require scanning millions of rows and performing massive aggregations. This consumes significant CPU and memory, starving the primary transactional processes and causing severe latency for end-users.
* **Table Locking:** Production databases use locks to maintain data integrity during transactions. Long-running analytical queries can hold read locks for extended periods, blocking write operations (inserts, updates, deletes) and causing transaction queues to pile up.
* **Application Crashes:** In severe cases, the resource exhaustion caused by heavy analytics can crash the live application entirely, leading to system downtime, lost revenue, and disrupted user experience.
* **Opposing Optimizations:** Production DBs are indexed and optimized for quick, single-row read/write operations. Analytics require entirely different optimization strategies (like column-oriented storage) to be efficient.

---

## OLAP vs. OLTP Comparison

**Online Transaction Processing (OLTP)** systems are built to reliably and efficiently manage real-time transactional data in high volumes. 
**Online Analytical Processing (OLAP)** systems are designed to combine, group, and analyze massive volumes of historical data from multiple sources (including OLTPs) to support business decision-making.

| Criteria | OLTP (Online Transaction Processing) | OLAP (Online Analytical Processing) |
| :--- | :--- | :--- |
| **Purpose** | Manage and process real-time transactions. | Analyze large volumes of data to support decision-making. |
| **Data Source** | Real-time and transactional data from a single source/application. | Historical and aggregated data from multiple sources. |
| **Data Structure** | Relational databases (row-oriented). | Multidimensional (data cubes) or relational databases (columnar). |
| **Data Model** | Normalized or denormalized models optimized for fast writes. | Star schema, snowflake schema, or other analytical models optimized for heavy reads. |
| **Volume of Data** | Comparatively smaller storage requirements (Gigabytes - GB). | Massive storage requirements (Terabytes - TB to Petabytes - PB). |
| **Response Time** | Extremely fast, typically in milliseconds. | Longer response times, typically in seconds or minutes. |
| **Example Applications** | Processing payments, customer data management, order processing, inventory updates. | Analyzing trends, predicting customer behavior, identifying profitability, financial reporting. |

---

## Example Use Case: Large Retail Company

To understand how these two systems work together in an ecosystem, consider a retail company operating hundreds of stores:

* **OLTP (The Day-to-Day):** The company uses an OLTP system to process real-time store transactions. When a customer buys a product, the system instantly updates inventory levels, manages payment information, and tracks loyalty points. Each store connects to this central database, requiring millisecond response times so checkout lines keep moving.
* **OLAP (The Big Picture):** Separately, the company's business analysts use an OLAP system to generate reports. They run complex queries across massive volumes of historical data (originally collected by the OLTP) to identify sales trends, customer demographics, and popular products over specific time periods. Because this happens in the OLAP environment, the intensive queries do not slow down the cash registers in the stores.
week3/notes/week3.md
Displaying week3/notes/week3.md.

## Fact Tables

### Definition
A Fact Table is the primary table in a dimensional model where the numerical performance measurements of a business process are stored.  

It represents a **"verb" or event**, such as:
- a sale
- a login
- a temperature reading  

It sits at the **center of a star schema**, surrounded by dimension tables.

---

### Content and Measures

#### Foreign Keys (FK)
- Columns that link the fact table to dimension tables  
- Example: `product_key`, `date_key`, `customer_key`  
- Enable joining with dimensions 

#### Measures (Facts)
- Quantitative, numeric values  
- Can be aggregated (SUM, AVG, COUNT)  
- Answer questions like:
  - "How much?"
  - "How many?" 

#### Degenerate Dimensions
- Identifiers stored directly in the fact table  
- No corresponding dimension table  
- Example: `order_id`, `invoice_number` 

---

### Common Fact Types

#### Additive Facts
- Can be summed across all dimensions  
- Example: total sales amount 

#### Semi-Additive Facts
- Can be summed across some dimensions, but not all  
- Typically **not additive over time**  
- Example: account balance 

#### Non-Additive Facts
- Cannot be meaningfully summed  
- Usually ratios or percentages  
- Example: profit margin %, unit price 

#### Factless Fact Tables
- Contain only foreign keys (no numeric measures)  
- Used to track event occurrence  
- Example: student attendance 

---

### Notes / Understanding

- Fact tables capture **events**, not descriptions  
- They are designed for **analysis and aggregation**  
- Always tied to a defined **grain** (level of detail)

## Dimension Tables

### Definition
A **Dimension Table** provides the "context" or the "who, what, where, when, and why" of a business process. While the fact table contains the numbers, the dimension tables contain the descriptive text that allows us to filter, group, and label those numbers in a report.

### Content and Attributes
* **Primary Key (PK):** A unique identifier for each row (usually a **Surrogate Key**, which is a simple integer). 
* **Attributes:** Textual fields that describe the dimension (e.g., `Product Name`, `Color`, `Size`). These are often verbose and used as headers in reports. 
* **Hierarchies:** Attributes that represent levels of a category, like `City > State > Country`. 

### Example: Product Dimension
| Product_SK (PK) | SKU | Product Name | Category | Brand | Color |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 501 | CR-99 | Mountain Bike | Sports | Trek | Blue |

## Grain (Crucial Concept)

### Definition
The **Grain** is the fundamental definition of what a single row in a fact table represents. It is the level of detail at which the data is captured. You must "declare the grain" before you define your dimensions or facts.

### Importance
* **Consistency:** Every measurement in the table is at the same level of detail. 
* **Accuracy:** Prevents double-counting during data aggregation. 
* **Dimension Selection:** Directly dictates which dimensions can be associated with the fact table. 

### Example: "One row per order item"
If a customer buys a loaf of bread and a carton of milk, this grain results in **two rows** in the fact table (one for each item), allowing for precise analysis of product-level trends.

## Surrogate Keys

### Definition
A **Surrogate Key** is an internally generated, meaningless integer used as the Primary Key for a dimension table. It exists solely to identify a record within the data warehouse.

### Why use them over Natural Keys?
* **System Decoupling:** Protects the warehouse from changes or recycling of IDs in source systems. 
* **Historical Tracking:** Essential for **Slowly Changing Dimensions**, allowing one natural entity to have multiple records representing different points in time. 
* **Query Performance:** Joins on integers are much faster than joins on text-based natural keys. 
* **Consolidation:** Easily handles overlapping natural keys when merging data from multiple sources. 

## E-commerce Scenario Definition

### Scenario Description

We model an e-commerce business that sells products across multiple categories. Customers place orders, and each order can contain one or more products.  

The goal of this data model is to support **analytical queries** related to:
- sales performance
- customer behavior
- product trends  

This model will be used in an OLAP/data warehouse context, not for transactional operations.

---

### Core Business Questions

To design an effective data model, we first define the key business questions the system must answer.

#### 1. Sales Performance
**Question:**  
How much revenue do we generate per day per product?

**Why this matters:**  
This question enables tracking overall business performance over time and identifies which products contribute the most to revenue. It introduces the need for:
- a time dimension
- a product dimension
- an aggregatable revenue metric  

---

#### 2. Customer Behavior
**Question:**  
What is the total revenue and number of orders per customer?

**Why this matters:**  
This allows the business to evaluate customer value and identify high-value customers. It introduces:
- a customer dimension  
- the need to aggregate both revenue and order counts  

---

#### 3. Product Trends
**Question:**  
Which products sell the most (by quantity and revenue) over time?

**Why this matters:**  
This supports trend analysis and inventory/business decisions. It reinforces:
- product-level analysis  
- time-based aggregation  
- use of both quantity and revenue measures  

---

#### 4. Order Behavior (AOV)
**Question:**  
What is the average order value (AOV) over time?

**Why this matters:**  
This introduces order-level analysis and helps measure purchasing patterns. It requires:
- tracking order identifiers  
- calculating derived metrics (revenue / number of orders)  
- understanding customer purchasing behavior  

---

### Modeling Insight

Although these questions cover different perspectives, they all revolve around a single core business event:

> A customer purchasing a product.

This insight allows us to design a **single fact table** that can answer all questions by combining:
- product data  
- customer data  
- time data  
- order-level information  

This alignment ensures the model is:
- consistent  
- scalable  
- capable of supporting multiple analytical use cases  

## Fact Table Grain

### Definition of Grain

The grain defines the level of detail represented by each row in the fact table. It must be explicitly defined before designing the schema.

### Chosen Grain

> Each row represents a single product within a customer order (one order item).

### Why this grain was chosen

This grain aligns with the core business questions and enables flexible analysis across multiple dimensions:

- **Sales performance:**  
  Allows aggregation of revenue by product and time  

- **Customer behavior:**  
  Enables tracking of purchases at the customer level  

- **Product trends:**  
  Supports analysis of quantity and revenue per product over time  

- **Order behavior (AOV):**  
  Enables calculation of average order value by grouping order items by order  

### Key Implications

- A single order with multiple products will generate multiple rows  
- Revenue and quantity are recorded at the most detailed level  
- All higher-level metrics (e.g., total revenue, AOV) are derived through aggregation  

### Summary

This grain provides the right balance between:
- flexibility (supports many analytical queries)  
- accuracy (captures detailed transactional behavior)  
- scalability (can support future analytical needs)