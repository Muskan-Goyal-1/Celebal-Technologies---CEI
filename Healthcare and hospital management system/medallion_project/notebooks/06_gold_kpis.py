"""
Notebook 06 -- gold_kpis
Layer: Gold
Purpose: Compute all 8 KPIs from Silver tables. Writes to gold_kpi_summary
         and individual KPI Delta tables.
Ref: PDD section 5.3 (Gold metadata columns), section 9 (KPI definitions
     & thresholds).
"""
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.spark_utils import get_spark, save_table, read_table, append_audit_log, new_batch_id, now_ts, ENVIRONMENT
from pyspark.sql import functions as F

spark = get_spark("06_gold_kpis")
batch_id = new_batch_id()
start = now_ts()
report_date = now_ts().date()

appts = read_table(spark, "silver", "silver_appointments").filter("_is_current = true")
billing = read_table(spark, "silver", "silver_billing").filter("_is_current = true")
meds = read_table(spark, "silver", "silver_medications").filter("_is_current = true")

def gold_meta(df, kpi_period, silver_sources, dept_col=None):
    d = (df
        .withColumn("_gold_load_timestamp", F.current_timestamp())
        .withColumn("_gold_batch_id", F.lit(batch_id))
        .withColumn("_kpi_period", F.lit(kpi_period))
        .withColumn("_kpi_version", F.lit(1))
        .withColumn("_silver_source_tables", F.lit(silver_sources))
        .withColumn("_department_id", F.col(dept_col) if dept_col else F.lit("ALL"))
        .withColumn("_report_as_of_date", F.lit(report_date))
        .withColumn("_is_restatement", F.lit(False))
    )
    return d

def threshold_status(value, good_if, threshold):
    """good_if: 'lt' (value < threshold is GREEN) or 'gt' (value > threshold is GREEN)."""
    if value is None:
        return "AMBER"
    if good_if == "lt":
        if value < threshold: return "GREEN"
        if value < threshold * 1.25: return "AMBER"
        return "RED"
    else:
        if value > threshold: return "GREEN"
        if value > threshold * 0.9: return "AMBER"
        return "RED"

kpi_rows = []  # (kpi_name, value, unit, threshold_label, threshold_status)

# 1. Patient No-Show Rate = No-shows / Total Appts * 100  (target < 10%)
total_appts = appts.count()
no_shows = appts.filter(F.col("is_no_show") == True).count()
no_show_rate = round(100.0 * no_shows / total_appts, 2) if total_appts else None
kpi_rows.append(("patient_no_show_rate", no_show_rate, "%", "< 10%", threshold_status(no_show_rate, "lt", 10)))

# 2. Average Length of Stay (ALOS) = SUM(discharge-admit)/COUNT(patients)  (benchmark by dept)
alos_row = appts.filter(F.col("length_of_stay_days").isNotNull()).agg(
    F.sum("length_of_stay_days").alias("total_days"), F.countDistinct("patient_id").alias("n_patients")
).first()
alos = round(alos_row["total_days"] / alos_row["n_patients"], 2) if alos_row and alos_row["n_patients"] else None
kpi_rows.append(("average_length_of_stay", alos, "days", "benchmark by dept", "AMBER" if alos is None else "GREEN"))

# 3. HCAHPS Satisfaction Score = AVG(patient_satisfaction_score)  (target > 85%)
hcahps_row = appts.filter(F.col("patient_satisfaction_score").isNotNull()).agg(
    F.avg("patient_satisfaction_score").alias("avg_score"))
hcahps = round(hcahps_row.first()["avg_score"], 2) if hcahps_row.first()["avg_score"] is not None else None
kpi_rows.append(("hcahps_satisfaction_score", hcahps, "%", "> 85%", threshold_status(hcahps, "gt", 85)))

# 4. Billing Accuracy Rate = Accurate Bills / Total Bills * 100  (target > 98%)
total_bills = billing.count()
accurate_bills = billing.filter(F.col("is_billing_accurate") == True).count()
billing_accuracy = round(100.0 * accurate_bills / total_bills, 2) if total_bills else None
kpi_rows.append(("billing_accuracy_rate", billing_accuracy, "%", "> 98%", threshold_status(billing_accuracy, "gt", 98)))

# 5. Insurance Claim Approval Rate = Approved Claims / Total Claims * 100  (target > 95%)
total_claims = billing.count()
approved_claims = billing.filter(F.col("is_claim_approved") == True).count()
claim_approval_rate = round(100.0 * approved_claims / total_claims, 2) if total_claims else None
kpi_rows.append(("insurance_claim_approval_rate", claim_approval_rate, "%", "> 95%", threshold_status(claim_approval_rate, "gt", 95)))

# 6. Medication Inventory Turnover = Units Dispensed / Avg Inventory Units  (target 4-6x/year)
med_agg = meds.filter(F.col("valid_quantity") == True).agg(
    F.sum("quantity_dispensed_clean").alias("units_dispensed"),
    F.avg("inventory_on_hand").alias("avg_inventory")
).first()
turnover = round(med_agg["units_dispensed"] / med_agg["avg_inventory"], 2) if med_agg["avg_inventory"] else None
turnover_status = "GREEN" if turnover is not None and 4 <= turnover <= 6 else ("AMBER" if turnover is not None else "AMBER")
kpi_rows.append(("medication_inventory_turnover", turnover, "x/year", "4-6x per year", turnover_status))

# 7. Operating Cost per Patient = Total Operating Cost / Unique Patients  (billing + medications)
total_billing_cost = billing.agg(F.sum("charge_amount")).first()[0] or 0
total_med_cost = meds.filter(F.col("valid_quantity") == True).agg(F.sum("total_cost")).first()[0] or 0
unique_patients = appts.select("patient_id").distinct().count()
op_cost_per_patient = round((float(total_billing_cost) + float(total_med_cost)) / unique_patients, 2) if unique_patients else None
kpi_rows.append(("operating_cost_per_patient", op_cost_per_patient, "$", "below dept budget", "AMBER"))

# 8. Patient Readmission Rate = Readmissions within 30 days / Discharges * 100  (target < 15%)
discharges = appts.filter((F.col("visit_type") == "Inpatient") & F.col("discharge_date").isNotNull())
w_pat = __import__("pyspark.sql.window", fromlist=["Window"]).Window.partitionBy("patient_id").orderBy("discharge_date")
disch_dated = discharges.withColumn("discharge_dt", F.to_date("discharge_date"))
disch_dated = disch_dated.withColumn("prev_discharge", F.lag("discharge_dt").over(w_pat))
disch_dated = disch_dated.withColumn("days_since_prev", F.datediff(F.col("discharge_dt"), F.col("prev_discharge")))
total_discharges = disch_dated.count()
readmissions = disch_dated.filter((F.col("days_since_prev").isNotNull()) & (F.col("days_since_prev") <= 30)).count()
readmission_rate = round(100.0 * readmissions / total_discharges, 2) if total_discharges else None
kpi_rows.append(("patient_readmission_rate", readmission_rate, "%", "< 15%", threshold_status(readmission_rate, "lt", 15)))

# ---- write gold_kpi_summary (one row per KPI, wide dashboard-ready table) ----
summary_schema_rows = [(name, val, unit, thr, status) for name, val, unit, thr, status in kpi_rows]
summary_df = spark.createDataFrame(summary_schema_rows, schema="kpi_name string, kpi_value double, unit string, target_threshold string, threshold_status string")
summary_df = gold_meta(summary_df, "DAILY", "silver_appointments,silver_billing,silver_medications")
save_table(summary_df, "gold", "gold_kpi_summary", mode="overwrite")

# ---- also write per-department breakdown for the KPIs that support it (dashboard drill-down) ----
dept_no_show = (appts.groupBy("department")
    .agg(F.count("*").alias("total_appts"), F.sum(F.col("is_no_show").cast("int")).alias("no_shows"))
    .withColumn("no_show_rate_pct", F.round(100.0 * F.col("no_shows") / F.col("total_appts"), 2)))
dept_no_show = gold_meta(dept_no_show, "DAILY", "silver_appointments", dept_col="department")
save_table(dept_no_show, "gold", "gold_no_show_by_department", mode="overwrite")

dept_alos = (appts.filter(F.col("length_of_stay_days").isNotNull())
    .groupBy("department")
    .agg(F.round(F.avg("length_of_stay_days"), 2).alias("avg_length_of_stay_days")))
dept_alos = gold_meta(dept_alos, "DAILY", "silver_appointments", dept_col="department")
save_table(dept_alos, "gold", "gold_alos_by_department", mode="overwrite")

print("Gold KPI Summary:")
for name, val, unit, thr, status in kpi_rows:
    print(f"  {name:32s} = {val}{unit:8s} (target {thr:18s}) -> {status}")

end = now_ts()
append_audit_log(spark, [{
    "audit_id": str(uuid.uuid4()), "batch_id": batch_id, "source_name": "gold_kpi_summary",
    "layer": "GOLD", "pipeline_start_time": start, "pipeline_end_time": end,
    "rows_read": total_appts + total_bills + meds.count(), "rows_written": len(kpi_rows), "rows_rejected": 0,
    "status": "SUCCESS", "error_message": None, "triggered_by": "scheduler",
    "created_at": now_ts(), "pipeline_duration_secs": int((end - start).total_seconds()),
    "notebook_name": "06_gold_kpis", "cluster_id": "local-cluster",
    "spark_app_id": spark.sparkContext.applicationId, "rows_quarantined": 0,
    "dq_score_avg": None, "schema_version": "v1.0",
    "environment": ENVIRONMENT, "retry_attempt": 0, "data_classification": "INTERNAL",
    "sla_met": True, "downstream_notified": True,
}])

spark.stop()
