from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import AsyncSessionLocal
from app.models.user import User


async def main() -> None:
    email = os.getenv("ADMIN_EMAIL", "admin@dentosmart.app")
    password = os.getenv("ADMIN_PASSWORD", "Admin123!")
    name = os.getenv("ADMIN_NAME", "Primary Admin")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"admin_exists: {email}")
            return
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role="admin",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f"admin_created: {email}")


if __name__ == "__main__":
    asyncio.run(main())
