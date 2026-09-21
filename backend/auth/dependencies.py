from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.auth.jwt import decode_token
from backend.auth.service import get_user_by_email
from backend.models.user import User

# Optional auth support for both Bearer and OAuth2 header styles
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials or not credentials.credentials:
        raise credentials_exception

    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role", "researcher")
        name: str = payload.get("name", "Researcher")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # Attempt to fetch persistent user or reconstruct from token claims
    user = await get_user_by_email(db, email)
    if not user:
        # Construct active user instance from JWT payload
        user = User(
            id=user_id or "usr_jwt",
            email=email,
            name=name,
            role=role,
            is_active=True,
            hashed_password="",
        )
    return user


def require_role(allowed_roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker


require_admin = require_role(["admin"])
require_researcher = require_role(["admin", "researcher"])
