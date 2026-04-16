# Week 2 Notes – Python for Data Engineering

## What is Parquet?

Parquet is a columnar file format designed for efficient data storage and retrieval. Unlike CSV, which stores data row by row, Parquet stores data by columns.

This has several advantages:

- Smaller file size due to better compression  
- Faster queries, since only needed columns are read  
- Efficient for analytics workloads, especially with large datasets  

In this project, saving data as Parquet resulted in a smaller file size compared to CSV and faster read performance.

---

## Python Concept That Clicked

One concept that became clear during this week is writing modular functions for data pipelines.

Instead of writing one large script, I structured the pipeline into small, reusable functions such as:

- handle_missing_values  
- transform_duration  
- transform_genres_pipeline  

This made the code:
- easier to read  
- easier to test with pytest  
- easier to debug  

It also showed how important it is to separate concerns (cleaning vs transformation vs saving), which is a key principle in data engineering.