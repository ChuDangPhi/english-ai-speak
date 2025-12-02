"""
Attempt schemas - Cấu trúc dữ liệu cho Lần làm bài

GIẢI THÍCH BẢNG LESSON_ATTEMPTS:
=================================
Bảng trung tâm lưu trữ MỖI LẦN user làm bài.
Liên kết với user_id và lesson_id.

Mỗi khi user bắt đầu 1 lesson:
1. Tạo record lesson_attempts mới
2. Lưu started_at = now()
3. Khi hoàn thành: cập nhật completed_at, scores

FIELDS THEO LOẠI LESSON:
-------------------------

1. VOCABULARY_MATCHING:
   - vocabulary_correct: Số từ đúng
   - vocabulary_total: Tổng số từ
   - overall_score = (correct / total) * 100

2. PRONUNCIATION:
   - pronunciation_score: Điểm phát âm trung bình
   - intonation_score: Điểm ngữ điệu trung bình
   - stress_score: Điểm trọng âm trung bình
   - overall_score = average của 3 điểm

3. CONVERSATION:
   - conversation_turns: Số lượt nói
   - fluency_score: Điểm lưu loát
   - grammar_score: Điểm ngữ pháp
   - overall_score = weighted average

COMMON FIELDS:
---------------
- attempt_number: Lần thử thứ mấy (1, 2, 3...)
- duration_seconds: Thời gian làm bài (giây)
- ai_feedback: Nhận xét tổng hợp từ AI
- is_passed: Đạt hay chưa (so với passing_score)
- is_completed: Đã hoàn thành chưa
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ============= REQUEST SCHEMAS =============

class LessonAttemptCreate(BaseModel):
    """Schema bắt đầu làm bài mới"""
    lesson_id: int = Field(..., description="ID bài học")


class LessonAttemptComplete(BaseModel):
    """Schema hoàn thành bài học"""
    lesson_attempt_id: int = Field(..., description="ID lần làm bài")
    
    # Scores (optional - có thể đã được cập nhật trong quá trình làm)
    overall_score: Optional[float] = Field(None, ge=0, le=100)
    
    # Vocabulary matching
    vocabulary_correct: Optional[int] = Field(None, ge=0)
    vocabulary_total: Optional[int] = Field(None, ge=0)
    
    # Pronunciation
    pronunciation_score: Optional[float] = Field(None, ge=0, le=100)
    intonation_score: Optional[float] = Field(None, ge=0, le=100)
    stress_score: Optional[float] = Field(None, ge=0, le=100)
    
    # Conversation
    conversation_turns: Optional[int] = Field(None, ge=0)
    fluency_score: Optional[float] = Field(None, ge=0, le=100)
    grammar_score: Optional[float] = Field(None, ge=0, le=100)


# ============= RESPONSE SCHEMAS =============

class LessonAttemptResponse(BaseModel):
    """Schema trả về thông tin lần làm bài"""
    id: int
    user_id: int
    lesson_id: int
    attempt_number: int
    
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    # Scores
    overall_score: Optional[float] = None
    vocabulary_correct: int = 0
    vocabulary_total: int = 0
    pronunciation_score: Optional[float] = None
    intonation_score: Optional[float] = None
    stress_score: Optional[float] = None
    conversation_turns: int = 0
    fluency_score: Optional[float] = None
    grammar_score: Optional[float] = None
    
    ai_feedback: Optional[str] = None
    is_passed: bool = False
    is_completed: bool = False
    
    class Config:
        from_attributes = True


class LessonAttemptStartResponse(BaseModel):
    """Schema trả về khi bắt đầu làm bài"""
    attempt_id: int
    lesson_id: int
    lesson_type: str
    lesson_title: str
    attempt_number: int
    started_at: datetime
    
    # Thông tin lesson
    instructions: Optional[str] = None
    passing_score: float
    estimated_minutes: int


class LessonAttemptSummary(BaseModel):
    """Schema tổng kết sau khi hoàn thành bài học"""
    attempt_id: int
    lesson_id: int
    lesson_type: str
    lesson_title: str
    attempt_number: int
    
    # Thời gian
    started_at: datetime
    completed_at: datetime
    duration_seconds: int
    duration_formatted: str  # "5 phút 30 giây"
    
    # Điểm số
    overall_score: float
    passing_score: float
    is_passed: bool
    
    # Chi tiết điểm theo loại lesson
    score_breakdown: dict  # Tuỳ loại lesson
    
    # Feedback
    ai_feedback: str
    
    # So sánh với lần trước
    previous_best_score: Optional[float] = None
    is_new_best: bool = False
    improvement: Optional[float] = None  # % cải thiện


# ============= HISTORY SCHEMAS =============

class LessonAttemptHistoryItem(BaseModel):
    """Schema 1 item trong lịch sử làm bài"""
    id: int
    lesson_id: int
    lesson_title: str
    lesson_type: str
    attempt_number: int
    overall_score: Optional[float] = None
    is_passed: bool
    is_completed: bool
    duration_seconds: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LessonAttemptHistoryResponse(BaseModel):
    """Schema danh sách lịch sử làm bài"""
    items: List[LessonAttemptHistoryItem]
    total: int
    page: int
    page_size: int


# ============= STATISTICS SCHEMAS =============

class UserLessonStats(BaseModel):
    """Thống kê của user cho 1 lesson cụ thể"""
    lesson_id: int
    lesson_title: str
    lesson_type: str
    
    total_attempts: int
    best_score: Optional[float] = None
    average_score: Optional[float] = None
    last_attempt_at: Optional[datetime] = None
    first_passed_at: Optional[datetime] = None
    
    # Trend (so sánh 5 lần gần nhất)
    recent_scores: List[float] = []
    trend: str = "stable"  # improving, declining, stable
