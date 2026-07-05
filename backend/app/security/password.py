from passlib.context import CryptContext
from app.core.config import settings

# Initialize Passlib's CryptContext with bcrypt rounds configured
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS
)

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its bcrypt hash.
    """
    return pwd_context.verify(plain_password, hashed_password)
