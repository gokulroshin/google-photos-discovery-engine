from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.config import get_settings
from backend.schemas.auth import LoginRequest, TokenResponse, UserResponse
from backend.auth.service import authenticate_user
from backend.auth.jwt import create_access_token
from backend.auth.dependencies import get_current_user
from backend.auth.rate_limiter import login_rate_limiter
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticates researcher or admin and returns a signed JWT access token.
    Rate limited to 10 attempts per IP per 15 minutes.
    """
    # 1. Enforce IP rate limiting
    await login_rate_limiter.check_rate_limit(request, email=credentials.email)

    # 2. Authenticate credentials
    user = await authenticate_user(
        db,
        email=credentials.email,
        password=credentials.password,
        requested_role=credentials.role,
    )
    if not user:
        await login_rate_limiter.log_failed_attempt(request, email=credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Create 8-hour JWT token with claims
    expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name,
        },
        expires_delta=expires_delta,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile and assigned role.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        created_at=current_user.created_at,
    )
