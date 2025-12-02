"""
Vocabulary schemas - Cấu trúc dữ liệu cho Từ vựng

GIẢI THÍCH BẢNG VOCABULARY:
===========================
Bảng `vocabulary` lưu trữ tất cả từ vựng tiếng Anh trong hệ thống.
Mỗi từ có đầy đủ thông tin: nghĩa, phiên âm, ví dụ, audio.

Ví dụ:
- word: "restaurant"
- phonetic: "/ˈrestərɒnt/"
- definition: "Nhà hàng - nơi phục vụ đồ ăn"
- example_sentence: "Let's go to a restaurant for dinner."
- part_of_speech: "noun"
- difficulty_level: "beginner"

BẢNG LESSON_VOCABULARY (M:M):
==============================
Liên kết giữa Lesson và Vocabulary.
Mỗi lesson có 3-5 từ vựng để học.
- is_key_word: Đánh dấu từ quan trọng cần nhớ
- display_order: Thứ tự hiển thị trong bài học

BẢNG USER_VOCABULARY:
======================
Theo dõi từ vựng user đã gặp và mức độ thuộc.
- times_encountered: Số lần gặp từ này
- times_correct: Số lần trả lời đúng
- mastery_level: learning → familiar → mastered
- is_saved: User đánh dấu yêu thích để ôn tập
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============= REQUEST SCHEMAS =============

class VocabularyCreate(BaseModel):
    """Schema tạo từ vựng mới (Admin)"""
    word: str = Field(..., min_length=1, max_length=100, description="Từ tiếng Anh")
    phonetic: Optional[str] = Field(None, max_length=100, description="Phiên âm IPA")
    definition: str = Field(..., min_length=1, description="Nghĩa tiếng Việt")
    example_sentence: Optional[str] = Field(None, description="Câu ví dụ")
    audio_url: Optional[str] = Field(None, max_length=500, description="URL audio phát âm")
    difficulty_level: Optional[str] = Field(None, description="beginner, intermediate, advanced")
    part_of_speech: Optional[str] = Field(None, description="noun, verb, adjective, adverb, etc.")


class VocabularyUpdate(BaseModel):
    """Schema cập nhật từ vựng (Admin)"""
    word: Optional[str] = Field(None, min_length=1, max_length=100)
    phonetic: Optional[str] = None
    definition: Optional[str] = None
    example_sentence: Optional[str] = None
    audio_url: Optional[str] = None
    difficulty_level: Optional[str] = None
    part_of_speech: Optional[str] = None


# ============= RESPONSE SCHEMAS =============

class VocabularyResponse(BaseModel):
    """Schema trả về thông tin từ vựng"""
    id: int
    word: str
    phonetic: Optional[str] = None
    definition: str
    example_sentence: Optional[str] = None
    audio_url: Optional[str] = None
    difficulty_level: Optional[str] = None
    part_of_speech: Optional[str] = None
    
    class Config:
        from_attributes = True


class VocabularyForMatchingGame(BaseModel):
    """
    Schema từ vựng cho game nối từ với nghĩa
    Chỉ trả về word và definition để user match
    """
    id: int
    word: str
    definition: str
    
    class Config:
        from_attributes = True


class VocabularyWithUserProgress(BaseModel):
    """Schema từ vựng kèm tiến độ học của user"""
    id: int
    word: str
    phonetic: Optional[str] = None
    definition: str
    example_sentence: Optional[str] = None
    audio_url: Optional[str] = None
    part_of_speech: Optional[str] = None
    
    # User progress
    times_encountered: int = 0
    times_correct: int = 0
    mastery_level: str = "new"  # new, learning, familiar, mastered
    is_saved: bool = False
    
    class Config:
        from_attributes = True


# ============= MATCHING GAME SCHEMAS =============

class VocabularyMatchSubmit(BaseModel):
    """Schema submit kết quả nối 1 từ"""
    vocabulary_id: int = Field(..., description="ID của từ vựng")
    user_answer: str = Field(..., description="Nghĩa user chọn")
    time_taken_seconds: Optional[int] = Field(None, ge=0, description="Thời gian trả lời")


class VocabularyMatchingSubmitRequest(BaseModel):
    """Schema submit kết quả toàn bộ game nối từ"""
    lesson_attempt_id: int = Field(..., description="ID của lần làm bài")
    results: List[VocabularyMatchSubmit] = Field(..., min_length=1, description="Danh sách kết quả")


class VocabularyMatchingResultResponse(BaseModel):
    """Schema trả về kết quả game nối từ"""
    vocabulary_id: int
    word: str
    correct_definition: str
    user_answer: str
    is_correct: bool
    time_taken_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


class VocabularyMatchingSummary(BaseModel):
    """Schema tổng kết game nối từ"""
    total_words: int
    correct_count: int
    incorrect_count: int
    accuracy_percent: float  # 0-100
    total_time_seconds: int
    results: List[VocabularyMatchingResultResponse]


# ============= USER VOCABULARY SCHEMAS =============

class UserVocabularySaveRequest(BaseModel):
    """Schema đánh dấu yêu thích từ vựng"""
    vocabulary_id: int
    is_saved: bool = True


class UserVocabularyListResponse(BaseModel):
    """Schema danh sách từ vựng đã lưu của user"""
    items: List[VocabularyWithUserProgress]
    total: int
    page: int
    page_size: int
