"""
Pronunciation schemas - Cấu trúc dữ liệu cho Phát âm

GIẢI THÍCH BẢNG PRONUNCIATION_ATTEMPTS:
========================================
Bảng lưu kết quả đánh giá phát âm của user.
Mỗi lần user đọc 1 bài tập phát âm sẽ tạo 1 record.

3 TIÊU CHÍ ĐÁNH GIÁ CHÍNH:
---------------------------
1. PRONUNCIATION_SCORE (Phát âm): 0-100
   - Đánh giá độ chính xác phát âm từng âm tiết
   - So sánh với audio chuẩn
   - VD: "restaurant" → /ˈrestərɒnt/
   
2. INTONATION_SCORE (Ngữ điệu): 0-100
   - Đánh giá âm điệu lên xuống của giọng
   - Quan trọng với câu hỏi, câu cảm thán
   - VD: Câu hỏi phải lên giọng cuối câu
   
3. STRESS_SCORE (Trọng âm): 0-100
   - Đánh giá nhấn âm đúng vị trí
   - VD: resTAUrant (nhấn âm 2)
   - Sai trọng âm có thể gây hiểu nhầm

FLOW XỬ LÝ:
-----------
1. User nhấn mic, đọc nội dung hiển thị
2. Frontend ghi audio, gửi lên server
3. Server gọi Deepgram API để:
   - Speech-to-text (transcription)
   - Lấy điểm pronunciation
4. Server tính toán điểm 3 tiêu chí
5. Trả về kết quả + feedback chi tiết
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============= REQUEST SCHEMAS =============

class PronunciationSubmitRequest(BaseModel):
    """
    Schema submit bài tập phát âm
    Frontend gửi audio_url sau khi upload lên storage
    """
    lesson_attempt_id: int = Field(..., description="ID lần làm bài")
    exercise_id: int = Field(..., description="ID bài tập phát âm")
    audio_url: str = Field(..., description="URL audio user đã ghi")
    

class PronunciationSubmitBase64Request(BaseModel):
    """
    Schema submit audio dạng base64
    Dùng khi frontend gửi trực tiếp audio data
    """
    lesson_attempt_id: int = Field(..., description="ID lần làm bài")
    exercise_id: int = Field(..., description="ID bài tập phát âm")
    audio_base64: str = Field(..., description="Audio data encoded base64")
    audio_format: str = Field(default="webm", description="Format: webm, wav, mp3")


# ============= RESPONSE SCHEMAS =============

class PronunciationScoreDetail(BaseModel):
    """Chi tiết điểm 3 tiêu chí"""
    pronunciation_score: float = Field(..., ge=0, le=100, description="Điểm phát âm")
    intonation_score: float = Field(..., ge=0, le=100, description="Điểm ngữ điệu")
    stress_score: float = Field(..., ge=0, le=100, description="Điểm trọng âm")
    accuracy_score: float = Field(..., ge=0, le=100, description="Điểm tổng hợp")


class PronunciationFeedback(BaseModel):
    """Feedback chi tiết cho từng phần"""
    overall: str = Field(..., description="Nhận xét tổng quan")
    pronunciation_feedback: str = Field(..., description="Nhận xét phát âm")
    intonation_feedback: str = Field(..., description="Nhận xét ngữ điệu")
    stress_feedback: str = Field(..., description="Nhận xét trọng âm")
    suggestions: List[str] = Field(default=[], description="Gợi ý cải thiện")


class WordAnalysis(BaseModel):
    """Phân tích chi tiết từng từ (nếu có)"""
    word: str
    is_correct: bool
    expected_phonetic: Optional[str] = None
    user_phonetic: Optional[str] = None
    feedback: Optional[str] = None


class PronunciationAttemptResponse(BaseModel):
    """Schema trả về kết quả đánh giá phát âm"""
    id: int
    exercise_id: int
    attempt_number: int
    
    # Nội dung đã đọc
    expected_content: str  # Nội dung cần đọc
    transcription: Optional[str] = None  # Kết quả speech-to-text
    
    # Điểm số
    scores: PronunciationScoreDetail
    
    # Feedback
    feedback: PronunciationFeedback
    
    # Phân tích chi tiết (optional)
    word_analysis: Optional[List[WordAnalysis]] = None
    
    # Đạt hay chưa
    is_passed: bool
    target_score: float
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class PronunciationLessonSummary(BaseModel):
    """Tổng kết toàn bộ lesson phát âm"""
    lesson_id: int
    lesson_title: str
    total_exercises: int
    completed_exercises: int
    
    # Điểm trung bình
    average_pronunciation: float
    average_intonation: float
    average_stress: float
    overall_score: float
    
    # Kết quả từng bài tập
    exercise_results: List[PronunciationAttemptResponse]
    
    # Đạt hay chưa
    is_passed: bool
    passing_score: float
    
    # Feedback tổng hợp từ AI
    ai_summary_feedback: Optional[str] = None


# ============= REALTIME FEEDBACK (Optional - WebSocket) =============

class RealtimePronunciationFeedback(BaseModel):
    """
    Schema cho feedback realtime qua WebSocket
    Gửi feedback ngay khi user đang nói
    """
    status: str  # listening, processing, completed, error
    partial_transcription: Optional[str] = None
    confidence: Optional[float] = None
    message: Optional[str] = None
