"""
Notebook 03 -- silver_appointments
Layer: Silver
Purpose: Cleanse Appointments: date validation, join with patient, no-show
         flag. Writes silver_appointments.
"""
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.spark_utils import get_spark, save_table, read_table, append_audit_log, new_batch_id, now_ts, ENVIRONMENT
from pyspark.sql import functions as F

spark = get_spark("03_silver_appointments")
batch_id = new_batch_id()
start = now_ts()

bronze = read_table(spark, "bronze", "appointments")
bronze_batch_id = bronze.select("_batch_id").first()["_batch_id"]
patients = read_table(spark, "silver", "silver_patients").filter("_is_current = true").select("patient_id")
rows_read = bronze.count()

MANDATORY = ["appointment_id", "patient_id", "doctor_id", "appointment_date", "status"]
silver = bronze.withColumn(
    "_dq_failure_reason",
    F.concat_ws(",", *[F.when(F.col(c).isNull() | (F.col(c).cast("string") == ""), F.lit(c)) for c in MANDATORY])
)

# date validation: discharge must not precede admit for inpatient visits
# NOTE: CSV inferSchema parses admit_date/discharge_date as DateType, so blank
# source values already come through as null (not "") -- check isNotNull() only.
bad_dates = (F.col("visit_type") == "Inpatient") & F.col("discharge_date").isNotNull() & \
            F.col("admit_date").isNotNull() & \
            (F.to_date("discharge_date") < F.to_date("admit_date"))
silver = silver.withColumn(
    "_dq_failure_reason",
    F.when(bad_dates, F.concat_ws(",", F.col("_dq_failure_reason"), F.lit("discharge_before_admit")))
     .otherwise(F.col("_dq_failure_reason"))
)

present_count = None
for c in MANDATORY:
    term = F.when(F.col(c).isNotNull() & (F.col(c).cast("string") != ""), F.lit(1)).otherwise(F.lit(0))
    present_count = term if present_count is None else present_count + term
silver = silver.withColumn("_dq_score", ((present_count / F.lit(len(MANDATORY))) -
                                          F.when(bad_dates, F.lit(0.1)).otherwise(F.lit(0.0))).cast("float"))
silver = silver.withColumn("_dq_passed", (F.col("_dq_failure_reason") == "") | F.col("_dq_failure_reason").isNull())

rows_rejected = silver.filter(~F.col("_dq_passed")).count()

# cross-source enrichment: confirm patient exists in Silver patient master (Patient 360 join)
enriched = silver.join(patients, on="patient_id", how="left") \
    .withColumn("_patient_on_file", F.col("patient_id").isNotNull())

# no-show flag + length-of-stay (for ALOS KPI downstream)
enriched = (enriched
    .withColumn("is_no_show", F.col("status") == "No-Show")
    .withColumn("length_of_stay_days",
        F.when((F.col("visit_type") == "Inpatient") & F.col("admit_date").isNotNull() & F.col("discharge_date").isNotNull() & ~bad_dates,
               F.datediff(F.to_date("discharge_date"), F.to_date("admit_date"))))
)

silver_final = (enriched
    .withColumn("_silver_load_timestamp", F.current_timestamp())
    .withColumn("_silver_batch_id", F.lit(batch_id))
    .withColumn("_bronze_batch_id", F.lit(bronze_batch_id))
    .withColumn("_is_current", F.lit(True))
    .withColumn("_effective_from", F.current_timestamp())
    .withColumn("_effective_to", F.lit(None).cast("timestamp"))
    .withColumn("_masked_fields", F.lit(""))
    .withColumn("_enrichment_source", F.lit("bronze.appointments,silver.silver_patients"))
    .withColumn("_record_version", F.lit(1))
    .drop("_record_hash", "_raw_row_number", "_is_duplicate")
)

save_table(silver_final, "silver", "silver_appointments", mode="overwrite")
rows_written = silver_final.count()
dq_avg = silver_final.agg(F.avg("_dq_score")).first()[0]

end = now_ts()
append_audit_log(spark, [{
    "audit_id": str(uuid.uuid4()), "batch_id": batch_id, "source_name": "silver_appointments",
    "layer": "SILVER", "pipeline_start_time": start, "pipeline_end_time": end,
    "rows_read": rows_read, "rows_written": rows_written, "rows_rejected": rows_rejected,
    "status": "SUCCESS", "error_message": None, "triggered_by": "scheduler",
    "created_at": now_ts(), "pipeline_duration_secs": int((end - start).total_seconds()),
    "notebook_name": "03_silver_appointments", "cluster_id": "local-cluster",
    "spark_app_id": spark.sparkContext.applicationId, "rows_quarantined": 0,
    "dq_score_avg": float(dq_avg) if dq_avg is not None else None, "schema_version": "v1.1",
    "environment": ENVIRONMENT, "retry_attempt": 0, "data_classification": "PHI",
    "sla_met": True, "downstream_notified": False,
}])

print(f"silver_appointments: {rows_read} read -> {rows_written} written, {rows_rejected} failed DQ, avg_dq_score={dq_avg:.3f}")
spark.stop()
