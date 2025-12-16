import asyncio
import sys
import os
from uuid import uuid4

# Add project root to python path
sys.path.append(os.getcwd())

# Import all models to ensure Registry is populated (Fix for KeyError)
import db.models.auth
import db.models.tenant
import db.models.clinical
import db.models.intake
import db.models.assessment
import db.models.audit

from db.base import async_session
from app.services.tenant_service import TenantService
from app.schemas.tenant import TenantCreate, TenantUpdate
from db.models.tenant import TenantStatus

async def verify_tenant_flow():
    print("🚀 Starting Tenant Service Verification...")
    
    async with async_session() as db:
        service = TenantService()
        
        # 1. Create Tenant
        print("\n[Step 1] Creating New Tenant...")
        code = f"TEST-HOSPITAL-{str(uuid4())[:8]}"
        tenant_in = TenantCreate(
            name="Test General Hospital",
            code=code,
            registration_number="REG-12345",
            registration_authority="Health Dept",
            accreditation_type="JCI"
        )
        
        try:
            tenant = await service.create_tenant(db, obj_in=tenant_in)
            print(f"✅ Tenant Created: {tenant.name} ({tenant.code}) - Status: {tenant.status}")
        except Exception as e:
            print(f"❌ Failed to create tenant: {e}")
            return

        # 2. Test Duplicate Code
        print("\n[Step 2] Testing Duplicate Code Check...")
        try:
            await service.create_tenant(db, obj_in=tenant_in)
            print("❌ Error: Duplicate Code was allowed!")
        except Exception as e:
            if "already exists" in str(e):
                print("✅ Duplicate Code Rejected correctly.")
            else:
                print(f"❌ Unexpected error during duplicate check: {e}")

        # 3. Update Tenant
        print("\n[Step 3] Updating Tenant (PATCH)...")
        update_in = TenantUpdate(
            name="Updated Hospital Name",
            status=TenantStatus.SUSPENDED
        )
        updated_tenant = await service.update_tenant(db, tenant_id=tenant.id, obj_in=update_in)
        
        if updated_tenant.name == "Updated Hospital Name" and updated_tenant.status == TenantStatus.SUSPENDED:
             print(f"✅ Tenant Updated: Name='{updated_tenant.name}', Status='{updated_tenant.status}'")
        else:
             print(f"❌ Update Verification Failed: {updated_tenant}")

        # 4. List Tenants
        print("\n[Step 4] Listing Tenants...")
        tenants = await service.list_tenants(db)
        print(f"✅ Found {len(tenants)} tenants in database.")

if __name__ == "__main__":
    try:
        asyncio.run(verify_tenant_flow())
    except ImportError as e:
         print(f"❌ Import Error: {e}. Check your PYTHONPATH.")
    except Exception as e:
         print(f"❌ Verification Failed: {e}")
