"""
Seed Admin User - Tạo tài khoản admin mặc định
Chạy: python -m app.seeding.seed_admin
Nâng cấp user: python -m app.seeding.seed_admin --make-admin email@example.com
"""
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import SessionLocal
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Admin role value
ADMIN_ROLE = "admin"
USER_ROLE = "user"


def seed_admin_user():
    """Tạo tài khoản admin mặc định nếu chưa tồn tại"""
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin_email = "admin@example.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if existing_admin:
            print(f"⚠️  Admin user already exists: {admin_email}")
            # Update to admin if not already
            if existing_admin.role != ADMIN_ROLE:
                existing_admin.role = ADMIN_ROLE
                db.commit()
                print(f"✅ Updated user to admin role")
            return existing_admin
        
        # Create admin user
        admin_user = User(
            email=admin_email,
            password_hash=pwd_context.hash("admin123"),  # Default password
            full_name="System Administrator",
            role=ADMIN_ROLE,
            is_active=True,
            current_level="advanced"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"")
        print(f"✅ Created admin user successfully!")
        print(f"")
        print(f"   📧 Email:    {admin_email}")
        print(f"   🔑 Password: admin123")
        print(f"   👤 Role:     {admin_user.role}")
        print(f"")
        print(f"⚠️  IMPORTANT: Change the password after first login!")
        print(f"")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def make_user_admin(email: str):
    """Nâng cấp 1 user thành admin"""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            return None
        
        if user.role == ADMIN_ROLE:
            print(f"⚠️  User {email} is already an admin")
            return user
        
        user.role = ADMIN_ROLE
        db.commit()
        db.refresh(user)
        
        print(f"✅ User {email} is now an admin!")
        return user
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def list_admins():
    """Liệt kê tất cả admin users"""
    db = SessionLocal()
    
    try:
        admins = db.query(User).filter(User.role == ADMIN_ROLE).all()
        
        if not admins:
            print("📋 No admin users found")
            return []
        
        print(f"📋 Admin users ({len(admins)}):")
        print("-" * 50)
        for admin in admins:
            status = "🟢 Active" if admin.is_active else "🔴 Inactive"
            print(f"  ID: {admin.id} | {admin.email} | {admin.full_name or 'N/A'} | {status}")
        print("-" * 50)
        
        return admins
        
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--make-admin" and len(sys.argv) > 2:
            email = sys.argv[2]
            make_user_admin(email)
        
        elif command == "--list":
            list_admins()
        
        else:
            print("Usage:")
            print("  python -m app.seeding.seed_admin              # Create default admin")
            print("  python -m app.seeding.seed_admin --make-admin <email>  # Make user admin")
            print("  python -m app.seeding.seed_admin --list       # List all admins")
    else:
        seed_admin_user()
