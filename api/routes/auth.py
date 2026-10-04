import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User, Patient
from api.schemas.auth import UserLogin, UserRegister, UserResponse, TokenResponse
from api.dependencies import (
    hash_password, verify_password, create_access_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_patient(payload: UserRegister, db: Session = Depends(get_db)):
    email_clean = payload.email.lower().strip()
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    user_id = f"usr-pat-{uuid.uuid4().hex[:8]}"
    pwd_hash, salt = hash_password(payload.password)

    user = User(
        id=user_id,
        email=email_clean,
        password_hash=pwd_hash,
        salt=salt,
        role="Patient",
        name=payload.name.strip(),
        phone=payload.phone,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    patient_profile = Patient(
        id=f"profile-{user_id}",
        user_id=user.id,
        medical_record_num=f"MRN-{uuid.uuid4().hex[:6].upper()}",
        age=payload.age,
        gender=payload.gender,
        blood_group=payload.blood_group,
        emergency_contact=payload.phone
    )
    db.add(patient_profile)
    db.commit()

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user) if hasattr(UserResponse, 'from_orm') else UserResponse.model_validate(user)
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email_clean = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(payload.password, user.password_hash, user.salt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "doctor_id": user.doctor_id
    })

    user_data = UserResponse.model_validate(user) if hasattr(UserResponse, "model_validate") else UserResponse.from_orm(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user) if hasattr(UserResponse, "model_validate") else UserResponse.from_orm(current_user)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out. Please clear your client token."}
