import os
import sys
import argparse
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import SessionLocal
from database.models import User
from api.dependencies import hash_password


def create_operations_manager(email: str, password: str, name: str, phone: str = None):
    db = SessionLocal()
    try:
        email_clean = email.lower().strip()
        existing = db.query(User).filter_by(email=email_clean).first()
        if existing:
            print(f"Error: User with email '{email_clean}' already exists.")
            return

        pwd_hash, salt = hash_password(password)
        user_id = f"usr-ops-{uuid.uuid4().hex[:8]}"

        admin = User(
            id=user_id,
            email=email_clean,
            password_hash=pwd_hash,
            salt=salt,
            role="OperationsManager",
            name=name,
            phone=phone,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print(f"Successfully provisioned Operations Manager account: {email_clean} (ID: {user_id})")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Provision Hospital Operations Manager Account")
    parser.add_argument("--email", required=True, help="Manager email address")
    parser.add_argument("--password", required=True, help="Secure password")
    parser.add_argument("--name", required=True, help="Full manager name")
    parser.add_argument("--phone", default="+91 98400 11223", help="Contact phone")
    args = parser.parse_args()

    create_operations_manager(args.email, args.password, args.name, args.phone)
