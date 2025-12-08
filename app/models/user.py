"""
User model - Định nghĩa bảng users trong database
"""
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, BigInteger, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, Enum):
    """Enum cho role của user"""
    ADMIN = "admin"
    USER = "user"


class User(Base):
    """
    Model User - Bảng lưu thông tin người dùng
    
    Các thuộc tính:
    - id: Khóa chính BIGINT UNSIGNED AUTO_INCREMENT
    - email: Email đăng nhập, duy nhất
    - password_hash: Mật khẩu đã mã hóa (KHÔNG lưu plain text)
    - full_name: Họ tên đầy đủ
    - avatar_url: URL ảnh đại diện
    - current_level: Trình độ hiện tại (beginner, intermediate, advanced)
    - is_active: Trạng thái tài khoản (active/inactive)
    - created_at: Thời gian tạo tài khoản
    - updated_at: Thời gian cập nhật gần nhất
    """
    
    __tablename__ = "users"
    
    # Khóa chính - BIGINT UNSIGNED AUTO_INCREMENT
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    
    # Email - Duy nhất, không được null, có index để tìm kiếm nhanh
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Password đã hash - Không được null
    password_hash = Column(String(255), nullable=False)
    
    # Họ tên - Có thể null
    full_name = Column(String(100), nullable=True)
    
    # Avatar URL - Có thể null
    avatar_url = Column(String(500), nullable=True)
    
    # Level hiện tại - Mặc định là "beginner"
    current_level = Column(String(20), default="beginner", nullable=True)
    
    # Trạng thái tài khoản - Mặc định là active (True)
    is_active = Column(Boolean, default=True, nullable=True)
    
    # Role - admin hoặc user, mặc định là user
    role = Column(String(20), default="user", nullable=False)
    
    # Thời gian tạo - Tự động lấy thời gian hiện tại
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    
    # Thời gian cập nhật - Tự động cập nhật khi có thay đổi
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    
    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    lesson_attempts = relationship("LessonAttempt", back_populates="user", cascade="all, delete-orphan")
    lesson_progress = relationship("UserLessonProgress", back_populates="user", cascade="all, delete-orphan")
    topic_progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    user_vocabulary = relationship("UserVocabulary", back_populates="user", cascade="all, delete-orphan")
    daily_stats = relationship("DailyStats", back_populates="user", cascade="all, delete-orphan")
    streak = relationship("UserStreak", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        """Hiển thị thông tin object khi print"""
        return f"<User(id={self.id}, email={self.email})>"


class UserSettings(Base):
    """Model UserSettings - Cài đặt người dùng"""
    
    __tablename__ = "user_settings"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    ai_voice_type = Column(String(50), default="female_us")
    daily_goal_minutes = Column(Integer, default=15)
    notification_enabled = Column(Boolean, default=True)
    theme = Column(String(20), default="light")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id})>"