"""
Run this ONCE to create database schemas and tables
"""
import asyncio
from sqlalchemy import text

async def setup():
    from db.base import engine
    from db.models.assessment import AssessmentSection, AssessmentQuestion
    
    async with engine.begin() as conn:
        # Create assessment schema only
        print("Creating assessment schema...")
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS assessment"))
        print("✓ Assessment schema created")
        
        
        print("Creating questions table...")
        await conn.run_sync(AssessmentQuestion.__table__.create)
        print("✓ Questions table created successfully!")
    
    await engine.dispose()

asyncio.run(setup())
