from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.models.auth import Login
from app.security.tokens import decode_access_token

# Define OAuth2 scheme pointing to our login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> Login:
    """
    Dependency to validate access token and return the currently logged-in user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    # Query the login database record
    query = select(Login).where(Login.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    # Inject impersonation context
    if payload.get("impersonating"):
        setattr(user, "is_impersonated", True)
        setattr(user, "actor_user_id", payload.get("actor_user_id"))
        setattr(user, "actor_role", payload.get("actor_role"))
    else:
        setattr(user, "is_impersonated", False)
        
    await db.commit()
    return user
