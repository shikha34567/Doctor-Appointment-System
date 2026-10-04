import os
import sys
import argparse
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import SessionLocal
from database.models import User, Patient
from api.dependencies import hash_password


def create_patient(name: str, email: str, password: str, phone: str = None, age: int = 30, gender: str = "Other"):
    db = SessionLocal()
    try:
        email_clean = email.lower().strip()
        existing = db.query(User).filter_by(email=email_clean).first()
        if existing:
            print(f"Error: User with email '{email_clean}' already exists.")
            return

        pwd_hash, salt = hash_password(password)
        user_id = f"usr-pat-{uuid.uuid4().hex[:8]}"

        user = User(
            id=user_id,
            email=email_clean,
            password_hash=pwd_hash,
            salt=salt,
            role="Patient",
            name=name,
            phone=phone,
            is_active=True
        )
        db.add(user)
        db.commit()

        patient = Patient(
            id=f"profile-{user_id}",
            user_id=user.id,
            medical_record_num=f"MRN-{uuid.uuid4().hex[:6].upper()}",
            age=age,
            gender=gender,
            blood_group="O+",
            emergency_contact=phone
        )
        db.add(patient)
        db.commit()
        print(f"Successfully provisioned Patient {name} ({email_clean})")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Provision Patient Account")
    parser.add_argument("--name", required=True, help="Patient full name")
    parser.add_argument("--email", required=True, help="Patient email")
    parser.add_argument("--password", required=True, help="Patient password")
    parser.add_argument("--phone", default="+91 98401 55555", help="Patient phone")
    parser.add_argument("--age", type=int, default=35, help="Patient age")
    parser.add_argument("--gender", default="Female", help="Patient gender")
    args = parser.parse_args()

    create_patient(args.name, args.email, args.password, args.phone, args.age, args.gender)
