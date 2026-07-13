"""
Shared helpers for all notebooks.

STORAGE FORMAT NOTE
--------------------
The target platform (per the PDD) is Azure Databricks + ADLS Gen2, where every
Bronze/Silver/Gold table is a **Delta Lake** table (ACID transactions, MERGE,
time travel). This build runs in a sandboxed local environment with no access
to Maven Central, so the Delta Lake JAR cannot be resolved at runtime.

To keep the pipeline logic and code 100% portable, every table write/read goes
through save_table() / read_table() below, which currently use Parquet as a
local stand-in. On Databricks, change FORMAT = "parquet" to FORMAT = "delta"
(one line) and every notebook in this project runs unchanged, including
MERGE-based upserts if you replace `upsert_table` with a real `MERGE INTO`.
"""
import os
import uuid
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

FORMAT = "parquet"  # -> change to "delta" on Databricks
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")
PIPELINE_VERSION = "v1.0.0"
ENVIRONMENT = "DEV"


def get_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )


def path_for(layer: str, table_name: str) -> str:
    return os.path.join(DATA_ROOT, layer, table_name)


def save_table(df, layer: str, table_name: str, mode: str = "overwrite", partition_by=None):
    p = path_for(layer, table_name)
    writer = df.write.format(FORMAT).mode(mode)
    if partition_by:
        writer = writer.partitionBy(partition_by)
    writer.save(p)
    return p


def read_table(spark, layer: str, table_name: str):
    p = path_for(layer, table_name)
    return spark.read.format(FORMAT).load(p)


def table_exists(layer: str, table_name: str) -> bool:
    p = path_for(layer, table_name)
    return os.path.exists(p) and os.path.isdir(p) and len(os.listdir(p)) > 0


def new_batch_id() -> str:
    return str(uuid.uuid4())


def now_ts():
    return datetime.utcnow()


AUDIT_LOG_SCHEMA_SPEC = [
    ("audit_id", "string"), ("batch_id", "string"), ("source_name", "string"),
    ("layer", "string"), ("pipeline_start_time", "timestamp"), ("pipeline_end_time", "timestamp"),
    ("rows_read", "long"), ("rows_written", "long"), ("rows_rejected", "long"),
    ("status", "string"), ("error_message", "string"), ("triggered_by", "string"),
    ("created_at", "timestamp"), ("pipeline_duration_secs", "long"), ("notebook_name", "string"),
    ("cluster_id", "string"), ("spark_app_id", "string"), ("rows_quarantined", "long"),
    ("dq_score_avg", "double"), ("schema_version", "string"), ("environment", "string"),
    ("retry_attempt", "int"), ("data_classification", "string"), ("sla_met", "boolean"),
    ("downstream_notified", "boolean"),
]


def append_audit_log(spark, records: list):
    """
    records: list of dicts matching the Audit Log schema (section 7.1 of the PDD).
    Appends to data/audit/audit_log (creates it on first write).
    """
    from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, IntegerType, BooleanType, TimestampType
    type_map = {
        "string": StringType(), "long": LongType(), "double": DoubleType(),
        "int": IntegerType(), "boolean": BooleanType(), "timestamp": TimestampType(),
    }
    schema_cols = [c for c, _ in AUDIT_LOG_SCHEMA_SPEC]
    struct = StructType([StructField(c, type_map[t]) for c, t in AUDIT_LOG_SCHEMA_SPEC])
    rows = [tuple(r.get(c) for c in schema_cols) for r in records]
    df = spark.createDataFrame(rows, schema=struct)
    mode = "append" if table_exists("audit", "audit_log") else "overwrite"
    save_table(df, "audit", "audit_log", mode=mode)
