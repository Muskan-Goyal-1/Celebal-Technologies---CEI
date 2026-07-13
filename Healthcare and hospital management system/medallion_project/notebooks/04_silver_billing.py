"""
Notebook 04 -- silver_billing
Layer: Silver
Purpose: Cleanse Billing & Claims: charge validation, claim status
         enrichment. Writes silver_billing.
"""
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.spark_utils import get_spark, save_table, read_table, append_audit_log, new_batch_id, now_ts, ENVIRONMENT
from pyspark.sql import functions as F

spark = get_spark("04_silver_billing")
batch_id = new_batch_id()
start = now_ts()

bronze = read_table(spark, "bronze", "billing_claims")
bronze_batch_id = bronze.select("_batch_id").first()["_batch_id"]
appts = read_table(spark, "silver", "silver_appointments").filter("_is_current = true").select(
    F.col("appointment_id"), F.col("department").alias("appt_department"))
rows_read = bronze.count()

MANDATORY = ["claim_id", "patient_id", "charge_amount", "claim_status"]
silver = bronze.withColumn(
    "_dq_failure_reason",
    F.concat_ws(",", *[F.when(F.col(c).isNull() | (F.col(c).cast("string") == ""), F.lit(c)) for c in MANDATORY])
)

# charge validation: charge_amount must be positive and claim_amount should equal charge_amount
bad_charge = F.col("charge_amount").isNull() | (F.col("charge_amount") <= 0)
mismatch = (F.col("claim_amount") != F.col("charge_amount")) & F.col("claim_amount").isNotNull() & F.col("charge_amount").isNotNull()
silver = silver.withColumn(
    "_dq_failure_reason",
    F.when(bad_charge, F.concat_ws(",", F.col("_dq_failure_reason"), F.lit("invalid_charge_amount")))
     .otherwise(F.col("_dq_failure_reason"))
)

present_count = None
for c in MANDATORY:
    term = F.when(F.col(c).isNotNull() & (F.col(c).cast("string") != ""), F.lit(1)).otherwise(F.lit(0))
    present_count = term if present_count is None else present_count + term
silver = silver.withColumn("_dq_score", (present_count / F.lit(len(MANDATORY))).cast("float"))
silver = silver.withColumn("_dq_passed", (F.col("_dq_failure_reason") == "") | F.col("_dq_failure_reason").isNull())
rows_rejected = silver.filter(~F.col("_dq_passed")).count()

# claim status enrichment: is this claim "accurate" (used by Billing Accuracy Rate KPI)?
enriched = (silver
    .withColumn("is_billing_accurate", ~mismatch & F.col("_dq_passed"))
    .withColumn("is_claim_approved", F.col("claim_status") == "Approved")
    .join(appts, on="appointment_id", how="left")
)

silver_final = (enriched
    .withColumn("_silver_load_timestamp", F.current_timestamp())
    .withColumn("_silver_batch_id", F.lit(batch_id))
    .withColumn("_bronze_batch_id", F.lit(bronze_batch_id))
    .withColumn("_is_current", F.lit(True))
    .withColumn("_effective_from", F.current_timestamp())
    .withColumn("_effective_to", F.lit(None).cast("timestamp"))
    .withColumn("_masked_fields", F.lit(""))
    .withColumn("_enrichment_source", F.lit("bronze.billing_claims,silver.silver_appointments"))
    .withColumn("_record_version", F.lit(1))
    .drop("_record_hash", "_raw_row_number", "_is_duplicate")
)

save_table(silver_final, "silver", "silver_billing", mode="overwrite")
rows_written = silver_final.count()
dq_avg = silver_final.agg(F.avg("_dq_score")).first()[0]

end = now_ts()
append_audit_log(spark, [{
    "audit_id": str(uuid.uuid4()), "batch_id": batch_id, "source_name": "silver_billing",
    "layer": "SILVER", "pipeline_start_time": start, "pipeline_end_time": end,
    "rows_read": rows_read, "rows_written": rows_written, "rows_rejected": rows_rejected,
    "status": "SUCCESS", "error_message": None, "triggered_by": "scheduler",
    "created_at": now_ts(), "pipeline_duration_secs": int((end - start).total_seconds()),
    "notebook_name": "04_silver_billing", "cluster_id": "local-cluster",
    "spark_app_id": spark.sparkContext.applicationId, "rows_quarantined": 0,
    "dq_score_avg": float(dq_avg) if dq_avg is not None else None, "schema_version": "v1.0",
    "environment": ENVIRONMENT, "retry_attempt": 0, "data_classification": "PII",
    "sla_met": True, "downstream_notified": False,
}])

print(f"silver_billing: {rows_read} read -> {rows_written} written, {rows_rejected} failed DQ, avg_dq_score={dq_avg:.3f}")
spark.stop()
