
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())

from app.services.auth_service import AuthService
from app.core.security import hash_password

# Import ALL models to ensure SQLAlchemy registry is populated
# This prevents "KeyError: 'Section'" or "InvalidRequestError"
import db.models.auth as auth_models
import db.models.tenant as tenant_models
import db.models.clinical as clinical_models
import db.models.intake as intake_models
import db.models.assessment as assessment_models
import db.models.audit as audit_models

# Use short aliases for convenience if needed, but we mostly need the side-effect of importing
User = auth_models.User
UserRole = auth_models.UserRole
UserStatus = auth_models.UserStatus


async def verify_auth_flow():
    print("🚀 Starting Auth Flow Verification...")
    
    # 1. Setup Service and Mock DB
    service = AuthService()
    mock_db = AsyncMock()
    
    # Mock UserRepo interactions since we don't have a real DB running
    # We will assume UserRepo works (unit tested separately) or just patch it?
    # For this verification script to run STANDALONE, we need to bypass the actual DB calls.
    # But AuthService calls UserRepo which calls DB.
    
    # Let's mock the UserRepo METHODS on the service instance if possible, 
    # but service instantiates UserRepo in __init__. 
    # So we patch the instance's user_repo.
    service.user_repo = MagicMock()
    service.user_repo.get_by_email = AsyncMock(return_value=None) # Initially no user
    service.user_repo.create_from_invitation = AsyncMock()
    
    # 2. Test Invitation Acceptance
    print("\n[Step 1] Testing Invitation Acceptance...")
    token = "mock-token:newuser@example.com:DOCTOR:123e4567-e89b-12d3-a456-426614174000"
    password = "securePassword123!"
    
    # Setup create return value
    created_user = User(
        id="user-123",
        email="newuser@example.com",
        hashed_password=hash_password(password),
        role=UserRole.DOCTOR,
        status=UserStatus.ACTIVE
    )
    service.user_repo.create_from_invitation.return_value = created_user
    
    user = await service.accept_invitation(mock_db, token, password)
    
    print(f"✅ Invitation Accepted! User Created: {user.email} with Role: {user.role}")
    
    # 3. Test Login
    print("\n[Step 2] Testing Login...")
    # Setup get_by_email to return the user now
    service.user_repo.get_by_email.return_value = created_user
    
    login_user = await service.authenticate_user(mock_db, "newuser@example.com", password)
    
    if login_user:
        print(f"✅ Login Successful for: {login_user.email}")
    else:
        print("❌ Login Failed!")
        return

    # 4. Test Token Generation (Real Logic)
    print("\n[Step 3] Testing Token Generation...")
    from app.core.security import create_access_token, decode_token
    
    token = create_access_token({"sub": "user-123", "email": login_user.email, "roles": [login_user.role]})
    print(f"Generated Token: {token[:20]}...")
    
    decoded = decode_token(token)
    print(f"✅ Token Verified! Sub: {decoded['sub']}, Roles: {decoded['roles']}")

if __name__ == "__main__":
    asyncio.run(verify_auth_flow())
