"""
CarePath AI — Security Foundations
JWT-based authentication with role-based access control.
Architecture supports future Microsoft Entra ID integration.
"""
from __future__ import annotations

import enum
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings

import bcrypt

security_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate a bcrypt password hash."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


class UserRole(str, enum.Enum):
    """Supported user roles per the research plan."""
    PATIENT = "patient"
    CARE_COORDINATOR = "care_coordinator"
    CLINICIAN = "clinician"
    DOCTOR = "doctor"
    ADMIN = "admin"


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # user ID
    role: str
    email: Optional[str] = None
    name: Optional[str] = None
    exp: datetime
    iat: datetime


class CurrentUser(BaseModel):
    """Represents the authenticated user context."""
    user_id: str
    role: str
    email: Optional[str] = None
    name: Optional[str] = None


def create_access_token(
    user_id: str,
    role: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expiry = now + (expires_delta if expires_delta else timedelta(days=7))
    payload = {
        "sub": str(user_id),
        "role": str(role),
        "email": email or "",
        "name": name or "",
        "iat": now,
        "exp": expiry,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(
            sub=str(payload["sub"]),
            role=str(payload.get("role", "patient")),
            email=payload.get("email"),
            name=payload.get("name"),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload.get("iat", datetime.now(timezone.utc).timestamp()), tz=timezone.utc),
        )
    except (JWTError, KeyError, ValueError) as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> Optional[CurrentUser]:
    """Get current user if token is provided (optional auth)."""
    if credentials is None:
        return None
    token_data = decode_token(credentials.credentials)
    return CurrentUser(
        user_id=token_data.sub,
        role=token_data.role,
        email=token_data.email,
        name=token_data.name,
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> CurrentUser:
    """
    Get current user — required auth.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication credentials required.")

    token_data = decode_token(credentials.credentials)
    return CurrentUser(
        user_id=token_data.sub,
        role=token_data.role,
        email=token_data.email,
        name=token_data.name,
    )


def require_role(*allowed_roles: UserRole):
    """Dependency that enforces role-based access control."""
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{current_user.role.value}' is not authorized for this action.",
            )
        return current_user
    return role_checker
