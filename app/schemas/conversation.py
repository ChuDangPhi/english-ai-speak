"""
Conversation schemas - Cấu trúc dữ liệu cho Hội thoại AI

GIẢI THÍCH BẢNG CONVERSATION_TEMPLATES:
========================================
Template định nghĩa tình huống hội thoại với AI.
Mỗi lesson type=conversation có 1 template.

Ví dụ Template "At the Restaurant":
- ai_role: "Friendly waiter at an Italian restaurant"
- scenario_context: "You are a customer at a restaurant. 
  The waiter will take your order. Practice ordering food,
  asking about menu items, and making requests."
- starter_prompts: [
    "Hi! I'd like to see the menu please.",
    "What do you recommend?",
    "I'm ready to order."
  ]
- min_turns: 5 (ít nhất 5 lượt nói)

BẢNG CONVERSATION_MESSAGES:
============================
Lưu lịch sử hội thoại giữa user và AI.
- speaker: "user" hoặc "ai"
- message_text: Nội dung tin nhắn
- audio_url: Audio nếu user nói (speech-to-text)
- grammar_errors: Lỗi ngữ pháp AI phát hiện (JSON)
- vocabulary_used: Từ vựng user đã dùng (JSON)
- sentiment: positive, negative, neutral

FLOW HỘI THOẠI:
---------------
1. User bắt đầu lesson conversation
2. AI gửi tin nhắn mở đầu theo scenario
3. User reply (gõ text hoặc nói)
4. Nếu user nói:
   - Deepgram chuyển speech → text
   - AI đánh giá grammar, vocabulary
5. AI reply tiếp tục conversation
6. Lặp lại đến khi đủ min_turns
7. AI đưa ra feedback tổng kết
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============= MESSAGE SCHEMAS =============

class ConversationMessageCreate(BaseModel):
    """Schema gửi tin nhắn mới (từ user)"""
    lesson_attempt_id: int = Field(..., description="ID lần làm bài")
    message_text: str = Field(..., min_length=1, description="Nội dung tin nhắn")
    audio_url: Optional[str] = Field(None, description="URL audio nếu user nói")


class ConversationMessageWithAudio(BaseModel):
    """Schema gửi tin nhắn bằng audio (speech-to-text)"""
    lesson_attempt_id: int = Field(..., description="ID lần làm bài")
    audio_base64: str = Field(..., description="Audio data encoded base64")
    audio_format: str = Field(default="webm", description="Format: webm, wav, mp3")


class GrammarError(BaseModel):
    """Chi tiết lỗi ngữ pháp"""
    original: str = Field(..., description="Câu gốc user nói")
    corrected: str = Field(..., description="Câu đã sửa")
    error_type: str = Field(..., description="Loại lỗi: tense, article, preposition, etc.")
    explanation: str = Field(..., description="Giải thích lỗi")


class ConversationMessageResponse(BaseModel):
    """Schema trả về tin nhắn"""
    id: int
    message_order: int
    speaker: str  # "user" hoặc "ai"
    message_text: str
    audio_url: Optional[str] = None
    
    # Phân tích (chỉ có với tin nhắn của user)
    grammar_errors: Optional[List[GrammarError]] = None
    vocabulary_used: Optional[List[str]] = None
    sentiment: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= AI RESPONSE SCHEMAS =============

class AIConversationResponse(BaseModel):
    """Schema response từ AI sau khi user gửi tin nhắn"""
    # Tin nhắn AI reply
    ai_message: ConversationMessageResponse
    
    # Phân tích tin nhắn user vừa gửi
    user_message_analysis: Optional[Dict[str, Any]] = None
    
    # User transcription (for voice messages)
    user_transcription: Optional[str] = None
    user_audio_url: Optional[str] = None
    
    # Gợi ý reply tiếp theo cho user
    suggested_replies: Optional[List[str]] = None
    
    # Trạng thái conversation
    current_turn: int
    min_turns: int
    can_end: bool  # True nếu đã đủ min_turns


# ============= CONVERSATION SESSION SCHEMAS =============

class ConversationStartRequest(BaseModel):
    """Schema bắt đầu conversation mới"""
    lesson_id: int = Field(..., description="ID bài học conversation")  


class ConversationStartResponse(BaseModel):
    """Schema trả về khi bắt đầu conversation"""
    lesson_attempt_id: int
    lesson_id: int
    lesson_title: str
    
    # Template info
    ai_role: str
    scenario_context: str
    starter_prompts: Optional[List[str]] = None
    suggested_topics: Optional[List[str]] = None
    min_turns: int
    max_duration_minutes: int
    
    # Tin nhắn mở đầu từ AI
    opening_message: ConversationMessageResponse


class ConversationEndRequest(BaseModel):
    """Schema kết thúc conversation"""
    lesson_attempt_id: int = Field(..., description="ID lần làm bài")


# ============= CONVERSATION SUMMARY SCHEMAS =============

class ConversationSummary(BaseModel):
    """Tổng kết hội thoại sau khi kết thúc"""
    lesson_attempt_id: int
    lesson_id: int
    lesson_title: str
    
    # Thống kê
    total_turns: int
    duration_seconds: int
    total_user_messages: int
    total_ai_messages: int
    
    # Điểm số
    fluency_score: float = Field(..., ge=0, le=100, description="Điểm lưu loát")
    grammar_score: float = Field(..., ge=0, le=100, description="Điểm ngữ pháp")
    vocabulary_score: float = Field(..., ge=0, le=100, description="Điểm từ vựng")
    overall_score: float = Field(..., ge=0, le=100, description="Điểm tổng")
    
    # Phân tích
    grammar_errors_summary: List[GrammarError]
    vocabulary_used: List[str]
    new_vocabulary_learned: List[str]
    
    # Feedback từ AI
    strengths: List[str] = Field(default=[], description="Điểm mạnh")
    areas_to_improve: List[str] = Field(default=[], description="Cần cải thiện")
    ai_feedback: str = Field(..., description="Nhận xét tổng quan từ AI")
    
    # Đạt hay chưa
    is_passed: bool
    passing_score: float
    
    # Lịch sử conversation
    messages: List[ConversationMessageResponse]


# ============= CONVERSATION HISTORY =============

class ConversationHistoryResponse(BaseModel):
    """Schema lịch sử hội thoại (để xem lại)"""
    lesson_attempt_id: int
    lesson_title: str
    ai_role: str
    scenario_context: str
    
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    overall_score: Optional[float] = None
    is_passed: bool = False
    
    messages: List[ConversationMessageResponse]
