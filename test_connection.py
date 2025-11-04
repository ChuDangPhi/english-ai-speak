"""
Script kiểm tra kết nối database và hiển thị thông tin bảng
"""
from sqlalchemy import inspect, text
from app.database import engine, SessionLocal
from app.config import settings

def test_connection():
    """Kiểm tra kết nối MySQL"""
    print("=" * 60)
    print("🔌 KIỂM TRA KẾT NỐI DATABASE")
    print("=" * 60)
    
    try:
        # Test 1: Kết nối cơ bản
        print("\n[1] Đang kết nối đến MySQL...")
        print(f"    Host: {settings.DATABASE_HOST}")
        print(f"    Port: {settings.DATABASE_PORT}")
        print(f"    Database: {settings.DATABASE_NAME}")
        print(f"    User: {settings.DATABASE_USER}")
        
        with engine.connect() as connection:
            print("    ✅ Kết nối thành công!")
            
            # Test 2: Lấy phiên bản MySQL
            print("\n[2] Thông tin MySQL Server:")
            result = connection.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"    Version: {version}")
            
            # Test 3: Kiểm tra database hiện tại
            result = connection.execute(text("SELECT DATABASE()"))
            current_db = result.scalar()
            print(f"    Current Database: {current_db}")
            
            # Test 4: Đếm số bảng
            result = connection.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = :db_name"
            ), {"db_name": settings.DATABASE_NAME})
            table_count = result.scalar()
            print(f"    Số bảng: {table_count}")
        
        # Test 5: Liệt kê tất cả bảng
        print("\n[3] Danh sách các bảng:")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            print("    ⚠️ Chưa có bảng nào trong database!")
        else:
            for idx, table in enumerate(tables, 1):
                print(f"    {idx:2d}. {table}")
        
        # Test 6: Kiểm tra cấu trúc bảng users (nếu có)
        if 'users' in tables:
            print("\n[4] Cấu trúc bảng 'users':")
            columns = inspector.get_columns('users')
            print(f"    {'Column':<20} {'Type':<25} {'Nullable':<10} {'Default'}")
            print(f"    {'-'*20} {'-'*25} {'-'*10} {'-'*20}")
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                nullable = 'YES' if col['nullable'] else 'NO'
                default = str(col.get('default', 'NULL'))
                print(f"    {col_name:<20} {col_type:<25} {nullable:<10} {default}")
        
        # Test 7: Đếm số records trong mỗi bảng
        if tables:
            print("\n[5] Số lượng records trong các bảng:")
            db = SessionLocal()
            try:
                for table in tables:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    status = "✅" if count > 0 else "📭"
                    print(f"    {status} {table:<30} {count:>5} records")
            finally:
                db.close()
        
        print("\n" + "=" * 60)
        print("✅ TẤT CẢ KIỂM TRA HOÀN TẤT!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ LỖI KẾT NỐI!")
        print("=" * 60)
        print(f"Chi tiết lỗi: {str(e)}")
        print("\n💡 Hướng dẫn khắc phục:")
        print("   1. Kiểm tra MySQL đã chạy chưa:")
        print("      - Mở Services (services.msc)")
        print("      - Tìm MySQL và Start")
        print("   2. Kiểm tra thông tin trong file .env:")
        print("      - DATABASE_HOST=localhost")
        print("      - DATABASE_PORT=3306")
        print("      - DATABASE_USER=root")
        print("      - DATABASE_PASSWORD=phi123455")
        print("      - DATABASE_NAME=ai_english_tutor")
        print("   3. Kiểm tra database đã tạo chưa:")
        print("      - mysql -u root -p")
        print("      - CREATE DATABASE ai_english_tutor;")
        print("   4. Kiểm tra user có quyền truy cập:")
        print("      - GRANT ALL ON ai_english_tutor.* TO 'root'@'localhost';")
        return False

if __name__ == "__main__":
    test_connection()
