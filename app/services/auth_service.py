from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.password_reset import PasswordReset
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user_schema import UserCreate


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, payload: UserCreate) -> User:
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def issue_tokens(db: AsyncSession, user: User) -> dict[str, str]:
    settings = get_settings()
    access_token = create_access_token(str(user.id), settings.access_token_minutes)
    refresh_token = create_refresh_token(str(user.id), settings.refresh_token_days)
    refresh_hash = _hash_token(refresh_token)
    expires_at = datetime.now(tz=timezone.utc) + timedelta(days=settings.refresh_token_days)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
        )
    )
    await db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token}


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict[str, str] | None:
    token_hash = _hash_token(refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    record = result.scalar_one_or_none()
    if not record or record.revoked_at:
        return None
    if record.expires_at < datetime.now(tz=timezone.utc):
        return None
    user_result = await db.execute(select(User).where(User.id == record.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return None
    if not user.is_active:
        return None
    record.revoked_at = datetime.now(tz=timezone.utc)
    await db.commit()
    return await issue_tokens(db, user)


async def revoke_refresh_token(db: AsyncSession, refresh_token: str) -> bool:
    token_hash = _hash_token(refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    record = result.scalar_one_or_none()
    if not record or record.revoked_at:
        return False
    record.revoked_at = datetime.now(tz=timezone.utc)
    await db.commit()
    return True


async def create_password_reset(db: AsyncSession, user: User) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    db.add(
        PasswordReset(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    await db.commit()
    return token


async def reset_password(db: AsyncSession, token: str, new_password: str) -> bool:
    token_hash = _hash_token(token)
    result = await db.execute(select(PasswordReset).where(PasswordReset.token_hash == token_hash))
    record = result.scalar_one_or_none()
    if not record or record.used_at:
        return False
    if record.expires_at < datetime.now(tz=timezone.utc):
        return False
    user_result = await db.execute(select(User).where(User.id == record.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return False
    user.password_hash = hash_password(new_password)
    record.used_at = datetime.now(tz=timezone.utc)
    await db.commit()
    return True
