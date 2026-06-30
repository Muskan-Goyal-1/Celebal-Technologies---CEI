# Week 6 — Apache Spark Assignment

## Project Overview

This repository contains a complete, ready-to-run PySpark assignment that demonstrates Apache Spark's core architecture, lazy execution model, and DataFrame API for efficient large-scale data processing. All work is implemented in a single, well-documented Jupyter Notebook and is backed by a runnable sample dataset, so every question can be executed end-to-end with no external dependencies.

## Assignment Objective

Understand Spark architecture and perform efficient data processing using transformations, filtering, schema handling, and optimized file formats — covering everything from how a Spark application is scheduled across a cluster down to practical, production-grade DataFrame transformations.

## Technologies Used

| Technology | Purpose |
|---|---|
| **Apache Spark 3.5.x (PySpark)** | Distributed data processing engine |
| **Python 3.11** | Notebook / driver-side language |
| **Jupyter Notebook** | Interactive development and documentation |
| **Parquet (Snappy compression)** | Columnar storage format |
| **CSV** | Row-based interchange format |

## Repository Structure

```
Week6-Apache-Spark/
│
├── notebooks/
│   └── Week6_Apache_Spark_Assignment.ipynb   # Main assignment notebook (Q1–Q15 + pipeline)
│
├── data/
│   ├── source.csv                            # Sample 20-row e-commerce orders dataset
│
│
├── output/
│   ├── output.csv                             # Pipeline + exercise outputs written as CSV

│
└── README.md
```

## Spark Architecture Summary

A Spark application consists of three cooperating components:

- **Driver** — runs the application's `main()` logic, builds the logical/physical execution plan (DAG), schedules tasks, and collects results. It is the coordinator of the entire job.
- **Cluster Manager** — allocates cluster resources (CPU/memory) and launches Executor processes on worker nodes on the Driver's behalf. Spark supports Standalone, YARN, Kubernetes, and (legacy) Mesos cluster managers.
- **Executors** — JVM processes on worker nodes that actually run tasks against data partitions and report results back to the Driver; they can also cache data in memory across stages.

**Execution modes** differ in *where the Driver runs*:
- **Local mode** — Driver and Executors share a single JVM on one machine (used by this notebook, via `local[*]`); ideal for development.
- **Client mode** — Driver runs on the machine that submitted the job, outside the cluster; the submitting machine must stay online for the job's duration.
- **Cluster mode** — Driver runs inside the cluster, managed by the Cluster Manager; production-standard, since it has no dependency on the submitting machine staying connected.

## Explanation of Each Task (Q1–Q15)

| # | Topic |
|---|---|
| Q1 | Roles of Driver, Cluster Manager, and Executor |
| Q2 | How Lazy Evaluation improves chained-transformation performance |
| Q3 | Reading CSV with header + inferred schema (and the explicit-schema alternative) |
| Q4 | CSV (row-based) vs Parquet (columnar) storage and why it matters |
| Q5 | Column selection combined with a filter |
| Q6 | Renaming a column and casting a column's data type |
| Q7 | How the DAG/lineage graph provides fault tolerance |
| Q8 | Filtering with an AND condition |
| Q9 | Predicate Pushdown in Parquet and its memory/performance impact |
| Q10 | Adding a derived column |
| Q11 | Transformations vs Actions, with examples of each |
| Q12 | Loading Parquet, dropping null rows, writing CSV (full null-handling patterns included) |
| Q13 | Client Mode vs Cluster Mode |
| Q14 | Filtering with an OR condition |
| Q15 | Why `.show(5)` is safer than `.collect()` on multi-terabyte datasets |

The notebook additionally includes dedicated sections on **wide transformations & shuffle** and a full **Read → Transform → Filter → Write pipeline** that ties every concept together into one reusable function.

## Performance Observations

- **Lazy evaluation**: building a multi-step transformation chain produces no Spark job until an action (`show()`, `count()`, `write()`) is called; `.explain()` confirms the optimizer sees and plans the *whole* chain at once.
- **Predicate pushdown**: filtering a Parquet-backed DataFrame shows a `PushedFilters` entry in the physical plan — row groups that can't match the filter are skipped without being read.
- **Wide transformations** (`groupBy`, `orderBy`, `join`) introduce `Exchange` (shuffle) operators in the physical plan — visible evidence of the network/disk cost these operations carry versus narrow transformations like `filter`/`select`.

## CSV vs Parquet Comparison

| | CSV | Parquet |
|---|---|---|
| Storage layout | Row-based, plain text | Columnar, binary |
| Schema | Not embedded — inferred or declared separately | Embedded / self-describing |
| Compression | Generic text compression | Type-aware columnar compression (often 4–10x smaller) |
| Column pruning | Not possible — must read all columns | Reads only requested columns |
| Predicate pushdown | Not possible | Supported via per-row-group min/max statistics |
| Best for | Interop, human-readable exports | Internal pipeline storage, repeated analytical reads |

The notebook includes a runnable benchmark cell that writes the same dataset as CSV and Parquet, compares on-disk size, and times a read+filter operation against both.

## Lazy Evaluation and DAG Summary

Spark transformations (`select`, `filter`, `withColumn`, `groupBy`, etc.) only build up a logical plan; nothing executes until an action is called. This lets Spark's Catalyst optimizer view the entire chain before running anything, enabling optimizations like filter/column pushdown and operator fusion. The same lineage graph that enables this optimization also provides **fault tolerance**: if a worker fails, Spark recomputes only the lost partitions by replaying their recorded lineage, rather than restarting the whole job.

## How to Run the Notebook

1. **Clone the repository** and `cd` into it.
2. **Install dependencies** (Python 3.9+ and a JVM are required, since PySpark runs on the JVM):
   ```bash
   pip install pyspark jupyter
   ```
3. **Launch Jupyter**:
   ```bash
   jupyter notebook notebooks/Week6_Apache_Spark_Assignment.ipynb
   ```
4. **Run all cells** (`Cell → Run All` or `Kernel → Restart & Run All`). The notebook is self-contained: it reads `../data/source.csv`, generates `../data/sample_parquet/` itself, and writes all pipeline outputs into `../output/csv/` and `../output/parquet/`.

No external dataset or cluster is required — everything runs locally via `local[*]` Spark mode against the included sample dataset.

## Conclusion

This assignment demonstrates a working command of Spark's architecture (Driver/Cluster Manager/Executor, execution modes), its lazy/DAG-based execution model, and the practical DataFrame API needed to build a real Read → Transform → Filter → Write pipeline — including schema handling, null handling, column-level transformations, and dual CSV/Parquet output. These are the same foundations needed to scale a pipeline safely from a small sample dataset up to multi-terabyte production workloads.
