import pytest
import uuid
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_api_root_health():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Online"
    assert "version" in data


def test_list_doctors_and_departments():
    # Public doctor directory test
    res = client.get("/api/v1/doctors")
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 55  # 55 verified physicians

    # Filter by specialty
    res_cardio = client.get("/api/v1/doctors?specialty=Cardiology")
    assert res_cardio.status_code == 200
    cardio_docs = res_cardio.json()
    assert len(cardio_docs) >= 5
    assert all("Cardiology" in d["specialty"] for d in cardio_docs)

    # Departments test
    res_dept = client.get("/api/v1/departments")
    assert res_dept.status_code == 200
    depts = res_dept.json()
    assert len(depts) == 11


def test_patient_registration_and_login():
    rand_email = f"patient_{uuid.uuid4().hex[:6]}@demo.test"
    reg_payload = {
        "name": "Test User",
        "email": rand_email,
        "password": "Password#1234!",
        "phone": "+91 98400 99999",
        "age": 30,
        "gender": "Female",
        "blood_group": "A+"
    }
    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["role"] == "Patient"

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": rand_email,
        "password": "Password#1234!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token is not None

    # 3. Test me endpoint
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == rand_email


def test_physician_login_and_data_isolation():
    # Login as Dr. John Smith (doc-001)
    doc_email = "dr.johnsmith@healthcare.demo"
    doc_pw = "Doctor#doc-0012026!"
    res = client.post("/api/v1/auth/login", json={"email": doc_email, "password": doc_pw})
    assert res.status_code == 200
    doc_token = res.json()["access_token"]
    assert res.json()["user"]["doctor_id"] == "doc-001"

    # Fetch physician appointments
    appts_res = client.get("/api/v1/physician/appointments", headers={"Authorization": f"Bearer {doc_token}"})
    assert appts_res.status_code == 200
    appts = appts_res.json()
    # All appointments returned must belong to doc-001
    for a in appts:
        assert a["doctor_id"] == "doc-001"


def test_appointment_booking_and_double_booking_prevention():
    # 1. Login as Ananya Raman (Patient)
    pat_res = client.post("/api/v1/auth/login", json={
        "email": "ananya.raman@healthcare.demo",
        "password": "Patient#Secure2026!"
    })
    assert pat_res.status_code == 200
    pat_token = pat_res.json()["access_token"]

    booking_date = "2027-11-20"
    slot = "10:30 AM"

    payload = {
        "doctor_id": "doc-002",
        "appointment_date": booking_date,
        "time_slot": slot,
        "patient_name": "Ananya Raman",
        "patient_phone": "+91 98401 99999",
        "notes": "Echocardiogram follow-up"
    }

    # First booking: should succeed
    b1_res = client.post("/api/v1/appointments", json=payload, headers={"Authorization": f"Bearer {pat_token}"})
    assert b1_res.status_code == 201
    appt_id = b1_res.json()["id"]

    # Second booking same doctor, date, and slot: MUST fail with 409 Conflict
    b2_res = client.post("/api/v1/appointments", json=payload, headers={"Authorization": f"Bearer {pat_token}"})
    assert b2_res.status_code == 409

    # Cancel appointment
    c_res = client.post(f"/api/v1/appointments/{appt_id}/cancel", headers={"Authorization": f"Bearer {pat_token}"})
    assert c_res.status_code == 200
    assert c_res.json()["status"] == "Cancelled"


def test_operations_manager_role_protection():
    # 1. Patient should be forbidden from accessing operations overview
    pat_res = client.post("/api/v1/auth/login", json={
        "email": "ananya.raman@healthcare.demo",
        "password": "Patient#Secure2026!"
    })
    pat_token = pat_res.json()["access_token"]

    forbidden_res = client.get("/api/v1/operations/overview", headers={"Authorization": f"Bearer {pat_token}"})
    assert forbidden_res.status_code == 403

    # 2. Operations Manager should succeed
    admin_res = client.post("/api/v1/auth/login", json={
        "email": "admin.operations@healthcare.demo",
        "password": "Admin#Operations2026!"
    })
    assert admin_res.status_code == 200
    admin_token = admin_res.json()["access_token"]

    ops_res = client.get("/api/v1/operations/overview", headers={"Authorization": f"Bearer {admin_token}"})
    assert ops_res.status_code == 200
    data = ops_res.json()
    assert "total_bed_capacity" in data
    assert "occupied_beds" in data
