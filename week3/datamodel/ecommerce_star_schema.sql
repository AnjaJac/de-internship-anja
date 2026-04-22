create schema if not exists ecommerce;

/* Date dimension stores calendar attributes for time-based analysis.
   It is pre-generated and does not require SCD handling. */
create table ecommerce.dim_date (
	date_key INTEGER PRIMARY KEY
);

/* Add actual date column */
alter table ecommerce.dim_date
add column full_date DATE;

/* Add core date components for aggregation and filtering */
alter table ecommerce.dim_date 
add column day INTEGER,
add column month INTEGER,
add column year INTEGER; 

/* Add extended date attributes for richer analysis */
alter table ecommerce.dim_date 
add column quarter INTEGER,
add column day_of_week INTEGER check (day_of_week between 1 and 7),
add column day_name TEXT,
add column is_weekend BOOLEAN;


/* Product dimension stores product attributes.
   Uses SCD Type 2 to track historical changes. */
create table ecommerce.dim_product (
	product_key INTEGER primary key, /*Surrogate key*/
	product_id TEXT not null,        /*Business key from source system*/
	product_name TEXT not null,
	category TEXT,
	brand TEXT
);

/* Adding the SCD Type 2 columns to track historical versions */
alter table ecommerce.dim_product
add column start_date DATE,
add column end_date DATE,
add column is_current BOOLEAN not null default true;

/*Ensure only one current version exists per product*/
create unique index uniq_product_current
on ecommerce.dim_product (product_id) 
where is_current = true;

/* Customer dimension stores customer attributes.
   Uses SCD Type 2 to track changes such as location and segment.*/
create table ecommerce.dim_customer (
	customer_key INTEGER primary key,   /*Surrogate key*/
	customer_id TEXT not null,          /*Business key*/
	city TEXT, 
	country TEXT,
	account_created_date DATE,
	birth_date DATE, 
	status TEXT not null,
	customer_segment TEXT,
	start_date DATE, 
	end_date DATE,
	is_current BOOLEAN not null default true
);
/* Ensure only one current version exists per customer */
create unique index uniq_customer_current 
on ecommerce.dim_customer (customer_id)
where is_current = true;

/* Fact table stores transactional data at the grain of one order item.
   Links to dimensions and contains measurable metrics. */
create table ecommerce.fact_sales (
	fact_key INTEGER primary key, 
	customer_key INTEGER not null references ecommerce.dim_customer (customer_key),
	product_key INTEGER not null references ecommerce.dim_product (product_key),
	date_key INTEGER not null references ecommerce.dim_date (date_key),
	order_id TEXT not null,   /* Degenerate dimension for grouping order items */
	quantity INTEGER,
	unit_price NUMERIC(10, 2),
	revenue NUMERIC(10, 2)
);

