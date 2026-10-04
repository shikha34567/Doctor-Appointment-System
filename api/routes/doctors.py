from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Physician, Department
from api.schemas.appointments import DoctorResponse, DepartmentResponse

router = APIRouter(tags=["Doctors & Departments"])


@router.get("/doctors", response_model=List[DoctorResponse])
def list_doctors(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    search: Optional[str] = Query(None, description="Search physician name or specialty"),
    db: Session = Depends(get_db)
):
    query = db.query(Physician)
    if specialty and specialty.strip() and specialty.lower() != "all":
        query = query.filter(Physician.specialty.ilike(f"%{specialty.strip()}%"))
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (Physician.name.ilike(term)) | (Physician.specialty.ilike(term)) | (Physician.qualification.ilike(term))
        )
    return query.order_by(Physician.name.asc()).all()


@router.get("/doctors/{doctor_id}", response_model=DoctorResponse)
def get_doctor_by_id(doctor_id: str, db: Session = Depends(get_db)):
    doc = db.query(Physician).filter(Physician.doctor_id == doctor_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physician with ID '{doctor_id}' not found."
        )
    return doc


@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).order_by(Department.name.asc()).all()
