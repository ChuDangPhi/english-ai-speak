"""
Lesson models - Bài học và các bảng liên quan
"""
from sqlalchemy import Column, String, Boolean, DateTime, BigInteger, Integer, Text, Numeric, Enum, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class LessonType(str, enum.Enum):
    """Loại bài học"""
    VOCABULARY_MATCHING = "vocabulary_matching"
    PRONUNCIATION = "pronunciation"
    CONVERSATION = "conversation"
    MIXED = "mixed"


class ExerciseType(str, enum.Enum):
    """Loại bài tập phát âm"""
    WORD = "word"
    PHRASE = "phrase"
    SENTENCE = "sentence"


class Lesson(Base):
    """Model Lesson - Bài học trong chủ đề"""
    
    __tablename__ = "lessons"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    topic_id = Column(BigInteger, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_type = Column(Enum(LessonType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    lesson_order = Column(Integer, nullable=False)
    instructions = Column(Text, nullable=True)
    difficulty_level = Column(String(20), nullable=True)
    estimated_minutes = Column(Integer, default=5)
    passing_score = Column(Numeric(5, 2), default=70.00)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    topic = relationship("Topic", back_populates="lessons")
    lesson_vocabulary = relationship("LessonVocabulary", back_populates="lesson", cascade="all, delete-orphan")
    pronunciation_exercises = relationship("PronunciationExercise", back_populates="lesson", cascade="all, delete-orphan")
    conversation_templates = relationship("ConversationTemplate", back_populates="lesson", cascade="all, delete-orphan")
    lesson_attempts = relationship("LessonAttempt", back_populates="lesson", cascade="all, delete-orphan")
    user_lesson_progress = relationship("UserLessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Lesson(id={self.id}, title={self.title}, type={self.lesson_type})>"


class LessonVocabulary(Base):
    """Model LessonVocabulary - Liên kết Lesson và Vocabulary (M:M)"""
    
    __tablename__ = "lesson_vocabulary"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lesson_id = Column(BigInteger, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    vocabulary_id = Column(BigInteger, ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False, index=True)
    display_order = Column(Integer, default=0)
    is_key_word = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    lesson = relationship("Lesson", back_populates="lesson_vocabulary")
    vocabulary = relationship("Vocabulary", back_populates="lesson_vocabulary")
    
    def __repr__(self):
        return f"<LessonVocabulary(lesson_id={self.lesson_id}, vocabulary_id={self.vocabulary_id})>"


class PronunciationExercise(Base):
    """Model PronunciationExercise - Bài tập phát âm"""
    
    __tablename__ = "pronunciation_exercises"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    lesson_id = Column(BigInteger, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_type = Column(Enum(ExerciseType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    content = Column(Text, nullable=False)  # Nội dung cần đọc (word/phrase/sentence)
    phonetic = Column(String(255), nullable=True)
    audio_url = Column(String(500), nullable=True)  # Audio mẫu
    target_pronunciation_score = Column(Numeric(5, 2), default=70.00)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    lesson = relationship("Lesson", back_populates="pronunciation_exercises")
    pronunciation_attempts = relationship("PronunciationAttempt", back_populates="exercise", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PronunciationExercise(id={self.id}, type={self.exercise_type})>"


class ConversationTemplate(Base):
    """Model ConversationTemplate - Template hội thoại với AI"""
    
    __tablename__ = "conversation_templates"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    lesson_id = Column(BigInteger, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_role = Column(String(100), nullable=False)  # VD: "Barista at a coffee shop"
    scenario_context = Column(Text, nullable=False)  # VD: "You are ordering coffee at a cafe..."
    starter_prompts = Column(JSON, nullable=True)  # Câu mở đầu gợi ý cho user
    suggested_topics = Column(JSON, nullable=True)  # Các chủ đề gợi ý trong conversation
    min_turns = Column(Integer, default=5)  # Số lượt tối thiểu
    max_duration_minutes = Column(Integer, default=10)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    lesson = relationship("Lesson", back_populates="conversation_templates")
    
    def __repr__(self):
        return f"<ConversationTemplate(id={self.id}, ai_role={self.ai_role})>"
