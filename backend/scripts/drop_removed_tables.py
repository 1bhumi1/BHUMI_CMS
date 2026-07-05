import asyncio
import os
import sys

# Add parent dir to path to allow importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database.session import engine

async def drop_tables():
    print("Dropping removed tables...")
    async with engine.begin() as conn:
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        await conn.execute(text("DROP TABLE IF EXISTS course;"))
        await conn.execute(text("DROP TABLE IF EXISTS section;"))
        await conn.execute(text("DROP TABLE IF EXISTS semester;"))
        await conn.execute(text("DROP TABLE IF EXISTS batch;"))
        await conn.execute(text("DROP TABLE IF EXISTS subject;"))
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    print("Tables dropped successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(drop_tables())
