"""
Test model User với database thực tế
"""
from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def test_user_model():
    """Test CRUD operations với User model"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("🧪 TEST USER MODEL")
        print("=" * 60)
        
        # Test 1: Tạo user mới
        print("\n[1] Tạo user mới...")
        test_user = User(
            email="test@example.com",
            password_hash=hash_password("password123"),
            full_name="Test User",
            current_level="beginner",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"    ✅ Tạo user thành công!")
        print(f"    ID: {test_user.id}")
        print(f"    Email: {test_user.email}")
        print(f"    UUID format: {len(test_user.id)} ký tự")
        
        # Test 2: Đọc user vừa tạo
        print("\n[2] Đọc user từ database...")
        user_from_db = db.query(User).filter(User.email == "test@example.com").first()
        if user_from_db:
            print(f"    ✅ Tìm thấy user:")
            print(f"    ID: {user_from_db.id}")
            print(f"    Email: {user_from_db.email}")
            print(f"    Full Name: {user_from_db.full_name}")
            print(f"    Level: {user_from_db.current_level}")
            print(f"    Active: {user_from_db.is_active}")
            print(f"    Created: {user_from_db.created_at}")
        
        # Test 3: Update user
        print("\n[3] Cập nhật user...")
        user_from_db.full_name = "Updated Test User"
        user_from_db.current_level = "intermediate"
        db.commit()
        print(f"    ✅ Cập nhật thành công!")
        
        # Test 4: Đếm tổng số users
        print("\n[4] Đếm tổng số users...")
        total = db.query(User).count()
        print(f"    Tổng số users trong DB: {total}")
        
        # Test 5: Xóa user test
        print("\n[5] Xóa user test...")
        db.delete(user_from_db)
        db.commit()
        print(f"    ✅ Xóa user thành công!")
        
        # Kiểm tra lại
        remaining = db.query(User).count()
        print(f"    Số users còn lại: {remaining}")
        
        print("\n" + "=" * 60)
        print("✅ TẤT CẢ TEST HOÀN TẤT!")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_user_model()
