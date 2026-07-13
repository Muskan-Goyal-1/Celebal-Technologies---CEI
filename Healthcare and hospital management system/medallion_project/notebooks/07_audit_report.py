"""
Notebook 07 -- audit_report
Layer: Ops
Purpose: Query audit log table to produce pipeline run summary. Display row
         counts, durations, failures.
Ref: PDD section 7.2 (What the Audit Log Enables).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.spark_utils import get_spark, read_table, PROJECT_ROOT
from pyspark.sql import functions as F

spark = get_spark("07_audit_report")
audit = read_table(spark, "audit", "audit_log")

print("=" * 90)
print("PIPELINE RUN SUMMARY (all batches on file)")
print("=" * 90)
audit.orderBy("layer", "source_name").select(
    "layer", "source_name", "status", "rows_read", "rows_written", "rows_rejected",
    "pipeline_duration_secs", "dq_score_avg", "sla_met"
).show(50, truncate=False)

print("Failure investigation -- any non-SUCCESS runs:")
failures = audit.filter(F.col("status") != "SUCCESS")
if failures.count() == 0:
    print("  None. All pipeline runs completed successfully.")
else:
    failures.select("layer", "source_name", "status", "error_message", "created_at").show(truncate=False)

print("SLA monitoring -- duration by layer:")
audit.groupBy("layer").agg(
    F.round(F.avg("pipeline_duration_secs"), 1).alias("avg_duration_secs"),
    F.sum(F.col("sla_met").cast("int")).alias("runs_met_sla"),
    F.count("*").alias("total_runs"),
).orderBy("layer").show()

print("Data quality trend -- rows rejected & avg DQ score by source:")
audit.filter(F.col("layer") == "SILVER").select(
    "source_name", "rows_read", "rows_rejected", "dq_score_avg"
).orderBy("source_name").show(truncate=False)

# ---- write a markdown summary report for stakeholders ----
rows = audit.orderBy("layer", "source_name").collect()
lines = ["# Pipeline Audit Report", "", f"Generated from `data/audit/audit_log`\n", "", "| Layer | Source | Status | Rows Read | Rows Written | Rows Rejected | Duration (s) | Avg DQ Score | SLA Met |",
          "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    lines.append(f"| {r['layer']} | {r['source_name']} | {r['status']} | {r['rows_read']} | {r['rows_written']} | "
                  f"{r['rows_rejected']} | {r['pipeline_duration_secs']} | "
                  f"{'' if r['dq_score_avg'] is None else round(r['dq_score_avg'],3)} | {r['sla_met']} |")
report_path = os.path.join(PROJECT_ROOT, "reports", "audit_report.md")
with open(report_path, "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"\nMarkdown report written to {report_path}")

spark.stop()
