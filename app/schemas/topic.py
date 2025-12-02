"""
Topic schemas - Cấu trúc dữ liệu cho Chủ đề học tập

GIẢI THÍCH BẢNG TOPICS:
========================
Bảng `topics` lưu trữ các chủ đề học tiếng Anh thường gặp.
Mỗi chủ đề có nhiều bài học (lessons) bên trong.

Ví dụ các chủ đề:
- "At the Restaurant" (Tại nhà hàng) - beginner
- "Job Interview" (Phỏng vấn xin việc) - intermediate  
- "Business Meeting" (Họp công việc) - advanced

Cấu trúc:
- title: Tên chủ đề (VD: "Ordering Food")
- description: Mô tả chi tiết về chủ đề
- category: Phân loại (general, business, travel, daily_life, academic)
- difficulty_level: Độ khó (beginner, intermediate, advanced)
- thumbnail_url: Ảnh đại diện của chủ đề
- total_lessons: Tổng số bài học trong chủ đề
- display_order: Thứ tự hiển thị trên UI
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============= REQUEST SCHEMAS =============

class TopicCreate(BaseModel):
    """Schema tạo chủ đề mới (Admin)"""
    title: str = Field(..., min_length=1, max_length=255, description="Tên chủ đề")
    description: Optional[str] = Field(None, description="Mô tả chi tiết")
    category: str = Field(default="general", description="Phân loại: general, business, travel, daily_life, academic")
    difficulty_level: str = Field(..., description="Độ khó: beginner, intermediate, advanced")
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="URL ảnh thumbnail")
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, description="Thời gian ước tính (phút)")
    display_order: int = Field(default=0, ge=0, description="Thứ tự hiển thị")


class TopicUpdate(BaseModel):
    """Schema cập nhật chủ đề (Admin)"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = None
    thumbnail_url: Optional[str] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


# ============= RESPONSE SCHEMAS =============

class TopicBasicResponse(BaseModel):
    """Schema trả về thông tin cơ bản của chủ đề (dùng trong danh sách)"""
    id: int
    title: str
    description: Optional[str] = None
    category: str
    difficulty_level: str
    thumbnail_url: Optional[str] = None
    total_lessons: int
    estimated_duration_minutes: Optional[int] = None
    display_order: int
    is_active: bool
    
    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    """Schema trả về danh sách chủ đề với phân trang"""
    items: List[TopicBasicResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TopicWithProgressResponse(BaseModel):
    """
    Schema trả về chủ đề kèm tiến độ học của user
    Dùng khi user đã đăng nhập và xem danh sách topics
    """
    id: int
    title: str
    description: Optional[str] = None
    category: str
    difficulty_level: str
    thumbnail_url: Optional[str] = None
    total_lessons: int
    estimated_duration_minutes: Optional[int] = None
    
    # Tiến độ của user
    lessons_completed: int = 0
    progress_percent: float = 0.0  # 0-100
    status: str = "not_started"  # not_started, in_progress, completed
    best_score: Optional[float] = None
    last_practiced_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============= FILTER/QUERY SCHEMAS =============

class TopicFilter(BaseModel):
    """Schema filter để tìm kiếm chủ đề"""
    category: Optional[str] = Field(None, description="Filter theo category")
    difficulty_level: Optional[str] = Field(None, description="Filter theo độ khó")
    search: Optional[str] = Field(None, description="Tìm kiếm theo title")
    is_active: Optional[bool] = Field(default=True, description="Chỉ lấy active topics")
