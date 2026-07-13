# Pipeline Audit Report

Generated from `data/audit/audit_log`


| Layer | Source | Status | Rows Read | Rows Written | Rows Rejected | Duration (s) | Avg DQ Score | SLA Met |
|---|---|---|---|---|---|---|---|---|
| BRONZE | appointments | SUCCESS | 1500 | 1500 | 0 | 3 |  | True |
| BRONZE | billing_claims | SUCCESS | 1400 | 1400 | 0 | 3 |  | True |
| BRONZE | lab_results | SUCCESS | 900 | 900 | 0 | 2 |  | True |
| BRONZE | medications | SUCCESS | 600 | 600 | 0 | 2 |  | True |
| BRONZE | patient_master | SUCCESS | 306 | 306 | 0 | 9 |  | True |
| GOLD | gold_kpi_summary | SUCCESS | 3500 | 8 | 0 | 18 |  | True |
| SILVER | silver_appointments | SUCCESS | 1500 | 1500 | 6 | 13 | 1.0 | True |
| SILVER | silver_billing | SUCCESS | 1400 | 1400 | 44 | 13 | 0.992 | True |
| SILVER | silver_lab | SUCCESS | 900 | 900 | 17 | 10 | 0.995 | True |
| SILVER | silver_medications | SUCCESS | 600 | 600 | 14 | 2 | 0.977 | True |
| SILVER | silver_patients | SUCCESS | 306 | 300 | 7 | 13 | 0.795 | True |
