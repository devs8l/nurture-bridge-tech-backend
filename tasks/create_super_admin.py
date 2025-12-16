import asyncio
import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

from db.base import async_session
from db.models.auth import User, UserRole, UserStatus
from app.core.security import hash_password

async def create_super_admin():
    print("👑 Creating Super Admin User...")
    
    email = input("Enter Email (default: admin@example.com): ").strip() or "admin@example.com"
    password = input("Enter Password (default: Admin123!): ").strip() or "Admin123!"
    
    async with async_session() as db:
        # Check if user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"⚠️  User {email} already exists!")
            update = input("Do you want to update their role to SUPER_ADMIN? (y/n): ").lower()
            if update == 'y':
                existing_user.role = UserRole.SUPER_ADMIN
                existing_user.status = UserStatus.ACTIVE
                await db.commit()
                print("✅ User updated to SUPER_ADMIN.")
            return

        # Create new user
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        print(f"✅ Super Admin created successfully!")
        print(f"📧 Email: {new_user.email}")
        print(f"🔑 ID: {new_user.id}")

if __name__ == "__main__":
    try:
        asyncio.run(create_super_admin())
    except Exception as e:
        print(f"❌ Error: {e}")
