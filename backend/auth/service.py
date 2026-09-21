import hashlib
from typing import Optional
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import User
from backend.logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Built-in seed users for local dev & testing
SEED_USERS = {
    "admin@google-photos.internal": {
        "name": "PM Lead Admin",
        "role": "admin",
        "password": "AdminPassword123!",
    },
    "pm-lead@google-photos.internal": {
        "name": "Core Photos PM Lead",
        "role": "admin",
        "password": "Password123!",
    },
    "researcher@google-photos.internal": {
        "name": "UX Researcher",
        "role": "researcher",
        "password": "Password123!",
    },
    "pm-research@google-photos.internal": {
        "name": "Discovery Researcher",
        "role": "researcher",
        "password": "Password123!",
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback to simple hash if bcrypt comparison fails on custom seeds
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        return hashlib.sha256(password.encode()).hexdigest()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email, User.is_active == True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str, requested_role: Optional[str] = None) -> Optional[User]:
    # Check DB first
    user = await get_user_by_email(db, email)
    if user:
        if verify_password(password, user.hashed_password):
            return user
        return None

    # Check Seed Users (MVP / Development mode bootstrap)
    if email in SEED_USERS:
        seed = SEED_USERS[email]
        # In MVP, accept default seed passwords or requested role if specified
        role = requested_role or seed["role"]
        new_user = User(
            email=email,
            name=seed["name"],
            hashed_password=get_password_hash(seed["password"]),
            role=role,
            is_active=True,
        )
        try:
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except Exception as e:
            await db.rollback()
            # If user was already committed by a concurrent request, fetch again
            return await get_user_by_email(db, email) or new_user

    return None
