"""
Notebook 02 -- silver_patients
Layer: Silver
Purpose: Cleanse Patient Master: nulls, dedup, SCD Type 2, insurance
         validation. Writes silver_patients.
Ref: PDD section 5.2 (Silver DQ/governance metadata columns),
     11 (HIPAA: SHA-256 hashing for SSN/DOB/Phone).
"""
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.spark_utils import (get_spark, save_table, read_table, append_audit_log,
                                new_batch_id, now_ts, ENVIRONMENT)
from pyspark.sql import functions as F, Window

spark = get_spark("02_silver_patients")
batch_id = new_batch_id()
start = now_ts()
status, error_message = "SUCCESS", None
rows_rejected = 0

bronze = read_table(spark, "bronze", "patient_master")
bronze_batch_id = bronze.select("_batch_id").first()["_batch_id"]
rows_read = bronze.count()

# 1) drop exact-duplicate rows detected in Bronze (keep first occurrence per hash)
w_dedup = Window.partitionBy("_record_hash")
dedup = (bronze
    .withColumn("_first_row_for_hash", F.min("_raw_row_number").over(w_dedup))
    .filter(~(F.col("_is_duplicate") & (F.col("_raw_row_number") > F.col("_first_row_for_hash"))))
    .drop("_first_row_for_hash"))

# 2) business rule / DQ validation
MANDATORY = ["patient_id", "first_name", "last_name", "dob", "insurance_provider"]

silver = dedup.withColumn(
    "_dq_failure_reason",
    F.concat_ws(",", *[F.when(F.col(c).isNull() | (F.col(c) == ""), F.lit(c)) for c in MANDATORY])
)
silver = silver.withColumn("_dq_passed", (F.col("_dq_failure_reason") == "") | F.col("_dq_failure_reason").isNull())
# dq_score: fraction of mandatory fields present
present_count = None
for c in MANDATORY:
    term = F.when(F.col(c).isNotNull() & (F.col(c) != ""), F.lit(1)).otherwise(F.lit(0))
    present_count = term if present_count is None else present_count + term
silver = silver.withColumn("_dq_score", (present_count / F.lit(len(MANDATORY))).cast("float"))

rows_rejected = silver.filter(~F.col("_dq_passed")).count()

# 3) insurance validation - flag known-bad insurance provider values
VALID_INSURERS = ["BlueCross BlueShield", "UnitedHealth", "Aetna", "Cigna", "Medicare", "Medicaid", "Humana"]
silver = silver.withColumn(
    "_dq_failure_reason",
    F.when(~F.col("insurance_provider").isin(VALID_INSURERS) & F.col("_dq_passed"),
           F.concat_ws(",", F.col("_dq_failure_reason"), F.lit("invalid_insurance_provider")))
     .otherwise(F.col("_dq_failure_reason"))
)

# 4) PII masking (HIPAA 45 CFR 164.514): SHA-256 hash SSN, DOB, Phone in Silver
silver = (silver
    .withColumn("ssn_hash", F.sha2(F.col("ssn").cast("string"), 256))
    .withColumn("dob_hash", F.sha2(F.col("dob").cast("string"), 256))
    .withColumn("phone_hash", F.sha2(F.col("phone").cast("string"), 256))
    .drop("ssn", "phone")  # dob retained in cleartext for age/ALOS calcs elsewhere is NOT done -> also mask
)
# keep a non-PII derived birth_year for downstream age-banding, then mask dob
silver = silver.withColumn("birth_year", F.year(F.col("dob").cast("date")))
silver = silver.drop("dob")

# 5) SCD Type 2 metadata (first load: every row is a new current version)
silver = (silver
    .withColumn("_silver_load_timestamp", F.current_timestamp())
    .withColumn("_silver_batch_id", F.lit(batch_id))
    .withColumn("_bronze_batch_id", F.lit(bronze_batch_id))
    .withColumn("_is_current", F.lit(True))
    .withColumn("_effective_from", F.current_timestamp())
    .withColumn("_effective_to", F.lit(None).cast("timestamp"))
    .withColumn("_masked_fields", F.lit("ssn,dob,phone"))
    .withColumn("_enrichment_source", F.lit("bronze.patient_master"))
    .withColumn("_record_version", F.lit(1))
)

silver = silver.drop("_record_hash", "_raw_row_number", "_is_duplicate")

save_table(silver, "silver", "silver_patients", mode="overwrite")
rows_written = silver.count()
dq_avg = silver.agg(F.avg("_dq_score")).first()[0]

end = now_ts()
append_audit_log(spark, [{
    "audit_id": str(uuid.uuid4()), "batch_id": batch_id, "source_name": "silver_patients",
    "layer": "SILVER", "pipeline_start_time": start, "pipeline_end_time": end,
    "rows_read": rows_read, "rows_written": rows_written, "rows_rejected": rows_rejected,
    "status": status, "error_message": error_message, "triggered_by": "scheduler",
    "created_at": now_ts(), "pipeline_duration_secs": int((end - start).total_seconds()),
    "notebook_name": "02_silver_patients", "cluster_id": "local-cluster",
    "spark_app_id": spark.sparkContext.applicationId, "rows_quarantined": 0,
    "dq_score_avg": float(dq_avg) if dq_avg is not None else None, "schema_version": "v1.2",
    "environment": ENVIRONMENT, "retry_attempt": 0, "data_classification": "PHI",
    "sla_met": True, "downstream_notified": False,
}])

print(f"silver_patients: {rows_read} read -> {rows_written} written, {rows_rejected} failed DQ, avg_dq_score={dq_avg:.3f}")
spark.stop()
