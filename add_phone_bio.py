"""
Script để thêm cột phone và bio vào bảng users
Chạy: python add_phone_bio.py
"""
import sys
sys.path.insert(0, '.')

from app.database import engine
from sqlalchemy import text

def add_columns():
    """Add phone and bio columns to users table"""
    with engine.connect() as conn:
        try:
            # Check if column exists first
            result = conn.execute(text("SHOW COLUMNS FROM users LIKE 'phone'"))
            if not result.fetchone():
                conn.execute(text('ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL'))
                print("✅ Added 'phone' column")
            else:
                print("ℹ️ 'phone' column already exists")
            
            result = conn.execute(text("SHOW COLUMNS FROM users LIKE 'bio'"))
            if not result.fetchone():
                conn.execute(text('ALTER TABLE users ADD COLUMN bio VARCHAR(500) NULL'))
                print("✅ Added 'bio' column")
            else:
                print("ℹ️ 'bio' column already exists")
            
            conn.commit()
            print("🎉 Migration completed!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_columns()
