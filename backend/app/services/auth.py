from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.auth import hash_password, verify_password
from app.db.models import User
from app.schemas.auth import UserCreate


async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email.lower())
    )

    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> User:
    user = User(
        email=str(user_data.email).lower(),
        hashed_password=hash_password(user_data.password),
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    user = await get_user_by_email(db, email)

    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user