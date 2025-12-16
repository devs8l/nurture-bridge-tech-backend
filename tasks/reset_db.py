import asyncio
import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

from db.base import engine, Base
from app_logging.logger import get_logger

# Import all models to ensure they are registered
import db.models.auth
import db.models.tenant
import db.models.clinical
import db.models.intake
import db.models.assessment
import db.models.audit

logger = get_logger("reset_db_script")

async def reset_db():
    logger.warning("🗑️  DROPPING ALL TABLES in 5 seconds... Press Ctrl+C to cancel.")
    await asyncio.sleep(5)
    
    async with engine.begin() as conn:
        logger.info("Dropping tables...")
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Database reset successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_db())
