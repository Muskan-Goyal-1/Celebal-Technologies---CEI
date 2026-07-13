"""
Notebook 05 -- silver_lab_meds
Layer: Silver
Purpose: Cleanse Lab Results + Medications: abnormal flag logic, inventory
         calc. Writes silver_lab, silver_medications.
"""
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.spark_utils import get_spark, save_table, read_table, append_audit_log, new_batch_id, now_ts, ENVIRONMENT
from pyspark.sql import functions as F

spark = get_spark("05_silver_lab_meds")
batch_id = new_batch_id()
audit_records = []

def silver_common(df, mandatory_cols, bronze_batch_id, source_desc):
    d = df.withColumn(
        "_dq_failure_reason",
        F.concat_ws(",", *[F.when(F.col(c).isNull() | (F.col(c).cast("string") == ""), F.lit(c)) for c in mandatory_cols])
    )
    present_count = None
    for c in mandatory_cols:
        term = F.when(F.col(c).isNotNull() & (F.col(c).cast("string") != ""), F.lit(1)).otherwise(F.lit(0))
        present_count = term if present_count is None else present_count + term
    d = d.withColumn("_dq_score", (present_count / F.lit(len(mandatory_cols))).cast("float"))
    d = d.withColumn("_dq_passed", (F.col("_dq_failure_reason") == "") | F.col("_dq_failure_reason").isNull())
    d = (d
        .withColumn("_silver_load_timestamp", F.current_timestamp())
        .withColumn("_silver_batch_id", F.lit(batch_id))
        .withColumn("_bronze_batch_id", F.lit(bronze_batch_id))
        .withColumn("_is_current", F.lit(True))
        .withColumn("_effective_from", F.current_timestamp())
        .withColumn("_effective_to", F.lit(None).cast("timestamp"))
        .withColumn("_masked_fields", F.lit(""))
        .withColumn("_enrichment_source", F.lit(source_desc))
        .withColumn("_record_version", F.lit(1))
        .drop("_record_hash", "_raw_row_number", "_is_duplicate")
    )
    return d

# ---------------- LAB RESULTS ----------------
start = now_ts()
lab_bronze = read_table(spark, "bronze", "lab_results")
lab_batch_id = lab_bronze.select("_batch_id").first()["_batch_id"]
lab_rows_read = lab_bronze.count()

# abnormal flag logic: recompute abnormality from numeric result vs. reference range
# (reference_range is text like "70-100" or "<200"); trust source flag but cross-check numeric ranges where parseable
def parse_low(rng):
    return F.when(F.col(rng).contains("-"), F.split(F.col(rng), "-").getItem(0).cast("double"))

def parse_high(rng):
    return F.when(F.col(rng).contains("-"), F.split(F.col(rng), "-").getItem(1).cast("double"))

lab_silver = (lab_bronze
    .withColumn("_ref_low", parse_low("reference_range"))
    .withColumn("_ref_high", parse_high("reference_range"))
    .withColumn("computed_abnormal_flag",
        F.when(F.col("result_value").isNull(), F.lit(None))
         .when(F.col("_ref_low").isNotNull() & F.col("_ref_high").isNotNull(),
               F.when((F.col("result_value") < F.col("_ref_low")) | (F.col("result_value") > F.col("_ref_high")), "Y").otherwise("N"))
         .otherwise(F.col("abnormal_flag")))
    .withColumn("flag_mismatch", (F.col("computed_abnormal_flag").isNotNull()) & (F.col("computed_abnormal_flag") != F.col("abnormal_flag")))
    .drop("_ref_low", "_ref_high")
)

lab_silver = silver_common(lab_silver, ["lab_id", "patient_id", "test_name", "result_value"], lab_batch_id,
                            "bronze.lab_results")
save_table(lab_silver, "silver", "silver_lab", mode="overwrite")
lab_rows_written = lab_silver.count()
lab_rows_rejected = lab_silver.filter(~F.col("_dq_passed")).count()
lab_dq_avg = lab_silver.agg(F.avg("_dq_score")).first()[0]
end = now_ts()
audit_records.append({
    "audit_id": str(uuid.uuid4()), "batch_id": batch_id, "source_name": "silver_lab",
    "layer": "SILVER", "pipeline_start_time": start, "pipeline_end_time": end,
    "rows_read": lab_rows_read, "rows_written": lab_rows_written, "rows_rejected": lab_rows_rejected,
    "status": "SUCCESS", "error_message": None, "triggered_by": "scheduler",
    "created_at": now_ts(), "pipeline_duration_secs": int((end - start).total_seconds()),
    "notebook_name": "05_silver_lab_meds", "cluster_id": "local-cluster",
    "spark_app_id": spark.sparkContext.applicationId, "rows_quarantined": 0,
    "dq_score_avg": float(lab_dq_avg) if lab_dq_avg is not None else None, "schema_version": "v1.0",
    "environment": ENVIRONMENT, "retry_attempt": 0, "data_classification": "PHI",
    "sla_met": True, "downstream_notified": False,
})
print(f"silver_lab: {lab_rows_read} read -> {lab_rows_written} written, {lab_rows_rejected} failed DQ, avg_dq_score={lab_dq_avg:.3f}")

# ---------------- MEDICATIONS ----------------
start = now_ts()
med_bronze = read_table(spark, "bronze", "medications")
med_batch_id = med_bronze.select("_batch_id").first()["_batch_id"]
med_rows_read = med_bronze.count()

# inventory calc: flag negative/implausible quantity_dispensed (data entry errors),
# and derive turnover-support columns used by the Gold KPI (Medication Inventory Turnover)
med_silver = (med_bronze
    .withColumn("valid_quantity", F.col("quantity_dispensed") > 0)
    .withColumn("quantity_dispensed_clean",
        F.when(F.col("quantity_dispensed") > 0, F.col("quantity_dispensed")).otherwise(F.lit(0)))
    .withColumn("total_cost", F.col("quantity_dispensed_clean") * F.col("unit_cost"))
)

med_silver = med_silver.withColumn(
    "_dq_failure_reason",
    F.when(~F.col("valid_quantity"), F.lit("invalid_quantity_dispensed")).otherwise(F.lit(""))
)
med_silver = med_silver.withColumn("_dq_passed", F.col("valid_quantity"))
med_silver = med_silver.withColumn("_dq_score", F.when(F.col("valid_quantity"), F.lit(1.0)).otherwise(F.lit(0.0)).cast("float"))
med_silver = (med_silver
    .withColumn("_silver_load_timestamp", F.current_timestamp())
    .withColumn("_silver_batch_id", F.lit(batch_id))
    .withColumn("_bronze_batch_id", F.lit(med_batch_id))
    .withColumn("_is_current", F.lit(True))
    .withColumn("_effective_from", F.current_timestamp())
    .withColumn("_effective_to", F.lit(None).cast("timestamp"))
    .withColumn("_masked_fields", F.lit(""))
    .withColumn("_enrichment_source", F.lit("bronze.medications"))
    .withColumn("_record_version", F.lit(1))
    .drop("_record_hash", "_raw_row_number", "_is_duplicate")
)

save_table(med_silver, "silver", "silver_medications", mode="overwrite")
med_rows_written = med_silver.count()
med_rows_rejected = med_silver.filter(~F.col("_dq_passed")).count()
med_dq_avg = med_silver.agg(F.avg("_dq_score")).first()[0]
end = now_ts()
audit_records.append({
    "audit_id": str(uuid.uuid4()), "batch_id": batch_id, "source_name": "silver_medications",
    "layer": "SILVER", "pipeline_start_time": start, "pipeline_end_time": end,
    "rows_read": med_rows_read, "rows_written": med_rows_written, "rows_rejected": med_rows_rejected,
    "status": "SUCCESS", "error_message": None, "triggered_by": "scheduler",
    "created_at": now_ts(), "pipeline_duration_secs": int((end - start).total_seconds()),
    "notebook_name": "05_silver_lab_meds", "cluster_id": "local-cluster",
    "spark_app_id": spark.sparkContext.applicationId, "rows_quarantined": 0,
    "dq_score_avg": float(med_dq_avg) if med_dq_avg is not None else None, "schema_version": "v1.0",
    "environment": ENVIRONMENT, "retry_attempt": 0, "data_classification": "PHI",
    "sla_met": True, "downstream_notified": False,
})
print(f"silver_medications: {med_rows_read} read -> {med_rows_written} written, {med_rows_rejected} failed DQ, avg_dq_score={med_dq_avg:.3f}")

append_audit_log(spark, audit_records)
spark.stop()
