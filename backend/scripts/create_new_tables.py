import asyncio
import os
import sys

# Add parent dir to path to allow importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import engine
from app.models.base import Base
from app.models import *

async def create_tables():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
