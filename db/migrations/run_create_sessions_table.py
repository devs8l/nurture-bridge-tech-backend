"""
Migration Script: Create auth.sessions table
Run this to apply the session management migration
"""
import asyncio
import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

from sqlalchemy import text
from db.base import async_session

async def run_migration():
    print("🔄 Running migration: Create auth.sessions table...")
    
    async with async_session() as db:
        try:
            # Step 1: Create sessions table
            print("  ➤ Creating auth.sessions table...")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS auth.sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
                    refresh_token_hash TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    user_agent TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMP NOT NULL,
                    revoked_at TIMESTAMP NULL,
                    revoked_reason TEXT NULL,
                    deleted_at TIMESTAMP NULL,
                    CONSTRAINT uq_user_device UNIQUE (user_id, device_id)
                )
            """))
            
            # Step 2: Create indexes
            print("  ➤ Creating indexes...")
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON auth.sessions(user_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_refresh_token ON auth.sessions(refresh_token_hash)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_active ON auth.sessions(user_id, revoked_at)"))
            
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
