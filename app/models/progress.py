"""
Progress models - Theo dõi tiến độ học tập của user
"""
from sqlalchemy import Column, String, Boolean, DateTime, BigInteger, Integer, Numeric, Enum, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class LessonStatus(str, enum.Enum):
    """Trạng thái bài học của user"""
    LOCKED = "LOCKED"           # Chưa mở khóa
    AVAILABLE = "AVAILABLE"     # Đã mở, chưa học
    IN_PROGRESS = "IN_PROGRESS" # Đang học
    COMPLETED = "COMPLETED"     # Đã hoàn thành


class UserLessonProgress(Base):
    """Model UserLessonProgress - Tiến độ từng bài học của user"""
    
    __tablename__ = "user_lesson_progress"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(BigInteger, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(LessonStatus), default=LessonStatus.LOCKED)
    best_score = Column(Numeric(5, 2), nullable=True)
    total_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    first_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="user_lesson_progress")
    
    def __repr__(self):
        return f"<UserLessonProgress(user_id={self.user_id}, lesson_id={self.lesson_id}, status={self.status})>"


class UserProgress(Base):
    """Model UserProgress - Tiến độ từng chủ đề của user"""
    
    __tablename__ = "user_progress"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(BigInteger, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="not_started")  # not_started, in_progress, completed
    lessons_completed = Column(Integer, default=0)
    total_lessons = Column(Integer, default=0)
    times_practiced = Column(Integer, default=0)
    best_score = Column(Numeric(5, 2), nullable=True)
    last_practiced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="topic_progress")
    topic = relationship("Topic", back_populates="user_progress")
    
    def __repr__(self):
        return f"<UserProgress(user_id={self.user_id}, topic_id={self.topic_id})>"


class UserVocabulary(Base):
    """Model UserVocabulary - Từ vựng user đã gặp và học"""
    
    __tablename__ = "user_vocabulary"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vocabulary_id = Column(BigInteger, ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False, index=True)
    times_encountered = Column(Integer, default=1)  # Số lần gặp
    times_correct = Column(Integer, default=0)      # Số lần trả lời đúng
    is_saved = Column(Boolean, default=False)       # User đánh dấu yêu thích
    mastery_level = Column(String(20), default="learning")  # learning, familiar, mastered
    last_seen_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_vocabulary")
    vocabulary = relationship("Vocabulary", back_populates="user_vocabulary")
    
    def __repr__(self):
        return f"<UserVocabulary(user_id={self.user_id}, vocabulary_id={self.vocabulary_id})>"


class DailyStats(Base):
    """Model DailyStats - Thống kê học tập hàng ngày"""
    
    __tablename__ = "daily_stats"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    practice_date = Column(Date, nullable=False)
    total_sessions = Column(Integer, default=0)     # Số phiên học
    total_minutes = Column(Integer, default=0)      # Tổng thời gian học (phút)
    lessons_completed = Column(Integer, default=0)  # Số bài hoàn thành
    average_score = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="daily_stats")
    
    def __repr__(self):
        return f"<DailyStats(user_id={self.user_id}, date={self.practice_date})>"


class UserStreak(Base):
    """Model UserStreak - Streak học tập liên tục"""
    
    __tablename__ = "user_streaks"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    current_streak = Column(Integer, default=0)   # Streak hiện tại
    longest_streak = Column(Integer, default=0)   # Streak dài nhất
    last_activity_date = Column(Date, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="streak")
    
    def __repr__(self):
        return f"<UserStreak(user_id={self.user_id}, current={self.current_streak})>"
