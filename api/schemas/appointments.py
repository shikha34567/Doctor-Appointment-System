from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class AppointmentCreate(BaseModel):
    doctor_id: str
    appointment_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    time_slot: str
    patient_name: str
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    notes: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(Scheduled|Completed|Cancelled)$")
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    patient_name: str
    patient_email: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    doctor_id: str
    doctor_name: str
    specialty: str
    appointment_date: str
    time_slot: str
    status: str
    fee: float
    room: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doctor_id: str
    name: str
    email: str
    specialty: str
    qualification: Optional[str] = None
    experience: Optional[str] = None
    fee: float
    availability: Optional[str] = None
    room: Optional[str] = None
    languages: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    total_beds: int
    icu_beds: int
    emergency_beds: int
    general_beds: int
    target_nurse_ratio: float
    target_physician_ratio: float
