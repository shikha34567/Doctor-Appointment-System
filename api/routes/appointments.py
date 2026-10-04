import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User, Physician, Appointment
from api.schemas.appointments import (
    AppointmentCreate, AppointmentResponse, AppointmentStatusUpdate
)
from api.dependencies import (
    get_current_user, require_patient, require_physician
)

router = APIRouter(tags=["Appointments"])


@router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: AppointmentCreate,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    # Verify doctor exists
    physician = db.query(Physician).filter(Physician.doctor_id == payload.doctor_id).first()
    if not physician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor ID '{payload.doctor_id}' does not exist in registry."
        )

    # Prevent double booking the same doctor on the same date and time slot
    existing_booking = db.query(Appointment).filter(
        Appointment.doctor_id == payload.doctor_id,
        Appointment.appointment_date == payload.appointment_date,
        Appointment.time_slot == payload.time_slot,
        Appointment.status != "Cancelled"
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Time slot '{payload.time_slot}' on {payload.appointment_date} is already booked for Dr. {physician.name}."
        )

    appointment_id = f"HC-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}"

    appointment = Appointment(
        id=appointment_id,
        patient_id=current_user.id,
        patient_name=payload.patient_name or current_user.name,
        patient_email=payload.patient_email or current_user.email,
        patient_phone=payload.patient_phone or current_user.phone,
        patient_age=payload.patient_age,
        patient_gender=payload.patient_gender,
        doctor_id=physician.doctor_id,
        doctor_name=physician.name,
        specialty=physician.specialty,
        appointment_date=payload.appointment_date,
        time_slot=payload.time_slot,
        status="Scheduled",
        fee=physician.fee,
        room=physician.room,
        notes=payload.notes
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/patient/appointments", response_model=List[AppointmentResponse])
def get_patient_appointments(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    # Strict data isolation: patients only receive their own records
    appointments = db.query(Appointment).filter(
        Appointment.patient_id == current_user.id
    ).order_by(Appointment.appointment_date.desc(), Appointment.time_slot.desc()).all()
    return appointments


@router.get("/physician/appointments", response_model=List[AppointmentResponse])
def get_physician_appointments(
    appointment_date: Optional[str] = Query(None, description="Filter by YYYY-MM-DD"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(require_physician),
    db: Session = Depends(get_db)
):
    # Strict physician isolation: mapped directly to unique doctor_id
    if not current_user.doctor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Physician account is not mapped to a valid doctor registry ID."
        )

    query = db.query(Appointment).filter(Appointment.doctor_id == current_user.doctor_id)
    if appointment_date and appointment_date.strip():
        query = query.filter(Appointment.appointment_date == appointment_date.strip())
    if status_filter and status_filter.strip() and status_filter.lower() != "all":
        query = query.filter(Appointment.status == status_filter.strip())

    return query.order_by(Appointment.appointment_date.asc(), Appointment.time_slot.asc()).all()


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment_details(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    # Authorization guard: owner patient, assigned physician, or operations manager
    if current_user.role == "Patient" and appointment.patient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this appointment record.")
    if current_user.role == "Physician" and appointment.doctor_id != current_user.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: appointment not assigned to you.")

    return appointment


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: str,
    payload: AppointmentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    if current_user.role == "Physician":
        if appointment.doctor_id != current_user.doctor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot alter another physician's appointment.")
    elif current_user.role == "Patient":
        if appointment.patient_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot alter another patient's appointment.")
        if payload.status != "Cancelled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patients can only cancel their appointments.")
    elif current_user.role != "OperationsManager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

    appointment.status = payload.status
    if payload.notes:
        appointment.notes = f"{appointment.notes or ''} [Update: {payload.notes}]".strip()

    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    if current_user.role == "Patient" and appointment.patient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel another patient's appointment.")
    if current_user.role == "Physician" and appointment.doctor_id != current_user.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel another doctor's appointment.")

    if appointment.status == "Completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel an already completed appointment.")

    appointment.status = "Cancelled"
    db.commit()
    db.refresh(appointment)
    return appointment
