"""
Migration Script: Add HOD, Receptionist roles and department field
Run this to apply the role and department refactor migration
"""
import asyncio
import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

from sqlalchemy import text
from db.base import async_session

async def run_migration():
    print("🔄 Running migration: Add HOD, Receptionist roles and department field...")
    
    async with async_session() as db:
        try:
            # Step 1: Add new roles to UserRole enum
            print("  ➤ Adding HOD role to enum...")
            await db.execute(text("ALTER TYPE auth.user_role ADD VALUE IF NOT EXISTS 'HOD'"))
            
            print("  ➤ Adding RECEPTIONIST role to enum...")
            await db.execute(text("ALTER TYPE auth.user_role ADD VALUE IF NOT EXISTS 'RECEPTIONIST'"))
            
            # Step 2: Create HOD table
            print("  ➤ Creating clinical.hods table...")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS clinical.hods (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id),
                    tenant_id UUID NOT NULL REFERENCES tenant.tenants(id),
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    department VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    deleted_at TIMESTAMP
                )
            """))
            
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_hods_user_id ON clinical.hods(user_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_hods_tenant_id ON clinical.hods(tenant_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_hods_department ON clinical.hods(department)"))
            
            # Step 3: Create Receptionist table
            print("  ➤ Creating clinical.receptionists table...")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS clinical.receptionists (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id),
                    tenant_id UUID NOT NULL REFERENCES tenant.tenants(id),
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    department VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    deleted_at TIMESTAMP
                )
            """))
            
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_receptionists_user_id ON clinical.receptionists(user_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_receptionists_tenant_id ON clinical.receptionists(tenant_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_receptionists_department ON clinical.receptionists(department)"))
            
            # Step 4: Add first_name and last_name to doctors table
            print("  ➤ Adding first_name and last_name to clinical.doctors...")
            await db.execute(text("ALTER TABLE clinical.doctors ADD COLUMN IF NOT EXISTS first_name VARCHAR(100)"))
            await db.execute(text("ALTER TABLE clinical.doctors ADD COLUMN IF NOT EXISTS last_name VARCHAR(100)"))
            
            # Step 5: Migrate existing name data
            print("  ➤ Migrating existing name data...")
            await db.execute(text("""
                UPDATE clinical.doctors
                SET 
                    first_name = SPLIT_PART(name, ' ', 1),
                    last_name = CASE 
                        WHEN POSITION(' ' IN name) > 0 THEN SUBSTRING(name FROM POSITION(' ' IN name) + 1)
                        ELSE ''
                    END
                WHERE first_name IS NULL
            """))
            
            # Step 6: Make first_name and last_name NOT NULL
            print("  ➤ Making first_name and last_name NOT NULL...")
            await db.execute(text("ALTER TABLE clinical.doctors ALTER COLUMN first_name SET NOT NULL"))
            await db.execute(text("ALTER TABLE clinical.doctors ALTER COLUMN last_name SET NOT NULL"))
            
            # Step 7: Rename specialization to department
            print("  ➤ Renaming specialization to department...")
            await db.execute(text("ALTER TABLE clinical.doctors RENAME COLUMN specialization TO department"))
            
            # Step 8: Make department NOT NULL
            print("  ➤ Setting default department and making it NOT NULL...")
            await db.execute(text("UPDATE clinical.doctors SET department = 'General' WHERE department IS NULL"))
            await db.execute(text("ALTER TABLE clinical.doctors ALTER COLUMN department SET NOT NULL"))
            
            # Step 9: Make license_number nullable
            print("  ➤ Making license_number nullable...")
            await db.execute(text("ALTER TABLE clinical.doctors ALTER COLUMN license_number DROP NOT NULL"))
            
            # Step 10: Drop the old name column
            print("  ➤ Dropping old name column...")
            await db.execute(text("ALTER TABLE clinical.doctors DROP COLUMN IF EXISTS name"))
            
            # Step 11: Add department field to invitations table
            print("  ➤ Adding department field to invitations...")
            await db.execute(text("ALTER TABLE auth.invitations ADD COLUMN IF NOT EXISTS department VARCHAR(255)"))
            
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
