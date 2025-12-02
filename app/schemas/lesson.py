"""
Lesson schemas - Cấu trúc dữ liệu cho Bài học

GIẢI THÍCH BẢNG LESSONS:
=========================
Bảng `lessons` lưu trữ các bài học trong mỗi chủ đề.
Mỗi topic có 3 loại lesson theo thứ tự:

1. VOCABULARY_MATCHING (Lesson 1):
   - Game nối từ với nghĩa
   - 3-5 từ vựng liên quan đến chủ đề
   - User kéo thả từ tiếng Anh match với nghĩa tiếng Việt
   
2. PRONUNCIATION (Lesson 2):
   - Luyện phát âm từng từ và cụm từ
   - User nhấn mic, đọc theo
   - AI đánh giá 3 tiêu chí: phát âm, ngữ điệu, trọng âm
   
3. CONVERSATION (Lesson 3):
   - Hội thoại ngắn với AI về chủ đề
   - AI đóng vai (VD: nhân viên nhà hàng)
   - User thực hành giao tiếp thực tế

Cấu trúc:
- topic_id: Thuộc chủ đề nào
- lesson_type: vocabulary_matching | pronunciation | conversation | mixed
- lesson_order: Thứ tự trong chủ đề (1, 2, 3...)
- passing_score: Điểm tối thiểu để pass (mặc định 70%)
- instructions: Hướng dẫn làm bài

BẢNG PRONUNCIATION_EXERCISES:
==============================
Các bài tập phát âm trong lesson type=pronunciation.
- exercise_type: word (từ đơn) | phrase (cụm từ) | sentence (câu)
- content: Nội dung cần đọc (VD: "restaurant", "I'd like to order")
- phonetic: Phiên âm IPA
- audio_url: Audio mẫu để user nghe trước

BẢNG CONVERSATION_TEMPLATES:
=============================
Template cho AI conversation trong lesson type=conversation.
- ai_role: Vai AI đóng (VD: "Waiter at a restaurant")
- scenario_context: Bối cảnh (VD: "You are ordering food at a restaurant...")
- starter_prompts: Câu gợi ý mở đầu cho user
- min_turns: Số lượt nói tối thiểu (thường 5 turns)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal


# ============= ENUMS AS STRINGS =============

LESSON_TYPES = ["vocabulary_matching", "pronunciation", "conversation", "mixed"]
EXERCISE_TYPES = ["word", "phrase", "sentence"]


# ============= REQUEST SCHEMAS =============

class LessonCreate(BaseModel):
    """Schema tạo bài học mới (Admin)"""
    topic_id: int = Field(..., description="ID chủ đề")
    lesson_type: str = Field(..., description="vocabulary_matching, pronunciation, conversation, mixed")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    lesson_order: int = Field(..., ge=1, description="Thứ tự trong chủ đề")
    instructions: Optional[str] = Field(None, description="Hướng dẫn làm bài")
    difficulty_level: Optional[str] = None
    estimated_minutes: int = Field(default=5, ge=1)
    passing_score: float = Field(default=70.0, ge=0, le=100)


class PronunciationExerciseCreate(BaseModel):
    """Schema tạo bài tập phát âm (Admin)"""
    lesson_id: int
    exercise_type: str = Field(..., description="word, phrase, sentence")
    content: str = Field(..., min_length=1, description="Nội dung cần đọc")
    phonetic: Optional[str] = Field(None, max_length=255)
    audio_url: Optional[str] = Field(None, max_length=500)
    target_pronunciation_score: float = Field(default=70.0, ge=0, le=100)
    display_order: int = Field(default=0, ge=0)


class ConversationTemplateCreate(BaseModel):
    """Schema tạo template hội thoại (Admin)"""
    lesson_id: int
    ai_role: str = Field(..., min_length=1, max_length=100, description="Vai AI đóng")
    scenario_context: str = Field(..., min_length=1, description="Bối cảnh tình huống")
    starter_prompts: Optional[List[str]] = Field(None, description="Câu gợi ý mở đầu")
    suggested_topics: Optional[List[str]] = Field(None, description="Chủ đề gợi ý trong conversation")
    min_turns: int = Field(default=5, ge=1)
    max_duration_minutes: int = Field(default=10, ge=1)


# ============= RESPONSE SCHEMAS =============

class LessonBasicResponse(BaseModel):
    """Schema thông tin cơ bản của bài học (dùng trong danh sách)"""
    id: int
    topic_id: int
    lesson_type: str
    title: str
    description: Optional[str] = None
    lesson_order: int
    difficulty_level: Optional[str] = None
    estimated_minutes: int
    passing_score: float
    is_active: bool
    
    class Config:
        from_attributes = True


class LessonWithProgressResponse(BaseModel):
    """Schema bài học kèm tiến độ của user"""
    id: int
    topic_id: int
    lesson_type: str
    title: str
    description: Optional[str] = None
    lesson_order: int
    instructions: Optional[str] = None
    estimated_minutes: int
    passing_score: float
    
    # User progress
    status: str = "locked"  # locked, available, in_progress, completed
    best_score: Optional[float] = None
    total_attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PronunciationExerciseResponse(BaseModel):
    """Schema bài tập phát âm"""
    id: int
    exercise_type: str  # word, phrase, sentence
    content: str        # Nội dung cần đọc
    phonetic: Optional[str] = None
    audio_url: Optional[str] = None
    target_pronunciation_score: float
    display_order: int
    
    class Config:
        from_attributes = True


class ConversationTemplateResponse(BaseModel):
    """Schema template hội thoại AI"""
    id: int
    ai_role: str
    scenario_context: str
    starter_prompts: Optional[List[str]] = None
    suggested_topics: Optional[List[str]] = None
    min_turns: int
    max_duration_minutes: int
    
    class Config:
        from_attributes = True


# ============= DETAILED LESSON RESPONSES =============

class VocabularyMatchingLessonDetail(BaseModel):
    """
    Chi tiết Lesson loại VOCABULARY_MATCHING
    Trả về danh sách từ vựng để chơi game nối
    """
    id: int
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    lesson_type: str = "vocabulary_matching"
    passing_score: float
    estimated_minutes: int
    
    # Danh sách từ vựng (3-5 từ)
    vocabulary_list: List[Any]  # List[VocabularyForMatchingGame]
    
    class Config:
        from_attributes = True


class PronunciationLessonDetail(BaseModel):
    """
    Chi tiết Lesson loại PRONUNCIATION
    Trả về danh sách bài tập phát âm
    """
    id: int
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    lesson_type: str = "pronunciation"
    passing_score: float
    estimated_minutes: int
    
    # Danh sách bài tập phát âm
    exercises: List[PronunciationExerciseResponse]
    
    class Config:
        from_attributes = True


class ConversationLessonDetail(BaseModel):
    """
    Chi tiết Lesson loại CONVERSATION
    Trả về template hội thoại với AI
    """
    id: int
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    lesson_type: str = "conversation"
    passing_score: float
    estimated_minutes: int
    
    # Template hội thoại
    conversation_template: Optional[ConversationTemplateResponse] = None
    
    class Config:
        from_attributes = True


# ============= TOPIC DETAIL WITH LESSONS =============

class TopicDetailResponse(BaseModel):
    """
    Schema chi tiết chủ đề kèm danh sách bài học
    Dùng khi user click vào 1 chủ đề
    """
    id: int
    title: str
    description: Optional[str] = None
    category: str
    difficulty_level: str
    thumbnail_url: Optional[str] = None
    total_lessons: int
    estimated_duration_minutes: Optional[int] = None
    
    # Danh sách lessons trong topic
    lessons: List[LessonWithProgressResponse]
    
    # User progress cho topic này
    lessons_completed: int = 0
    progress_percent: float = 0.0
    status: str = "not_started"
    
    class Config:
        from_attributes = True
