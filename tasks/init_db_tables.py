import asyncio
import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

from db.base import init_db, engine
from app_logging.logger import get_logger

# Import all models to ensure they are registered with Base.metadata
import db.models.auth
import db.models.tenant
import db.models.clinical
import db.models.intake
import db.models.assessment
import db.models.audit

logger = get_logger("init_db_script")

async def main():
    logger.info("Initializing database tables...")
    try:
        await init_db()
        logger.info("Tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        # Check for common errors
        if "password authentication failed" in str(e):
             logger.error("Check your database username and password in .env")
        elif "does not exist" in str(e):
             logger.error("Check if the database name exists in Postgres")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
