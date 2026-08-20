from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.security.auth import create_access_token
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    create_user,
    get_user_by_email,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    existing_user = await get_user_by_email(
        db,
        str(user_data.email),
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await create_user(
        db,
        user_data,
    )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(
        db,
        str(user_data.email),
        user_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
    )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(
        str(user.id),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user