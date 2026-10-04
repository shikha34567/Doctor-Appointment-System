import os
import sys
import argparse
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import SessionLocal
from database.models import User, Physician
from api.dependencies import hash_password


def create_physician(
    doctor_id: str,
    name: str,
    email: str,
    specialty: str,
    password: str,
    fee: float = 700.0,
    room: str = "Consultation Room",
    phone: str = "+91 98400 00000"
):
    db = SessionLocal()
    try:
        email_clean = email.lower().strip()
        existing = db.query(User).filter_by(email=email_clean).first()
        if existing:
            print(f"Error: User with email '{email_clean}' already exists.")
            return

        pwd_hash, salt = hash_password(password)
        user_id = f"usr-{doctor_id}"

        user = User(
            id=user_id,
            email=email_clean,
            password_hash=pwd_hash,
            salt=salt,
            role="Physician",
            name=name,
            phone=phone,
            doctor_id=doctor_id,
            is_active=True
        )
        db.add(user)
        db.commit()

        physician = Physician(
            doctor_id=doctor_id,
            user_id=user.id,
            name=name,
            email=email_clean,
            specialty=specialty,
            qualification="MBBS, MD",
            experience="10+ Years",
            fee=fee,
            room=room,
            phone=phone
        )
        db.add(physician)
        db.commit()
        print(f"Successfully provisioned Physician {name} ({doctor_id}) - {specialty}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Provision Physician Account")
    parser.add_argument("--doctor-id", required=True, help="Doctor registry ID e.g. doc-056")
    parser.add_argument("--name", required=True, help="Doctor full name")
    parser.add_argument("--email", required=True, help="Doctor email")
    parser.add_argument("--specialty", required=True, help="Clinical specialty")
    parser.add_argument("--password", required=True, help="Doctor account password")
    parser.add_argument("--fee", type=float, default=700.0, help="Consultation fee")
    parser.add_argument("--room", default="Consultation Wing - Room 204", help="Consultation room")
    parser.add_argument("--phone", default="+91 98400 00000", help="Phone")
    args = parser.parse_args()

    create_physician(args.doctor_id, args.name, args.email, args.specialty, args.password, args.fee, args.room, args.phone)
