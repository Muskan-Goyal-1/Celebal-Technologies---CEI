"""
Notebook 01 -- ingest_bronze
Layer: Bronze
Purpose: Metadata-driven CSV ingestion for all 5 sources. Appends audit
         columns. Writes to Delta (Parquet stand-in). Logs to audit.
Ref: PDD section 5.1 (Bronze audit/system metadata columns) and section 6.2
     (how the metadata-driven framework works).
"""
import sys, os, uuid, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.spark_utils import (get_spark, save_table, read_table, append_audit_log,
                                new_batch_id, now_ts, PIPELINE_VERSION, ENVIRONMENT)
from pyspark.sql import functions as F

spark = get_spark("01_ingest_bronze")
batch_id = new_batch_id()
audit_records = []

config_df = read_table(spark, "config", "metadata_config").filter("active_flag = 'Y'")
sources = [r.asDict() for r in config_df.collect()]

SOURCE_SYSTEM_CODE = {
    "patient_master": "EHR", "appointments": "PMS", "billing_claims": "BILLING",
    "lab_results": "LIS", "medications": "PHARMACY",
}

print(f"Batch {batch_id}: {len(sources)} active sources to ingest")

record_hash_cols_cache = {}

for src in sources:
    start = now_ts()
    source_name = src["source_name"]
    target_table = src["target_table"].split(".")[-1]  # bronze.<table> -> <table>
    file_path = src["file_path"]
    status, error_message = "SUCCESS", None
    rows_read = rows_written = 0
    try:
        raw = spark.read.option("header", "true").option("inferSchema", "true").csv(file_path)
        raw_cols = raw.columns

        # deterministic row hash across the original columns, for change detection
        raw = raw.withColumn(
            "_record_hash",
            F.sha2(F.concat_ws("||", *[F.coalesce(F.col(c).cast("string"), F.lit("")) for c in raw_cols]), 256),
        )

        # stable original row position (source-file order), added before any audit cols
        w = __import__("pyspark.sql.window", fromlist=["Window"]).Window.orderBy(F.monotonically_increasing_id())
        raw = raw.withColumn("_raw_row_number", F.row_number().over(w))

        rows_read = raw.count()

        # duplicate detection at ingest: flag rows whose full-content hash repeats
        dup_counts = raw.groupBy("_record_hash").count()
        raw = (raw.join(dup_counts, on="_record_hash", how="left")
                   .withColumn("_is_duplicate", F.col("count") > 1)
                   .drop("count"))

        bronze_df = (raw
            .withColumn("_ingestion_timestamp", F.current_timestamp())
            .withColumn("_source_file_name", F.lit(os.path.basename(file_path)))
            .withColumn("_batch_id", F.lit(batch_id))
            .withColumn("_layer", F.lit("BRONZE"))
            .withColumn("_ingestion_date", F.current_date())
            .withColumn("_pipeline_version", F.lit(PIPELINE_VERSION))
            .withColumn("_source_system", F.lit(SOURCE_SYSTEM_CODE.get(source_name, "UNKNOWN")))
        )

        save_table(bronze_df, "bronze", target_table, mode="overwrite", partition_by="_ingestion_date")
        rows_written = bronze_df.count()

        # basic row-count-threshold check (metadata-driven alerting per config)
        if rows_written < (src["row_count_threshold"] or 0):
            status = "PARTIAL"
            error_message = f"rows_written ({rows_written}) below row_count_threshold ({src['row_count_threshold']})"

        print(f"  [OK] {source_name}: {rows_read} read -> {rows_written} written -> bronze.{target_table}")

    except Exception as e:
        status = "FAILED"
        error_message = str(e)[:500]
        print(f"  [FAILED] {source_name}: {error_message}")

    end = now_ts()
    audit_records.append({
        "audit_id": str(uuid.uuid4()), "batch_id": batch_id, "source_name": source_name,
        "layer": "BRONZE", "pipeline_start_time": start, "pipeline_end_time": end,
        "rows_read": rows_read, "rows_written": rows_written, "rows_rejected": 0,
        "status": status, "error_message": error_message, "triggered_by": "scheduler",
        "created_at": now_ts(), "pipeline_duration_secs": int((end - start).total_seconds()),
        "notebook_name": "01_ingest_bronze", "cluster_id": "local-cluster",
        "spark_app_id": spark.sparkContext.applicationId, "rows_quarantined": 0,
        "dq_score_avg": None, "schema_version": src["expected_schema_version"],
        "environment": ENVIRONMENT, "retry_attempt": 0,
        "data_classification": src["data_classification"], "sla_met": True,
        "downstream_notified": False,
    })

append_audit_log(spark, audit_records)
print(f"Bronze ingestion complete. Batch ID: {batch_id}")
spark.stop()
