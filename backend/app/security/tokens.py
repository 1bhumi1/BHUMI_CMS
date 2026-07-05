import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import JWTError, jwt
from app.core.config import settings

def create_token(
    subject: str,
    expires_delta: timedelta,
    secret_key: str,
    token_type: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a signed JWT token.
    """
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    payload = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "type": token_type
    }
    
    if additional_claims:
        payload.update(additional_claims)
        
    return jwt.encode(payload, secret_key, algorithm=settings.ALGORITHM)

def create_access_token(user_id: int, computer_code: int, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a short-lived access token.
    """
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {"computer_code": computer_code}
    if additional_claims:
        claims.update(additional_claims)
    return create_token(
        subject=str(user_id),
        expires_delta=expires,
        secret_key=settings.JWT_SECRET,
        token_type="access",
        additional_claims=claims
    )

def create_refresh_token(user_id: int, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a long-lived refresh token.
    """
    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(
        subject=str(user_id),
        expires_delta=expires,
        secret_key=settings.JWT_REFRESH_SECRET,
        token_type="refresh",
        additional_claims=additional_claims
    )

def decode_token(token: str, secret_key: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token. Returns payload or raises JWTError.
    """
    payload = jwt.decode(token, secret_key, algorithms=[settings.ALGORITHM])
    
    # Check if expired (jose library does this automatically, but double check)
    exp = payload.get("exp")
    if exp is None:
        raise JWTError("Token payload missing exp claim.")
    
    now = datetime.now(timezone.utc).timestamp()
    if now > exp:
        raise JWTError("Token has expired.")
        
    return payload

def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate an access token.
    """
    payload = decode_token(token, settings.JWT_SECRET)
    if payload.get("type") != "access":
        raise JWTError("Invalid token type.")
    return payload

def decode_refresh_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a refresh token.
    """
    payload = decode_token(token, settings.JWT_REFRESH_SECRET)
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type.")
    return payload
