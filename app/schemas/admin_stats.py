"""
Admin Statistics Schemas - Định nghĩa response models cho Admin Dashboard
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


# ============= OVERVIEW STATISTICS =============

class OverviewStats(BaseModel):
    """Thống kê tổng quan hệ thống"""
    total_users: int
    active_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int
    
    total_lessons_completed: int
    total_study_time_minutes: int
    average_score: Optional[float] = None
    
    total_topics: int
    total_lessons: int
    total_vocabulary: int


class UserDistribution(BaseModel):
    """Phân bố users theo level"""
    beginner: int
    intermediate: int
    advanced: int


class LessonTypeStats(BaseModel):
    """Thống kê theo loại bài học"""
    lesson_type: str
    total_attempts: int
    completed_count: int
    pass_count: int
    average_score: Optional[float] = None
    completion_rate: Optional[float] = None
    pass_rate: Optional[float] = None


# ============= USER STATISTICS =============

class UserStatsItem(BaseModel):
    """Thông tin thống kê cho 1 user"""
    id: int
    email: str
    full_name: Optional[str] = None
    current_level: str
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    
    # Learning stats
    total_lessons_completed: int = 0
    total_study_time_minutes: int = 0
    average_score: Optional[float] = None
    current_streak: int = 0
    longest_streak: int = 0
    last_activity: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserStatsListResponse(BaseModel):
    """Response cho danh sách user stats với pagination"""
    items: List[UserStatsItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserDetailStats(BaseModel):
    """Thống kê chi tiết cho 1 user cụ thể"""
    user: UserStatsItem
    
    # Topic progress
    topics_started: int
    topics_completed: int
    
    # Vocabulary
    total_vocabulary_learned: int
    vocabulary_mastered: int
    vocabulary_familiar: int
    vocabulary_learning: int
    
    # Scores breakdown
    avg_pronunciation_score: Optional[float] = None
    avg_vocabulary_score: Optional[float] = None
    avg_conversation_score: Optional[float] = None
    
    # Recent activity
    recent_attempts: List[dict] = []


# ============= ACTIVITY STATISTICS =============

class DailyActivityItem(BaseModel):
    """Thống kê hoạt động theo ngày"""
    date: date
    active_users: int
    total_sessions: int
    total_minutes: int
    lessons_completed: int
    average_score: Optional[float] = None


class ActivityStatsResponse(BaseModel):
    """Response cho thống kê hoạt động theo thời gian"""
    period: str  # "daily", "weekly", "monthly"
    data: List[DailyActivityItem]
    summary: dict


# ============= LESSON STATISTICS =============

class LessonStatsItem(BaseModel):
    """Thống kê cho 1 bài học"""
    lesson_id: int
    lesson_title: str
    topic_name: str
    lesson_type: str
    
    total_attempts: int
    unique_users: int
    completed_count: int
    pass_count: int
    
    average_score: Optional[float] = None
    completion_rate: Optional[float] = None
    pass_rate: Optional[float] = None
    avg_duration_seconds: Optional[int] = None


class LessonStatsResponse(BaseModel):
    """Response cho danh sách lesson stats"""
    items: List[LessonStatsItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class TopLessonItem(BaseModel):
    """Top lessons (popular hoặc difficult)"""
    lesson_id: int
    lesson_title: str
    topic_name: str
    value: float  # Có thể là số attempts hoặc pass_rate tùy context
    metric: str  # "attempts", "pass_rate", "avg_score"


# ============= LEADERBOARD =============

class LeaderboardItem(BaseModel):
    """Item trong bảng xếp hạng"""
    rank: int
    user_id: int
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    current_level: str
    value: float  # Giá trị để xếp hạng
    metric: str  # "score", "streak", "lessons_completed", "study_time"


class LeaderboardResponse(BaseModel):
    """Response cho leaderboard"""
    metric: str
    period: Optional[str] = None  # "all_time", "this_week", "this_month"
    items: List[LeaderboardItem]


# ============= COMBINED DASHBOARD RESPONSE =============

class AdminDashboardResponse(BaseModel):
    """Response tổng hợp cho Admin Dashboard"""
    overview: OverviewStats
    user_distribution: UserDistribution
    lesson_type_stats: List[LessonTypeStats]
    recent_activity: List[DailyActivityItem]
    top_lessons: List[TopLessonItem]
    top_users: List[LeaderboardItem]
