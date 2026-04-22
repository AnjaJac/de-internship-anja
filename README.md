## Week 3 – Data Modeling and Warehouse Concepts

### Overview

Designed and implemented a data warehouse model for an e-commerce scenario using a star schema.

---

### Key Concepts

- OLTP vs OLAP systems  
- Star schema design  
- Fact table grain definition  
- Slowly Changing Dimensions (SCD Type 2)  
- Medallion architecture (Bronze, Silver, Gold)  

---

### Implementation

#### Star Schema

- `fact_sales` → one row per order item  
- `dim_product` → SCD Type 2  
- `dim_customer` → SCD Type 2  
- `dim_date` → generated date dimension  

---

#### SCD Type 2

- Implemented using:
  - `start_date`
  - `end_date`
  - `is_current`
- Enforced using partial unique indexes  

---

#### Transformations

- Populated `dim_date` using `generate_series`  
- Created aggregated table `fact_sales_daily`  
  - Grain: one row per product per day  
  - Used for performance optimization  

---

### Data Model Files

- `week3/datamodel/ecommerce_star_schema.sql`  
- `week3/datamodel/transformations.sql`  
- `week3/datamodel/ecommerce.dbml`  
- `week3/datamodel/ecommerce_star_schema.png`  

---

### Key Takeaways

- Grain defines the correctness of the model  
- Star schema simplifies analytical queries  
- SCD Type 2 preserves historical accuracy  
- Aggregations improve performance but reduce detail 