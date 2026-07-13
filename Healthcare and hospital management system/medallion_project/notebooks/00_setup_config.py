"""
Notebook 00 -- setup_config
Layer: Setup
Purpose: Create metadata config table, mount ADLS (n/a locally), initialize
         audit log table, set global variables.
Ref: PDD section 6.1 (Metadata Config Table -- Full Schema)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.spark_utils import get_spark, save_table, DATA_ROOT

spark = get_spark("00_setup_config")

CONFIG_ROWS = [
    # source_id, source_name, file_path, file_format, target_table, primary_key,
    # active_flag, load_type, last_load_timestamp, expected_schema_version,
    # source_system_owner, data_classification, row_count_threshold, max_null_pct,
    # notification_email, retry_count, quarantine_path, partition_column,
    # sla_cutoff_time, dependency_source_ids
    ("SRC_001", "patient_master", f"{DATA_ROOT}/landing/patient_master.csv", "csv",
     "bronze.patient_master", "patient_id", "Y", "FULL", None, "v1.2",
     "EHR Team", "PHI", 100, 0.05, "data-ops@hospital.org", 3,
     f"{DATA_ROOT}/quarantine/patient_master", "ingestion_date", "06:00 AM UTC", None),

    ("SRC_002", "appointments", f"{DATA_ROOT}/landing/appointments.csv", "csv",
     "bronze.appointments", "appointment_id", "Y", "FULL", None, "v1.1",
     "PMS Team", "PHI", 200, 0.05, "data-ops@hospital.org", 3,
     f"{DATA_ROOT}/quarantine/appointments", "ingestion_date", "06:00 AM UTC", "SRC_001"),

    ("SRC_003", "billing_claims", f"{DATA_ROOT}/landing/billing_claims.csv", "csv",
     "bronze.billing_claims", "claim_id", "Y", "FULL", None, "v1.0",
     "Billing Systems Team", "PII", 200, 0.05, "data-ops@hospital.org", 3,
     f"{DATA_ROOT}/quarantine/billing_claims", "ingestion_date", "06:00 AM UTC", "SRC_001,SRC_002"),

    ("SRC_004", "lab_results", f"{DATA_ROOT}/landing/lab_results.csv", "csv",
     "bronze.lab_results", "lab_id", "Y", "FULL", None, "v1.0",
     "LIS Team", "PHI", 100, 0.05, "data-ops@hospital.org", 3,
     f"{DATA_ROOT}/quarantine/lab_results", "ingestion_date", "06:00 AM UTC", "SRC_001"),

    ("SRC_005", "medications", f"{DATA_ROOT}/landing/medications.csv", "csv",
     "bronze.medications", "med_id", "Y", "FULL", None, "v1.0",
     "Pharmacy Team", "PHI", 100, 0.05, "data-ops@hospital.org", 3,
     f"{DATA_ROOT}/quarantine/medications", "ingestion_date", "06:00 AM UTC", "SRC_001"),
]

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, TimestampType

SCHEMA = StructType([
    StructField("source_id", StringType()),
    StructField("source_name", StringType()),
    StructField("file_path", StringType()),
    StructField("file_format", StringType()),
    StructField("target_table", StringType()),
    StructField("primary_key", StringType()),
    StructField("active_flag", StringType()),
    StructField("load_type", StringType()),
    StructField("last_load_timestamp", TimestampType()),
    StructField("expected_schema_version", StringType()),
    StructField("source_system_owner", StringType()),
    StructField("data_classification", StringType()),
    StructField("row_count_threshold", IntegerType()),
    StructField("max_null_pct", FloatType()),
    StructField("notification_email", StringType()),
    StructField("retry_count", IntegerType()),
    StructField("quarantine_path", StringType()),
    StructField("partition_column", StringType()),
    StructField("sla_cutoff_time", StringType()),
    StructField("dependency_source_ids", StringType()),
])

df = spark.createDataFrame(CONFIG_ROWS, schema=SCHEMA)
save_table(df, "config", "metadata_config", mode="overwrite")

# Initialize empty audit log with correct schema (idempotent — only if missing)
from utils.spark_utils import table_exists, AUDIT_LOG_SCHEMA_SPEC
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, IntegerType, BooleanType, TimestampType
if not table_exists("audit", "audit_log"):
    type_map = {"string": StringType(), "long": LongType(), "double": DoubleType(),
                "int": IntegerType(), "boolean": BooleanType(), "timestamp": TimestampType()}
    struct = StructType([StructField(c, type_map[t]) for c, t in AUDIT_LOG_SCHEMA_SPEC])
    empty = spark.createDataFrame([], schema=struct)
    save_table(empty, "audit", "audit_log", mode="overwrite")

print("Metadata config table created with", df.count(), "sources:")
df.select("source_id", "source_name", "target_table", "active_flag", "data_classification").show(truncate=False)
print("Audit log initialized at data/audit/audit_log")
spark.stop()
