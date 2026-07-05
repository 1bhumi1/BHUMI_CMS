from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import BigInteger, Integer

# Dialect-specific ID type to support Auto-Increment on SQLite tests while preserving BIGINT on production MySQL
BigIntID = BigInteger().with_variant(Integer, "sqlite")

class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 declarative base class.
    All database models should inherit from this class.
    """
    pass
