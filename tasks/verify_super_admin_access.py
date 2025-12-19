import asyncio
import httpx
import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

async def verify_access():
    print("🔐 Verifying Super Admin Access...")
    
    email = input("Enter Super Admin Email: ").strip()
    password = input("Enter Super Admin Password: ").strip()
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        print(f"\n[Step 1] Logging in as {email}...")
        try:
            # LoginRequest schema expects "email" and "password"
            login_payload = {
                "email": email,
                "password": password
            }
            # Note: The auth endpoint might be named differently, checking implementation...
            # app/api/v1/endpoints/auth.py -> @router.post("/login")
            response = await client.post(f"{base_url}/auth/login", json=login_payload)
            
            if response.status_code != 200:
                print(f"❌ Login Failed: {response.text}")
                return
                
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login Successful! Token received.")
            
        except Exception as e:
             print(f"❌ Connection Error (is server running?): {e}")
             return

        # 2. Access Protected Tenant Endpoint
        print(f"\n[Step 2] Accessing Protected Tenant API...")
        headers = {"Authorization": f"Bearer {token}"}
        print(token)
        
        try:
            # GET /tenants/ (List tenants)
            response = await client.get(f"{base_url}/tenants/", headers=headers)
            
            if response.status_code == 200:
                tenants = response.json()
                print(f"✅ Access Granted! Found {len(tenants)} tenants.")
                print(f"📜 Tenants: {tenants}")
            elif response.status_code == 403:
                print(f"❌ 403 Forbidden: Account does not have SUPER_ADMIN role.")
            else:
                 print(f"❌ Request Failed: {response.status_code} - {response.text}")

        except Exception as e:
             print(f"❌ Error calling API: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(verify_access())
    except ImportError:
        print("❌ Error: 'httpx' library missing. Install it with: pip install httpx")
    except KeyboardInterrupt:
        print("\nAborted.")
