"""
Vocabulary model - Từ vựng
"""
from sqlalchemy import Column, String, DateTime, BigInteger, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Vocabulary(Base):
    """Model Vocabulary - Từ vựng tiếng Anh"""
    
    __tablename__ = "vocabulary"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    word = Column(String(100), unique=True, nullable=False, index=True)
    phonetic = Column(String(100), nullable=True)
    definition = Column(Text, nullable=False)
    example_sentence = Column(Text, nullable=True)
    audio_url = Column(String(500), nullable=True)
    difficulty_level = Column(String(20), nullable=True, index=True)
    part_of_speech = Column(String(20), nullable=True)  # noun, verb, adj, adv, etc.
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    lesson_vocabulary = relationship("LessonVocabulary", back_populates="vocabulary", cascade="all, delete-orphan")
    user_vocabulary = relationship("UserVocabulary", back_populates="vocabulary", cascade="all, delete-orphan")
    matching_results = relationship("VocabularyMatchingResult", back_populates="vocabulary", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vocabulary(id={self.id}, word={self.word})>"
