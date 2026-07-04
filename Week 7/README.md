# Delta Lake Incremental Data Processing Assignment

## Objective
Perform incremental data processing using **Delta Lake**: load a base dataset, clean
it, simulate an incremental batch of new/changed data, apply a `MERGE` (upsert)
operation, and validate the results.

## Dataset
This project uses a customer-dimension dataset with the same schema as the
[Kaggle Superstore dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)
(`CustomerID`, `CustomerName`, `Segment`, `Country`, `City`, `State`, `PostalCode`,
`Region`).


## Project Structure
```
delta-lake-assignment/
│
├── data/
│   ├── customer_master.csv         # Base dataset (with a few intentional nulls/duplicates)
│   └── customer_incremental.csv    # Simulated incoming batch (6 updates + 6 new customers)
│
├── notebooks/
│   └── delta_scd_assignment.ipynb  # Full pipeline: load → clean → merge → validate
│
├── screenshots/
│   ├── data_loading/
│   ├── data_cleaning/
│   ├── scd1/
│   ├── scd2/
│   ├── validation/
│   └── final_output/
│
├── report/
│   └── assignment_summary.pdf 
│
└── README.md
```

## Steps Covered in the Notebook
1. **Load dataset into a Delta table** — read the CSV, write it as a managed Delta
   table (`customer_delta`).
2. **Basic cleaning** — remove exact duplicate rows, fill/handle nulls in
   non-key columns.
3. **Create incremental dataset** — `customer_incremental.csv` simulates a new
   batch: 6 updated customers + 6 new customers.
4. **MERGE operation** — `DeltaTable.merge()` upserts the incremental batch into
   the Delta table (SCD Type 1: update in place). An optional SCD Type 2 variant
   is also shown, which preserves history instead of overwriting it.
5. **Validation** — row counts, duplicate-key checks, and Delta's built-in
   `history()` transaction log.
6. **Final output** — the merged table is displayed along with a summary of what
   changed.

## How to Run
### Option A — Databricks (recommended, Delta Lake pre-installed)
1. Create a new Databricks Community Edition workspace/cluster.
2. Upload `data/customer_master.csv` and `data/customer_incremental.csv` to
   DBFS (or a Unity Catalog volume) and update the file paths at the top of the
   notebook.
3. Import `notebooks/delta_scd_assignment.ipynb` and run all cells top to bottom.

### Option B — Local Jupyter / PySpark
```bash
pip install pyspark==3.5.1 delta-spark==3.2.0 jupyter
jupyter notebook notebooks/delta_scd_assignment.ipynb
```
The notebook's setup cell uses `delta.configure_spark_with_delta_pip(...)` so no
extra Spark configuration is needed locally.


## Summary
Delta Lake's `MERGE INTO` makes incremental (upsert) loading a single declarative
operation instead of a manual read-join-overwrite dance, while ACID transactions
and the transaction log (`DeltaTable.history()`) give safety and auditability that
plain CSV/Parquet files don't provide.
