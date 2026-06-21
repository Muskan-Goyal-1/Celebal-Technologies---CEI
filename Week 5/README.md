# Spark Assignment — Week 5

Understand Spark fundamentals and perform data cleaning, transformation, and aggregation using DataFrames.

## Folder Structure

```
spark-assignment/
│── data/
│   └── dataset.csv          # Synthetic transactions dataset used throughout the notebook
│── notebook/
│   └── spark_basics.ipynb   # Full notebook: steps walkthrough + Q1-Q15 answers with code & output
│── output/
│   └── results.csv          # Final pipeline output: total revenue per store_id
│── README.md
```

## What's in the notebook

1. **Spark vs MapReduce** — limitations of MapReduce, advantages of Spark (in-memory computing, DAG execution).
2. **Spark session setup** and **data loading** (schema, row count, sample rows).
3. **Data cleaning** — duplicate removal, null handling (`drop` vs `fill`).
4. **Filtering** — by age range, category, region.
5. **Transformation** — renaming columns, casting types.
6. **Aggregation** — `count`, `sum`, `avg`, `min`, `max`.
7. **Grouping** — `groupBy` with conditions on aggregated results.
8. **Wide transformations & shuffle** — conceptual explanation.
9. **Schema modification** — casting `raw_timestamp` to `TimestampType`, renaming to `event_time`.
10. **Handling inconsistent data** — nulls, empty strings.
11. **Complete pipeline** — clean → filter → transform → aggregate, in one chain.
12. **Q&A section (Q1–Q15)** — every assignment question answered with explanation and/or runnable PySpark code and real captured output.
13. **Insights** — observations on data quality, null handling, and performance (shuffle cost).

## How to run

```bash
pip install pyspark
jupyter notebook notebook/spark_basics.ipynb
```

All cells run end-to-end with no errors using `pyspark` in local mode (`local[*]`).

## Dataset

`data/dataset.csv` is a synthetic dataset (515 rows) generated for this assignment, containing:
`user_id, transaction_date, region, product_category, sale_amount, age, subscription, city, price, store_id, email, username, status, raw_timestamp`

It intentionally includes duplicate rows, null values (in `age`, `price`, `sale_amount`, `status`, `email`), and an empty-string `username` case so every cleaning operation in the notebook has real data to act on.
