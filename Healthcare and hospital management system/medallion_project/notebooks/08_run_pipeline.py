"""
08_run_pipeline -- orchestrator
Implements PDD section 8.1 Execution Order:
  Step 1 - Notebook 00 once (setup)
  Step 2 - Notebook 01 (Bronze ingest)          -- can be scheduled daily
  Step 3 - Notebooks 02-05 (Silver)             -- after Bronze completes; can run in parallel
  Step 4 - Notebook 06 (Gold KPIs)              -- after all Silver tables are ready
  Step 5 - Notebook 07 (Audit Report)           -- for monitoring
"""
import subprocess, sys, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
NOTEBOOKS_IN_ORDER = [
    "00_setup_config.py",
    "01_ingest_bronze.py",
    "02_silver_patients.py",
    "03_silver_appointments.py",
    "04_silver_billing.py",
    "05_silver_lab_meds.py",
    "06_gold_kpis.py",
    "07_audit_report.py",
]

def run(nb):
    print(f"\n{'='*90}\n RUNNING {nb}\n{'='*90}")
    t0 = time.time()
    result = subprocess.run([sys.executable, os.path.join(HERE, nb)], capture_output=True, text=True)
    dur = time.time() - t0
    # filter noisy Spark logs
    for line in result.stdout.splitlines():
        if not any(noisy in line for noisy in ["WARN", "Stage", "26/07", "27/", "setLogLevel"]):
            print(line)
    if result.returncode != 0:
        print(f"\n!!! {nb} FAILED (exit {result.returncode}) !!!")
        print(result.stderr[-3000:])
        sys.exit(result.returncode)
    print(f"-- {nb} completed in {dur:.1f}s --")

if __name__ == "__main__":
    for nb in NOTEBOOKS_IN_ORDER:
        run(nb)
    print("\nPipeline run complete. All 8 notebooks executed successfully.")
