from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_logger import record_event
from app.core.security import get_current_user
from app.db.database import get_db
from app.schemas.user_schema import (
    ForgotPasswordRequest,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.services.auth_service import (
    authenticate_user,
    create_password_reset,
    get_user_by_email,
    issue_tokens,
    refresh_tokens,
    register_user,
    revoke_refresh_token,
    reset_password,
)


router = APIRouter()


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate, db: AsyncSession = Depends(get_db)
) -> TokenPair:
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")
    user = await register_user(db, payload)
    tokens = await issue_tokens(db, user)
    await record_event(db, "user_register", "user", str(user.id))
    return TokenPair(**tokens)


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenPair:
    user = await authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    tokens = await issue_tokens(db, user)
    await record_event(db, "user_login", "user", str(user.id))
    return TokenPair(**tokens)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    tokens = await refresh_tokens(db, payload.refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    return TokenPair(**tokens)


@router.post("/logout")
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    revoked = await revoke_refresh_token(db, payload.refresh_token)
    if not revoked:
        raise HTTPException(status_code=400, detail="Invalid refresh token.")
    return {"status": "ok"}


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    user = await get_user_by_email(db, payload.email)
    if not user:
        return {"status": "ok"}
    token = await create_password_reset(db, user)
    await record_event(db, "password_reset_requested", "user", str(user.id))
    return {"status": "ok", "reset_token": token}


@router.post("/reset-password")
async def reset_password_endpoint(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    success = await reset_password(db, payload.token, payload.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)) -> UserOut:
    return user
