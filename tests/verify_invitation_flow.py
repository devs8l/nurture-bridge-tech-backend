import asyncio
import httpx
import sys
import os
import secrets
from typing import Dict, Any

# Add project root to python path
sys.path.append(os.getcwd())

async def verify_flow():
    print("🚀 Verifying Invitation System Flow...")
    
    # 1. Get Super Admin Credentials (Interactively or Hardcoded for testing)
    email = input("Enter Super Admin Email: ").strip()
    password = input("Enter Super Admin Password: ").strip()
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        # --- LOGIN SUPER ADMIN ---
        print(f"\n[Step 1] Logging in as Super Admin ({email})...")
        login_res = await client.post(f"{base_url}/auth/login", json={"email": email, "password": password})
        if login_res.status_code != 200:
            print(f"❌ Login Failed: {login_res.text}")
            return
        
        sa_token = login_res.json()["access_token"]
        sa_headers = {"Authorization": f"Bearer {sa_token}"}
        print("✅ Super Admin Logged In.")

        # --- CREATE TENANT ---
        print(f"\n[Step 2] Creating a new Tenant...")
        tenant_code = "INVITE-TEST-" + secrets.token_hex(4)
        tenant_payload = {
            "name": "Invitation Test Hospital",
            "code": tenant_code.upper() # Code checks upper case usually
        }
        tenant_res = await client.post(f"{base_url}/tenants/", json=tenant_payload, headers=sa_headers)
        
        if tenant_res.status_code not in [200, 201]:
             print(f"❌ Tenant Creation Failed: {tenant_res.text}")
             return
             
        tenant_id = tenant_res.json()["id"]
        print(f"✅ Tenant Created: {tenant_id} ({tenant_code})")

        # --- SEND INVITATION ---
        print(f"\n[Step 3] Sending Invitation to a new Tenant Admin...")
        new_admin_email = f"admin-{secrets.token_hex(4)}@test.com"
        invite_payload = {
            "email": new_admin_email,
            "role": "TENANT_ADMIN",
            "tenant_id": tenant_id
        }
        
        invite_res = await client.post(f"{base_url}/auth/invitations", json=invite_payload, headers=sa_headers)
        
        if invite_res.status_code != 200:
             print(f"❌ Invitation Failed: {invite_res.text}")
             return
        
        invite_data = invite_res.json()
        token = invite_data["token"]
        print(f"✅ Invitation Sent!")
        print(f"   - Email: {invite_data['email']}")
        print(f"   - Token: {token}")

        # --- ACCEPT INVITATION ---
        print(f"\n[Step 4] Accepting Invitation (Setting Password)...")
        # Simulate the new user clicking the link and setting password
        new_password = "NewStrongPassword123!"
        accept_payload = {
            "password": new_password,
            "confirm_password": new_password
        }
        
        # Note: In real app, this is a POST to /invitations/{token}/accept
        accept_res = await client.post(
            f"{base_url}/auth/invitations/{token}/accept", 
            json=accept_payload
            # No Auth headers required! It uses the token in URL.
        )
        
        if accept_res.status_code != 200:
             print(f"❌ Acceptance Failed: {accept_res.status_code} - {accept_res.text}")
             return
             
        print(f"✅ Invitation Accepted! User created.")

        # --- LOGIN AS NEW TENANT ADMIN ---
        print(f"\n[Step 5] Logging in as the NEW Tenant Admin...")
        new_login_res = await client.post(
            f"{base_url}/auth/login", 
            json={"email": new_admin_email, "password": new_password}
        )
        
        if new_login_res.status_code != 200:
             print(f"❌ New User Login Failed: {new_login_res.text}")
             return
        
        new_token_data = new_login_res.json()
        print(f"✅ Login Successful!")
        print(f"   - Role: {new_token_data.get('role')}")
        print(f"   - Tenant ID: {tenant_id}")
        
        print("\n🎉 SUCCESS! Full Onboarding Flow Verified.")

if __name__ == "__main__":
    try:
        asyncio.run(verify_flow())
    except ImportError:
        print("❌ Error: 'httpx' library missing.")
    except Exception as e:
        print(f"❌ Error: {e}")
