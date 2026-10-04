from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index, Text
)
from sqlalchemy.orm import relationship
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False)  # 'Patient', 'Physician', 'OperationsManager'
    name = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=True)
    doctor_id = Column(String(32), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient_profile = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
    physician_profile = relationship("Physician", back_populates="user", uselist=False)
    appointments = relationship("Appointment", back_populates="user", foreign_keys="Appointment.patient_id")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    medical_record_num = Column(String(64), unique=True, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(16), nullable=True)
    blood_group = Column(String(8), nullable=True)
    emergency_contact = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="patient_profile")
    admissions = relationship("Admission", back_populates="patient")


class Physician(Base):
    __tablename__ = "physicians"

    doctor_id = Column(String(32), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    name = Column(String(128), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    specialty = Column(String(64), nullable=False, index=True)
    qualification = Column(String(255), nullable=True)
    experience = Column(String(32), nullable=True)
    fee = Column(Float, nullable=False, default=500.0)
    availability = Column(String(128), nullable=True)
    room = Column(String(64), nullable=True)
    languages = Column(String(128), nullable=True)
    bio = Column(Text, nullable=True)
    phone = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="physician_profile")
    appointments = relationship("Appointment", back_populates="physician")


class Department(Base):
    __tablename__ = "departments"

    id = Column(String(32), primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    code = Column(String(16), unique=True, nullable=False)
    total_beds = Column(Integer, nullable=False, default=40)
    icu_beds = Column(Integer, nullable=False, default=8)
    emergency_beds = Column(Integer, nullable=False, default=12)
    general_beds = Column(Integer, nullable=False, default=20)
    target_nurse_ratio = Column(Float, default=4.0)  # 1 nurse per N patients
    target_physician_ratio = Column(Float, default=10.0)  # 1 physician per N patients

    beds = relationship("Bed", back_populates="department_rel")
    admissions = relationship("Admission", back_populates="department_rel")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_name = Column(String(128), nullable=False)
    patient_email = Column(String(255), nullable=True)
    patient_phone = Column(String(32), nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(16), nullable=True)
    doctor_id = Column(String(32), ForeignKey("physicians.doctor_id"), nullable=False, index=True)
    doctor_name = Column(String(128), nullable=False)
    specialty = Column(String(64), nullable=False)
    appointment_date = Column(String(32), nullable=False, index=True)  # YYYY-MM-DD
    time_slot = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="Scheduled")  # 'Scheduled', 'Completed', 'Cancelled'
    fee = Column(Float, nullable=False)
    room = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="appointments", foreign_keys=[patient_id])
    physician = relationship("Physician", back_populates="appointments")

    __table_args__ = (
        Index("idx_doctor_slot", "doctor_id", "appointment_date", "time_slot"),
    )


class Bed(Base):
    __tablename__ = "beds"

    bed_id = Column(String(32), primary_key=True)
    department_id = Column(String(32), ForeignKey("departments.id"), nullable=False)
    hospital_unit = Column(String(64), nullable=False)  # 'Emergency', 'ICU', 'General Ward', 'Surgical'
    bed_type = Column(String(32), default="Standard")  # 'Standard', 'ICU-Ventilator', 'Isolation'
    status = Column(String(32), default="Available")  # 'Available', 'Occupied', 'Cleaning', 'Maintenance'
    room_number = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)

    department_rel = relationship("Department", back_populates="beds")
    assignments = relationship("BedAssignment", back_populates="bed")


class Admission(Base):
    __tablename__ = "admissions"

    admission_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    appointment_id = Column(String(64), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(String(32), ForeignKey("departments.id"), nullable=False)
    doctor_id = Column(String(32), ForeignKey("physicians.doctor_id", ondelete="SET NULL"), nullable=True)
    admission_datetime = Column(DateTime, nullable=False, index=True)
    discharge_datetime = Column(DateTime, nullable=True)
    admission_type = Column(String(32), nullable=False)  # 'Emergency', 'Elective', 'Urgent'
    emergency_priority = Column(Integer, nullable=True)  # 1 (Resuscitation) to 5 (Non-urgent)
    waiting_time_minutes = Column(Float, nullable=True)
    length_of_stay_days = Column(Float, nullable=True)
    bed_id = Column(String(32), ForeignKey("beds.bed_id", ondelete="SET NULL"), nullable=True)
    hospital_unit = Column(String(64), nullable=False)
    status = Column(String(32), default="Admitted")  # 'Admitted', 'Discharged', 'Transferred'
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="admissions")
    department_rel = relationship("Department", back_populates="admissions")
    bed_assignments = relationship("BedAssignment", back_populates="admission")


class BedAssignment(Base):
    __tablename__ = "bed_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bed_id = Column(String(32), ForeignKey("beds.bed_id"), nullable=False)
    admission_id = Column(String(64), ForeignKey("admissions.admission_id"), nullable=False)
    assigned_at = Column(DateTime, nullable=False)
    released_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="Active")  # 'Active', 'Released'

    bed = relationship("Bed", back_populates="assignments")
    admission = relationship("Admission", back_populates="bed_assignments")


class StaffingRecord(Base):
    __tablename__ = "staffing_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_date = Column(String(32), nullable=False, index=True)  # YYYY-MM-DD
    shift = Column(String(32), nullable=False)  # 'Morning', 'Afternoon', 'Night'
    department_id = Column(String(32), ForeignKey("departments.id"), nullable=False)
    staff_type = Column(String(32), nullable=False)  # 'Nurse', 'Physician', 'Support'
    staff_on_duty = Column(Integer, nullable=False)
    required_staff = Column(Integer, nullable=False)
    variance = Column(Integer, nullable=False)
    is_synthetic = Column(Boolean, default=True)


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_date = Column(String(32), nullable=False)  # YYYY-MM-DD
    target_date = Column(String(32), nullable=False)
    horizon_days = Column(Integer, nullable=False)
    predicted_admissions = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    model_name = Column(String(64), nullable=False)
    department_id = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelEvaluationRecord(Base):
    __tablename__ = "model_evaluation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_type = Column(String(64), nullable=False)  # 'Forecasting', 'WaitingTime'
    model_name = Column(String(64), nullable=False)
    target_variable = Column(String(64), nullable=False)
    metric_name = Column(String(32), nullable=False)  # 'MAE', 'RMSE', 'MAPE', 'R2'
    metric_value = Column(Float, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)


class OperationalConfig(Base):
    __tablename__ = "operational_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(64), unique=True, nullable=False)
    config_value = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
