"""
User model - Định nghĩa bảng users trong database
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base
import uuid


class User(Base):
    """
    Model User - Bảng lưu thông tin người dùng
    
    Các thuộc tính:
    - id: Khóa chính UUID (CHAR(36))
    - email: Email đăng nhập, duy nhất
    - password_hash: Mật khẩu đã mã hóa (KHÔNG lưu plain text)
    - full_name: Họ tên đầy đủ
    - avatar_url: URL ảnh đại diện
    - current_level: Trình độ hiện tại (beginner, intermediate, advanced)
    - is_active: Trạng thái tài khoản (active/inactive)
    - created_at: Thời gian tạo tài khoản
    - updated_at: Thời gian cập nhật gần nhất
    """
    
    __tablename__ = "users"  # Tên bảng trong database
    
    # Khóa chính - UUID string (36 ký tự)
    # default=lambda: str(uuid.uuid4()) - Tự động tạo UUID mới khi insert
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Email - Duy nhất, không được null, có index để tìm kiếm nhanh
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Password đã hash - Không được null
    # Lưu ý: Tên cột trong DB là "password_hash" (không phải "hashed_password")
    password_hash = Column(String(255), nullable=False)
    
    # Họ tên - Có thể null
    full_name = Column(String(100), nullable=True)
    
    # Avatar URL - Có thể null
    avatar_url = Column(String(500), nullable=True)
    
    # Level hiện tại - Mặc định là "beginner"
    # Các giá trị: beginner, intermediate, advanced
    current_level = Column(String(20), default="beginner", nullable=True)
    
    # Trạng thái tài khoản - Mặc định là active (True)
    is_active = Column(Boolean, default=True, nullable=True)
    
    # Thời gian tạo - Tự động lấy thời gian hiện tại
    # server_default=func.now(): MySQL tự động set CURRENT_TIMESTAMP
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    
    # Thời gian cập nhật - Tự động cập nhật khi có thay đổi
    # onupdate=func.now(): MySQL tự động update khi record thay đổi
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    
    def __repr__(self):
        """Hiển thị thông tin object khi print"""
        return f"<User(id={self.id}, email={self.email})>"