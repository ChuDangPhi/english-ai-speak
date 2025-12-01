"""
Topic model - Chủ đề học tập
"""
from sqlalchemy import Column, String, Boolean, DateTime, BigInteger, Integer, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Topic(Base):
    """Model Topic - Chủ đề học tập chính"""
    
    __tablename__ = "topics"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="general", index=True)
    difficulty_level = Column(String(20), nullable=False, index=True)
    thumbnail_url = Column(String(500), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    total_lessons = Column(Integer, default=0)
    display_order = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lessons = relationship("Lesson", back_populates="topic", cascade="all, delete-orphan")
    user_progress = relationship("UserProgress", back_populates="topic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Topic(id={self.id}, title={self.title})>"
