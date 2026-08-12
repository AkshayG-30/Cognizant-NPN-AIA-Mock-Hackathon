"""
CarePath AI — Authentication Routes
Secure, database-backed authentication with bcrypt password verification,
standardized email/Gmail validation, role-based JWT tokens, and persistent user registration.
"""
from __future__ import annotations

import re
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, decode_token, get_password_hash, verify_password
from app.db.database import get_db
from app.db.models import Patient, User

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Default demo credentials for pre-seeded accounts
DEMO_CREDENTIALS = {
    "patient@carepath.ai": {
        "name": "Jane Doe",
        "role": "patient",
        "password": "Patient@2026",
    },
    "sarah.williams@carepath.ai": {
        "name": "Dr. Sarah Williams",
        "role": "doctor",
        "password": "Doctor@2026",
    },
    "admin@carepath.ai": {
        "name": "System Admin",
        "role": "admin",
        "password": "Admin@2026",
    },
}


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email (Gmail or valid email address)")
    password: str = Field(..., description="User password")


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Full Name")
    email: str = Field(..., description="User email (e.g. user@gmail.com)")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 chars)")
    role: Optional[str] = Field("patient", description="User role: patient, doctor, admin")


class RegisterResponse(BaseModel):
    success: bool = True
    message: str
    email: str
    name: str
    role: str


class AuthResponse(BaseModel):
    token: str
    user: dict[str, Any]


async def ensure_demo_users(db: AsyncSession):
    """Ensure default demo accounts are seeded with valid bcrypt hashes in the database."""
    for demo_email, info in DEMO_CREDENTIALS.items():
        res = await db.execute(select(User).where(User.email == demo_email))
        existing = res.scalar_one_or_none()
        if not existing:
            new_user = User(
                email=demo_email,
                name=info["name"],
                role=info["role"],
                hashed_password=get_password_hash(info["password"]),
                is_active=True,
            )
            db.add(new_user)
            if info["role"] == "patient":
                parts = info["name"].split(" ", 1)
                first = parts[0]
                last = parts[1] if len(parts) > 1 else ""
                pat_res = await db.execute(select(Patient).where(Patient.external_id == "PAT-DEMO-01"))
                if not pat_res.scalar_one_or_none():
                    db.add(
                        Patient(
                            external_id="PAT-DEMO-01",
                            first_name=first,
                            last_name=last,
                            city="Boston",
                            state="MA",
                            zip_code="02115",
                            insurance="Medicare Part B",
                            data_source="DEMO",
                        )
                    )
            await db.commit()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.
    Validates email format, verifies password strength, hashes password,
    persists the user in PostgreSQL, and prompts the user to log in.
    """
    name_clean = req.name.strip()
    email_clean = req.email.strip().lower()
    role_clean = (req.role or "patient").strip().lower()

    if not name_clean:
        raise HTTPException(status_code=400, detail="Full name cannot be empty.")

    if not EMAIL_REGEX.match(email_clean):
        raise HTTPException(
            status_code=400,
            detail="Invalid email address format. Please enter a valid email (e.g. user@gmail.com).",
        )

    if len(req.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters in length.",
        )

    if role_clean not in ["patient", "doctor", "admin", "care_coordinator"]:
        role_clean = "patient"

    # Check if user already exists
    res = await db.execute(select(User).where(User.email == email_clean))
    existing_user = res.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists. Please sign in with your password.",
        )

    # Hash password with bcrypt
    hashed_pw = get_password_hash(req.password)

    # Create new database user
    user = User(
        name=name_clean,
        email=email_clean,
        hashed_password=hashed_pw,
        role=role_clean,
        is_active=True,
    )
    db.add(user)

    # If patient, create a corresponding patient record
    if role_clean == "patient":
        name_parts = name_clean.split(" ", 1)
        first_n = name_parts[0]
        last_n = name_parts[1] if len(name_parts) > 1 else ""
        ext_id = f"PAT-{uuid.uuid4().hex[:8].upper()}"
        patient_record = Patient(
            external_id=ext_id,
            first_name=first_n,
            last_name=last_n,
            data_source="USER_REGISTRATION",
        )
        db.add(patient_record)

    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        success=True,
        message="Account created successfully! Please sign in with your credentials.",
        email=user.email,
        name=user.name,
        role=user.role,
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user credentials (email & password).
    Verifies the email and bcrypt password against the database.
    Returns a signed JWT access token and user metadata upon verification.
    """
    email_clean = req.email.strip().lower()
    password = req.password

    if not email_clean or not password:
        raise HTTPException(
            status_code=400,
            detail="Both email and password are required.",
        )

    if not EMAIL_REGEX.match(email_clean):
        raise HTTPException(
            status_code=400,
            detail="Invalid email format. Please provide a valid email address.",
        )

    # Ensure demo accounts exist if logging in with demo email
    if email_clean in DEMO_CREDENTIALS:
        await ensure_demo_users(db)

    # Query user from PostgreSQL
    res = await db.execute(select(User).where(User.email == email_clean))
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials or create an account.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact support.",
        )

    # Verify password against bcrypt hash
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials.",
        )

    # Create JWT access token
    token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        email=user.email,
        name=user.name,
    )

    user_data = {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }

    return AuthResponse(token=token, user=user_data)


@router.get("/me")
async def get_me(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve current authenticated user profile from JWT token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
        )

    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        user_id = payload.sub
        
        # Verify user still exists in database
        try:
            user_uuid = uuid.UUID(user_id)
            res = await db.execute(select(User).where(User.id == user_uuid))
            user = res.scalar_one_or_none()
            if user and user.is_active:
                return {
                    "id": str(user.id),
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                }
        except ValueError:
            pass

        # Fallback to payload claims if valid token
        return {
            "id": payload.sub,
            "name": payload.name or payload.email or "User",
            "email": payload.email,
            "role": payload.role,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Session expired or invalid: {e}",
        )
