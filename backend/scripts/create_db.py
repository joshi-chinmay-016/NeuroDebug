"""Create PostgreSQL database if not exists."""

import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.scripts.create_db")

async def create_database_if_not_exists():
    db_url = Config.DATABASE_URL
    if not db_url.startswith("postgresql"):
        print("Not a postgresql database, skipping creation.")
        return

    parsed = urlparse(db_url.replace("postgresql+asyncpg://", "http://"))
    db_name = parsed.path.lstrip("/")
    user = parsed.username
    password = parsed.password
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    # Connect to default 'postgres' database
    import asyncpg
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres"
        )
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            print(f"Creating database '{db_name}'...")
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Database '{db_name}' created successfully!")
        else:
            print(f"Database '{db_name}' already exists.")
        await conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == "__main__":
    asyncio.run(create_database_if_not_exists())
