"""
Synthetic data generator for the 5 flat-CSV source systems described in the PDD.
Produces messy, realistic data (nulls, dupes, out-of-range values) so the
Silver-layer DQ logic in this project has something real to clean.
"""
import csv
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)
OUT = "data/landing"

FIRST = ["James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda","David","Elizabeth",
         "William","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Charles","Karen"]
LAST = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
        "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"]
INSURERS = ["BlueCross BlueShield","UnitedHealth","Aetna","Cigna","Medicare","Medicaid","Humana"]
DEPTS = ["Cardiology","Orthopedics","Emergency","Oncology","Pediatrics","Neurology","General Medicine"]
DOCTORS = [("DOC%03d" % i, random.choice(FIRST)+" "+random.choice(LAST)) for i in range(1, 26)]
CHRONIC = ["Diabetes","Hypertension","Asthma","None","None","None","COPD","Heart Disease"]
DRUGS = [("NDC%05d" % i, name) for i, name in enumerate(
    ["Lisinopril","Metformin","Atorvastatin","Amlodipine","Metoprolol","Albuterol",
     "Omeprazole","Losartan","Gabapentin","Hydrochlorothiazide"], start=1)]
TESTS = [("CBC","4.5-11.0","10^3/uL"),("Glucose","70-100","mg/dL"),("A1C","4.0-5.6","%"),
         ("Cholesterol","<200","mg/dL"),("Creatinine","0.6-1.2","mg/dL"),("Potassium","3.5-5.0","mmol/L")]

N_PATIENTS = 300
N_APPTS = 1500
N_LABS = 900
N_MEDS = 600

def rand_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

patients = []
with open(f"{OUT}/patient_master.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["patient_id","first_name","last_name","dob","gender","ssn","phone","address","city",
                "state","zip","insurance_provider","insurance_id","blood_type","chronic_conditions",
                "registration_date"])
    for i in range(1, N_PATIENTS + 1):
        pid = f"PT{i:05d}"
        patients.append(pid)
        dob = rand_date(datetime(1935,1,1), datetime(2015,12,31)).strftime("%Y-%m-%d")
        ssn = f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
        phone = f"555-{random.randint(200,999)}-{random.randint(1000,9999)}"
        row = [pid, random.choice(FIRST), random.choice(LAST), dob, random.choice(["M","F"]), ssn, phone,
               f"{random.randint(100,9999)} Main St", "Springfield", "IL", f"{random.randint(60000,62999)}",
               random.choice(INSURERS), f"INS{random.randint(100000,999999)}",
               random.choice(["A+","A-","B+","B-","O+","O-","AB+","AB-"]),
               random.choice(CHRONIC), rand_date(datetime(2015,1,1), datetime(2026,4,1)).strftime("%Y-%m-%d")]
        # inject nulls (~4%)
        if random.random() < 0.04:
            row[7] = ""  # missing address
        if random.random() < 0.03:
            row[11] = ""  # missing insurance
        w.writerow(row)
    # inject a few exact duplicate rows
    for _ in range(6):
        w.writerow(w.writerow and None) if False else None
# re-open to append true duplicates (simplest: duplicate first 6 patient rows verbatim)
with open(f"{OUT}/patient_master.csv") as f:
    lines = f.readlines()
with open(f"{OUT}/patient_master.csv", "a") as f:
    for line in lines[1:7]:
        f.write(line)

appt_rows = []
with open(f"{OUT}/appointments.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["appointment_id","patient_id","doctor_id","doctor_name","department","appointment_date",
                "appointment_time","duration_minutes","status","visit_type","patient_satisfaction_score",
                "admit_date","discharge_date"])
    for i in range(1, N_APPTS + 1):
        aid = f"APT{i:06d}"
        pid = random.choice(patients)
        doc_id, doc_name = random.choice(DOCTORS)
        dept = random.choice(DEPTS)
        appt_date = rand_date(datetime(2025,7,1), datetime(2026,4,1))
        status = random.choices(["Completed","No-Show","Cancelled"], weights=[80,12,8])[0]
        visit_type = random.choice(["Outpatient","Inpatient","Emergency"])
        satisfaction = random.randint(60,100) if status == "Completed" else None
        admit = appt_date.strftime("%Y-%m-%d") if visit_type == "Inpatient" else ""
        discharge = (appt_date + timedelta(days=random.randint(1,9))).strftime("%Y-%m-%d") if visit_type == "Inpatient" else ""
        dur = random.choice([15,30,45,60]) if status != "No-Show" else 0
        row = [aid, pid, doc_id, doc_name, dept, appt_date.strftime("%Y-%m-%d"),
               f"{random.randint(8,17):02d}:{random.choice(['00','15','30','45'])}", dur, status, visit_type,
               satisfaction if satisfaction is not None else "", admit, discharge]
        # inject a few bad dates (discharge before admit)
        if visit_type == "Inpatient" and random.random() < 0.02:
            row[12] = (appt_date - timedelta(days=2)).strftime("%Y-%m-%d")
        appt_rows.append(row)
        w.writerow(row)

with open(f"{OUT}/billing_claims.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["claim_id","patient_id","appointment_id","charge_code","charge_amount","insurance_provider",
                "claim_status","claim_amount","payment_amount","billing_date","payment_date","department"])
    for i, appt in enumerate(random.sample(appt_rows, k=min(1400, len(appt_rows))), start=1):
        aid, pid, doc_id, doc_name, dept, appt_date = appt[0], appt[1], appt[2], appt[3], appt[4], appt[5]
        cid = f"CLM{i:06d}"
        charge = round(random.uniform(80, 5000), 2)
        claim_status = random.choices(["Approved","Denied","Pending"], weights=[78,12,10])[0]
        claim_amt = charge
        payment_amt = round(charge * random.uniform(0.6,1.0), 2) if claim_status == "Approved" else 0
        billing_date = appt_date
        payment_date = appt_date if claim_status == "Approved" else ""
        row = [cid, pid, aid, f"CPT{random.randint(10000,99999)}", charge, random.choice(INSURERS),
               claim_status, claim_amt, payment_amt, billing_date, payment_date, dept]
        # inject some charge-code errors / missing charge amounts (~3%)
        if random.random() < 0.03:
            row[4] = ""
        w.writerow(row)

with open(f"{OUT}/lab_results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["lab_id","patient_id","appointment_id","test_name","test_date","result_value","unit",
                "reference_range","abnormal_flag","ordering_doctor"])
    for i in range(1, N_LABS + 1):
        lid = f"LAB{i:06d}"
        pid = random.choice(patients)
        appt = random.choice(appt_rows)
        test_name, ref_range, unit = random.choice(TESTS)
        val = round(random.uniform(1, 300), 1)
        abnormal = "Y" if random.random() < 0.15 else "N"
        row = [lid, pid, appt[0], test_name, appt[5], val, unit, ref_range, abnormal, appt[3]]
        if random.random() < 0.02:
            row[5] = ""  # missing result value
        w.writerow(row)

with open(f"{OUT}/medications.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["med_id","patient_id","drug_name","ndc_code","quantity_dispensed","unit_cost",
                "dispense_date","inventory_on_hand","reorder_level","pharmacy_location"])
    for i in range(1, N_MEDS + 1):
        mid = f"MED{i:06d}"
        pid = random.choice(patients)
        ndc, drug = random.choice(DRUGS)
        qty = random.randint(10,90)
        cost = round(random.uniform(0.5, 45.0), 2)
        row = [mid, pid, drug, ndc, qty, cost,
               rand_date(datetime(2025,7,1), datetime(2026,4,1)).strftime("%Y-%m-%d"),
               random.randint(0,500), random.randint(20,100), random.choice(["Main Pharmacy","Satellite-A","Satellite-B"])]
        if random.random() < 0.025:
            row[4] = -5  # bad negative quantity (data quality issue)
        w.writerow(row)

print("Generated 5 source CSVs in", OUT)
