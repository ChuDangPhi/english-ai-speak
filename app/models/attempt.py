"""
Attempt models - Lưu trữ kết quả làm bài của user
"""
from sqlalchemy import Column, String, Boolean, DateTime, BigInteger, Integer, Text, Numeric, Enum, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SpeakerType(str, enum.Enum):
    """Người nói trong hội thoại"""
    USER = "user"
    AI = "ai"


class LessonAttempt(Base):
    """Model LessonAttempt - Lần làm bài của user"""
    
    __tablename__ = "lesson_attempts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(BigInteger, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, default=1)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Scores tổng hợp
    overall_score = Column(Numeric(5, 2), nullable=True)
    
    # Vocabulary matching scores
    vocabulary_correct = Column(Integer, default=0)
    vocabulary_total = Column(Integer, default=0)
    
    # Pronunciation scores (3 tiêu chí)
    pronunciation_score = Column(Numeric(5, 2), nullable=True)  # Phát âm
    intonation_score = Column(Numeric(5, 2), nullable=True)     # Ngữ điệu
    stress_score = Column(Numeric(5, 2), nullable=True)         # Trọng âm
    
    # Conversation scores
    conversation_turns = Column(Integer, default=0)
    fluency_score = Column(Numeric(5, 2), nullable=True)
    grammar_score = Column(Numeric(5, 2), nullable=True)
    
    ai_feedback = Column(Text, nullable=True)
    is_passed = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="lesson_attempts")
    lesson = relationship("Lesson", back_populates="lesson_attempts")
    pronunciation_attempts = relationship("PronunciationAttempt", back_populates="lesson_attempt", cascade="all, delete-orphan")
    vocabulary_results = relationship("VocabularyMatchingResult", back_populates="lesson_attempt", cascade="all, delete-orphan")
    conversation_messages = relationship("ConversationMessage", back_populates="lesson_attempt", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LessonAttempt(id={self.id}, user_id={self.user_id}, lesson_id={self.lesson_id})>"


class PronunciationAttempt(Base):
    """Model PronunciationAttempt - Chi tiết đánh giá phát âm từng bài tập"""
    
    __tablename__ = "pronunciation_attempts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    lesson_attempt_id = Column(BigInteger, ForeignKey("lesson_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(BigInteger, ForeignKey("pronunciation_exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    audio_url = Column(String(500), nullable=True)  # Audio người dùng ghi
    transcription = Column(Text, nullable=True)  # Kết quả speech-to-text
    
    # Scores (3 tiêu chí đánh giá chính)
    pronunciation_score = Column(Numeric(5, 2), nullable=True)  # Phát âm chuẩn
    intonation_score = Column(Numeric(5, 2), nullable=True)     # Ngữ điệu
    stress_score = Column(Numeric(5, 2), nullable=True)         # Trọng âm
    accuracy_score = Column(Numeric(5, 2), nullable=True)       # Độ chính xác tổng
    
    detailed_feedback = Column(JSON, nullable=True)  # Chi tiết từng âm tiết
    suggestions = Column(Text, nullable=True)  # Gợi ý cải thiện
    attempt_number = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    lesson_attempt = relationship("LessonAttempt", back_populates="pronunciation_attempts")
    exercise = relationship("PronunciationExercise", back_populates="pronunciation_attempts")
    
    def __repr__(self):
        return f"<PronunciationAttempt(id={self.id}, exercise_id={self.exercise_id})>"


class VocabularyMatchingResult(Base):
    """Model VocabularyMatchingResult - Kết quả game nối từ với nghĩa"""
    
    __tablename__ = "vocabulary_matching_results"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    lesson_attempt_id = Column(BigInteger, ForeignKey("lesson_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    vocabulary_id = Column(BigInteger, ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False, index=True)
    user_answer = Column(String(255), nullable=True)  # Câu trả lời của user
    is_correct = Column(Boolean, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)  # Thời gian trả lời
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    lesson_attempt = relationship("LessonAttempt", back_populates="vocabulary_results")
    vocabulary = relationship("Vocabulary", back_populates="matching_results")
    
    def __repr__(self):
        return f"<VocabularyMatchingResult(id={self.id}, is_correct={self.is_correct})>"


class ConversationMessage(Base):
    """Model ConversationMessage - Lịch sử hội thoại với AI"""
    
    __tablename__ = "conversation_messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    lesson_attempt_id = Column(BigInteger, ForeignKey("lesson_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    message_order = Column(Integer, nullable=False)  # Thứ tự tin nhắn
    speaker = Column(Enum(SpeakerType, values_callable=lambda x: [e.value for e in x]), nullable=False)  # user hoặc ai
    message_text = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=True)  # Audio nếu user nói
    grammar_errors = Column(JSON, nullable=True)  # Lỗi ngữ pháp phát hiện được
    vocabulary_used = Column(JSON, nullable=True)  # Từ vựng đã sử dụng
    sentiment = Column(String(50), nullable=True)  # positive, negative, neutral
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    lesson_attempt = relationship("LessonAttempt", back_populates="conversation_messages")
    
    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, speaker={self.speaker})>"
