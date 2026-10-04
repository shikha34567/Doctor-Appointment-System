import os
import sys
import json
import sqlite3
import hashlib
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import engine, SessionLocal, Base
from database.models import (
    User, Patient, Physician, Department, Bed, Appointment, OperationalConfig
)


def hash_scrypt_password(password: str, salt: str = None) -> tuple[str, str]:
    """Compatible with existing Node.js scrypt format (n=16384, r=8, p=1, dklen=64)"""
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt.encode("utf-8"),
        n=16384,
        r=8,
        p=1,
        dklen=64
    ).hex()
    return hashed, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    calc_hash, _ = hash_scrypt_password(password, salt)
    return calc_hash == stored_hash


DEPARTMENTS_DATA = [
    {"id": "dep-cardio", "name": "Cardiology", "code": "CARD", "total_beds": 45, "icu_beds": 10, "emergency_beds": 10, "general_beds": 25, "nurse_ratio": 3.0, "physician_ratio": 8.0},
    {"id": "dep-genmed", "name": "General Medicine", "code": "GMED", "total_beds": 50, "icu_beds": 5, "emergency_beds": 15, "general_beds": 30, "nurse_ratio": 4.0, "physician_ratio": 10.0},
    {"id": "dep-neuro", "name": "Neurology", "code": "NEUR", "total_beds": 35, "icu_beds": 8, "emergency_beds": 7, "general_beds": 20, "nurse_ratio": 3.0, "physician_ratio": 8.0},
    {"id": "dep-ortho", "name": "Orthopedics", "code": "ORTH", "total_beds": 40, "icu_beds": 4, "emergency_beds": 8, "general_beds": 28, "nurse_ratio": 4.0, "physician_ratio": 10.0},
    {"id": "dep-pedia", "name": "Pediatrics", "code": "PED", "total_beds": 35, "icu_beds": 6, "emergency_beds": 9, "general_beds": 20, "nurse_ratio": 3.5, "physician_ratio": 8.0},
    {"id": "dep-derma", "name": "Dermatology", "code": "DERM", "total_beds": 20, "icu_beds": 0, "emergency_beds": 2, "general_beds": 18, "nurse_ratio": 5.0, "physician_ratio": 12.0},
    {"id": "dep-ent", "name": "ENT", "code": "ENT", "total_beds": 25, "icu_beds": 2, "emergency_beds": 3, "general_beds": 20, "nurse_ratio": 4.5, "physician_ratio": 10.0},
    {"id": "dep-opht", "name": "Ophthalmology", "code": "OPHT", "total_beds": 20, "icu_beds": 0, "emergency_beds": 2, "general_beds": 18, "nurse_ratio": 5.0, "physician_ratio": 12.0},
    {"id": "dep-gastro", "name": "Gastroenterology", "code": "GAST", "total_beds": 30, "icu_beds": 5, "emergency_beds": 5, "general_beds": 20, "nurse_ratio": 4.0, "physician_ratio": 9.0},
    {"id": "dep-gynec", "name": "Gynecology & Obstetrics", "code": "GYN", "total_beds": 40, "icu_beds": 6, "emergency_beds": 8, "general_beds": 26, "nurse_ratio": 3.5, "physician_ratio": 8.0},
    {"id": "dep-psych", "name": "Psychiatry", "code": "PSYC", "total_beds": 25, "icu_beds": 0, "emergency_beds": 5, "general_beds": 20, "nurse_ratio": 4.0, "physician_ratio": 10.0},
]


def init_database():
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Departments
        dept_id_map = {}
        for d in DEPARTMENTS_DATA:
            existing = db.query(Department).filter_by(id=d["id"]).first()
            if not existing:
                dept = Department(
                    id=d["id"],
                    name=d["name"],
                    code=d["code"],
                    total_beds=d["total_beds"],
                    icu_beds=d["icu_beds"],
                    emergency_beds=d["emergency_beds"],
                    general_beds=d["general_beds"],
                    target_nurse_ratio=d["nurse_ratio"],
                    target_physician_ratio=d["physician_ratio"]
                )
                db.add(dept)
                dept_id_map[d["name"]] = d["id"]
            else:
                dept_id_map[d["name"]] = existing.id
        db.commit()
        print(f"Departments initialized ({len(DEPARTMENTS_DATA)} departments).")

        # 2. Seed Beds for each department
        bed_count = db.query(Bed).count()
        if bed_count == 0:
            for dept_info in DEPARTMENTS_DATA:
                dept_id = dept_info["id"]
                code = dept_info["code"]
                # ICU beds
                for b in range(1, dept_info["icu_beds"] + 1):
                    bed = Bed(
                        bed_id=f"BED-{code}-ICU-{b:02d}",
                        department_id=dept_id,
                        hospital_unit="ICU",
                        bed_type="ICU-Ventilator",
                        status="Available",
                        room_number=f"ICU-Room-{b:02d}"
                    )
                    db.add(bed)
                # Emergency beds
                for b in range(1, dept_info["emergency_beds"] + 1):
                    bed = Bed(
                        bed_id=f"BED-{code}-EMG-{b:02d}",
                        department_id=dept_id,
                        hospital_unit="Emergency",
                        bed_type="Standard",
                        status="Available",
                        room_number=f"ER-Bay-{b:02d}"
                    )
                    db.add(bed)
                # General beds
                for b in range(1, dept_info["general_beds"] + 1):
                    bed = Bed(
                        bed_id=f"BED-{code}-GEN-{b:02d}",
                        department_id=dept_id,
                        hospital_unit="General Ward",
                        bed_type="Standard",
                        status="Available",
                        room_number=f"GW-Room-{b:02d}"
                    )
                    db.add(bed)
            db.commit()
            print("Hospital beds generated and seeded across all departments.")

        # 3. Seed Doctors and Physicians from doctors_registry.json
        doctors_path = os.path.join(os.path.dirname(__file__), "..", "data", "doctors_registry.json")
        if os.path.exists(doctors_path):
            with open(doctors_path, "r", encoding="utf-8") as f:
                doctors = json.load(f)

            for doc in doctors:
                doc_id = doc["id"]
                email = doc["email"].lower()
                name = doc["name"]
                specialty = doc["specialty"]

                user = db.query(User).filter_by(doctor_id=doc_id).first()
                if not user:
                    pw = f"Doctor#{doc_id}2026!"
                    pwd_hash, salt = hash_scrypt_password(pw)
                    user = User(
                        id=f"usr-{doc_id}",
                        email=email,
                        password_hash=pwd_hash,
                        salt=salt,
                        role="Physician",
                        name=name,
                        phone=doc.get("phone", "+91 98400 00000"),
                        doctor_id=doc_id,
                        is_active=True
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)

                physician = db.query(Physician).filter_by(doctor_id=doc_id).first()
                if not physician:
                    physician = Physician(
                        doctor_id=doc_id,
                        user_id=user.id,
                        name=name,
                        email=email,
                        specialty=specialty,
                        qualification=doc.get("qualification", "MBBS, MD"),
                        experience=doc.get("experience", "10+ Years"),
                        fee=float(doc.get("fee", 700.0)),
                        availability=doc.get("availability", "Mon - Fri (09:00 AM - 04:00 PM)"),
                        room=doc.get("room", "General Consultation Room"),
                        languages=doc.get("languages", "English, Hindi"),
                        bio=doc.get("bio", ""),
                        phone=doc.get("phone", "+91 98400 00000")
                    )
                    db.add(physician)
            db.commit()
            print(f"Physicians and Physician User accounts verified ({len(doctors)} doctors).")

        # 4. Seed Patients
        sample_patients = [
            {
                "id": "usr-pat-101",
                "name": "Ananya Raman",
                "email": "ananya.raman@healthcare.demo",
                "phone": "+91 98401 99999",
                "password": "Patient#Secure2026!",
                "age": 32,
                "gender": "Female",
                "blood_group": "O+",
                "mrn": "MRN-PAT-101"
            },
            {
                "id": "usr-pat-102",
                "name": "Karthik Verma",
                "email": "karthik.verma@healthcare.demo",
                "phone": "+91 98402 88888",
                "password": "Patient#Secure2026!",
                "age": 48,
                "gender": "Male",
                "blood_group": "B+",
                "mrn": "MRN-PAT-102"
            }
        ]

        for pat in sample_patients:
            u = db.query(User).filter_by(email=pat["email"]).first()
            if not u:
                pwd_hash, salt = hash_scrypt_password(pat["password"])
                u = User(
                    id=pat["id"],
                    email=pat["email"],
                    password_hash=pwd_hash,
                    salt=salt,
                    role="Patient",
                    name=pat["name"],
                    phone=pat["phone"],
                    is_active=True
                )
                db.add(u)
                db.commit()
                db.refresh(u)

            p_profile = db.query(Patient).filter_by(user_id=u.id).first()
            if not p_profile:
                p_profile = Patient(
                    id=f"profile-{pat['id']}",
                    user_id=u.id,
                    medical_record_num=pat["mrn"],
                    age=pat["age"],
                    gender=pat["gender"],
                    blood_group=pat["blood_group"],
                    emergency_contact=pat["phone"]
                )
                db.add(p_profile)
        db.commit()
        print("Test Patients verified.")

        # 5. Seed Hospital Operations Manager
        admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin.operations@healthcare.demo").lower()
        admin_pw = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin#Operations2026!")
        admin_name = os.getenv("INITIAL_ADMIN_NAME", "Hospital Operations Manager")

        admin_user = db.query(User).filter_by(email=admin_email).first()
        if not admin_user:
            pwd_hash, salt = hash_scrypt_password(admin_pw)
            admin_user = User(
                id="usr-ops-mgr-001",
                email=admin_email,
                password_hash=pwd_hash,
                salt=salt,
                role="OperationsManager",
                name=admin_name,
                phone="+91 98400 11223",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print(f"Hospital Operations Manager account provisioned: {admin_email}")

        # 6. Migrate existing appointments from healthcare.db if present and new DB is empty
        appt_count = db.query(Appointment).count()
        if appt_count == 0:
            old_db_path = os.path.join(os.path.dirname(__file__), "..", "data", "healthcare.db")
            if os.path.exists(old_db_path):
                try:
                    con = sqlite3.connect(old_db_path)
                    cur = con.cursor()
                    rows = cur.execute("SELECT id, patient_id, patient_name, patient_email, patient_phone, patient_age, patient_gender, doctor_id, doctor_name, specialty, appointment_date, time_slot, status, fee, room, notes, created_at FROM appointments").fetchall()
                    con.close()

                    for r in rows:
                        new_appt = Appointment(
                            id=r[0],
                            patient_id=r[1],
                            patient_name=r[2],
                            patient_email=r[3],
                            patient_phone=r[4],
                            patient_age=r[5],
                            patient_gender=r[6],
                            doctor_id=r[7],
                            doctor_name=r[8],
                            specialty=r[9],
                            appointment_date=r[10],
                            time_slot=r[11],
                            status=r[12],
                            fee=r[13],
                            room=r[14],
                            notes=r[15],
                            created_at=datetime.utcnow()
                        )
                        db.add(new_appt)
                    db.commit()
                    print(f"Migrated {len(rows)} legacy appointments successfully.")
                except Exception as e:
                    print(f"Notice: legacy appointment migration skipped ({e})")

        # 7. Seed Operational Config
        default_configs = [
            ("target_bed_occupancy_pct", "85.0", "Target bed occupancy safety threshold percentage"),
            ("max_emergency_wait_minutes", "60.0", "Maximum acceptable emergency waiting threshold in minutes"),
            ("nurse_to_patient_ratio_icu", "2.0", "Target nurse-to-patient ratio in Intensive Care Units"),
            ("nurse_to_patient_ratio_general", "4.0", "Target nurse-to-patient ratio in General Inpatient Wards"),
            ("system_data_mode", "SYNTHETIC_DEMO", "Data lineage mode indicator")
        ]
        for key, val, desc in default_configs:
            cfg = db.query(OperationalConfig).filter_by(config_key=key).first()
            if not cfg:
                db.add(OperationalConfig(config_key=key, config_value=val, description=desc))
        db.commit()
        print("Operational configuration defaults initialized.")

    finally:
        db.close()


if __name__ == "__main__":
    init_database()
