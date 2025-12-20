"""
Run this ONCE to create database schemas and tables
Creates: auth, tenant, clinical, intake, audit schemas and all their tables
Excludes: assessment schema (managed separately)
"""
import asyncio
from sqlalchemy import text

async def setup():
    from db.base import engine
    from db.models.tenant import Tenant
    from db.models.auth import User, Invitation
    from db.models.clinical import Doctor, Parent, Child, HOD, Receptionist
    from db.models.intake import IntakeSection, IntakeQuestion, IntakeResponse, IntakeAnswer
    from db.models.assessment import AssessmentSection, AssessmentQuestion, AssessmentResponse, AssessmentQuestionAnswer
    from db.models.audit import AuditLog
    
    async with engine.begin() as conn:
        print("=" * 60)
        print("DATABASE INITIALIZATION")
        print("=" * 60)
        
        # Step 1: Create all schemas first
        print("\n[1/3] Creating schemas...")
        schemas = ["auth", "tenant", "clinical", "intake", "assessment", "audit"]
        for schema in schemas:
            print(f"  - Creating {schema} schema...")
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        print("✓ All schemas created")
        
        # Step 2: Create tables in dependency order
        print("\n[2/3] Creating tables...")
        
        # Base tables (no foreign keys to other tables)
        print("  - Creating tenants table...")
        await conn.run_sync(lambda sync_conn: Tenant.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating users table...")
        await conn.run_sync(lambda sync_conn: User.__table__.create(sync_conn, checkfirst=True))
        
        # Tables with FK to users/tenants
        print("  - Creating doctors table...")
        await conn.run_sync(lambda sync_conn: Doctor.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating hods table...")
        await conn.run_sync(lambda sync_conn: HOD.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating receptionists table...")
        await conn.run_sync(lambda sync_conn: Receptionist.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating invitations table...")
        await conn.run_sync(lambda sync_conn: Invitation.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating parents table...")
        await conn.run_sync(lambda sync_conn: Parent.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating children table...")
        await conn.run_sync(lambda sync_conn: Child.__table__.create(sync_conn, checkfirst=True))
        
        # Intake tables
        print("  - Creating intake sections table...")
        await conn.run_sync(lambda sync_conn: IntakeSection.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating intake questions table...")
        await conn.run_sync(lambda sync_conn: IntakeQuestion.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating intake responses table...")
        await conn.run_sync(lambda sync_conn: IntakeResponse.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating intake answers table...")
        await conn.run_sync(lambda sync_conn: IntakeAnswer.__table__.create(sync_conn, checkfirst=True))
        
        # Assessment tables
        print("  - Creating assessment sections table...")
        await conn.run_sync(lambda sync_conn: AssessmentSection.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating assessment questions table...")
        await conn.run_sync(lambda sync_conn: AssessmentQuestion.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating assessment responses table...")
        await conn.run_sync(lambda sync_conn: AssessmentResponse.__table__.create(sync_conn, checkfirst=True))
        
        print("  - Creating assessment question answers table...")
        await conn.run_sync(lambda sync_conn: AssessmentQuestionAnswer.__table__.create(sync_conn, checkfirst=True))
        
        # Audit table
        print("  - Creating audit logs table...")
        await conn.run_sync(lambda sync_conn: AuditLog.__table__.create(sync_conn, checkfirst=True))
        
        print("✓ All tables created")
        
        print("\n[3/3] Cleanup...")
    
    await engine.dispose()
    print("\n" + "=" * 60)
    print("✓ DATABASE INITIALIZATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(setup())
