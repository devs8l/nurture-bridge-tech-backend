"""
Migration Script: Add name column to tables
Run this to add the name field to users, doctors, and parents tables
"""
import asyncio
import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

from sqlalchemy import text
from db.base import async_session

async def run_migration():
    print("🔄 Running migration: Adding name column to tables...")
    
    async with async_session() as db:
        try:
            # Add name column to auth.users table
            print("  ➤ Adding name column to auth.users...")
            await db.execute(text("""
                ALTER TABLE auth.users 
                ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT 'NBT_super_admin'
            """))
            
            # Add name column to clinical.doctors table
            print("  ➤ Adding name column to clinical.doctors...")
            await db.execute(text("""
                ALTER TABLE clinical.doctors 
                ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT 'Doctor'
            """))
            
            # Add name column to clinical.parents table
            print("  ➤ Adding name column to clinical.parents...")
            await db.execute(text("""
                ALTER TABLE clinical.parents 
                ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT 'Parent'
            """))
            
            await db.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    try:
        asyncio.run(run_migration())
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
