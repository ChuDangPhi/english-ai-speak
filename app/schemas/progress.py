"""
Progress schemas - Cấu trúc dữ liệu cho Tiến độ học tập

GIẢI THÍCH BẢNG USER_LESSON_PROGRESS:
======================================
Theo dõi tiến độ user cho TỪNG BÀI HỌC.

STATUS FLOW:
- locked → available → in_progress → completed

Ví dụ: Topic "Restaurant" có 3 lessons
- Lesson 1 (Vocabulary): available (mặc định mở)
- Lesson 2 (Pronunciation): locked
- Lesson 3 (Conversation): locked

Khi user hoàn thành Lesson 1 với điểm >= passing_score:
- Lesson 1: completed
- Lesson 2: available (mở khóa)
- Lesson 3: vẫn locked

GIẢI THÍCH BẢNG USER_PROGRESS:
===============================
Theo dõi tiến độ user cho TỪNG CHỦ ĐỀ.

- lessons_completed: Số bài đã hoàn thành
- total_lessons: Tổng số bài trong topic
- progress = (completed / total) * 100

Status:
- not_started: Chưa học bài nào
- in_progress: Đang học (1+ bài completed)
- completed: Hoàn thành tất cả

GIẢI THÍCH BẢNG DAILY_STATS:
=============================
Thống kê học tập THEO NGÀY.
Dùng để hiển thị biểu đồ, streak, thành tích.

- practice_date: Ngày học
- total_sessions: Số phiên học trong ngày
- total_minutes: Tổng thời gian học (phút)
- lessons_completed: Số bài hoàn thành
- average_score: Điểm trung bình trong ngày

GIẢI THÍCH BẢNG USER_STREAKS:
==============================
Theo dõi CHUỖI NGÀY học liên tục (streak).

- current_streak: Streak hiện tại (VD: 7 ngày)
- longest_streak: Streak dài nhất từ trước đến giờ
- last_activity_date: Ngày học gần nhất

Logic cập nhật:
- Nếu học ngày hôm nay: current_streak += 1
- Nếu bỏ 1 ngày: current_streak = 0
- longest_streak = max(current, longest)
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# ============= USER LESSON PROGRESS =============

class UserLessonProgressResponse(BaseModel):
    """Tiến độ 1 bài học của user"""
    id: int
    user_id: int
    lesson_id: int
    status: str  # locked, available, in_progress, completed
    best_score: Optional[float] = None
    total_attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    first_completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLessonProgressUpdate(BaseModel):
    """Schema cập nhật tiến độ bài học"""
    status: Optional[str] = Field(None, description="locked, available, in_progress, completed")
    best_score: Optional[float] = Field(None, ge=0, le=100)


# ============= USER TOPIC PROGRESS =============

class UserTopicProgressResponse(BaseModel):
    """Tiến độ 1 chủ đề của user"""
    id: int
    user_id: int
    topic_id: int
    topic_title: str
    status: str  # not_started, in_progress, completed
    lessons_completed: int
    total_lessons: int
    progress_percent: float  # 0-100
    times_practiced: int
    best_score: Optional[float] = None
    last_practiced_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============= DAILY STATS =============

class DailyStatsResponse(BaseModel):
    """Thống kê học tập 1 ngày"""
    date: date
    lessons_completed: int = 0
    vocabulary_reviewed: int = 0
    minutes_studied: int = 0
    experience_points_earned: int = 0
    pronunciation_exercises: int = 0
    conversation_turns: int = 0
    
    class Config:
        from_attributes = True


class WeeklyStatsResponse(BaseModel):
    """Thống kê học tập 1 tuần"""
    week_start: date
    week_end: date
    lessons_completed: int = 0
    vocabulary_reviewed: int = 0
    minutes_studied: int = 0
    experience_points_earned: int = 0
    lessons_change_from_last_week: int = 0
    minutes_change_from_last_week: int = 0


class MonthlyStatsResponse(BaseModel):
    """Thống kê học tập 1 tháng"""
    year: int
    month: int
    daily_stats: List[DailyStatsResponse]
    
    # Tổng hợp tháng
    total_days_practiced: int
    total_minutes: int
    total_lessons: int
    average_score: Optional[float] = None
    
    # So sánh với tháng trước
    minutes_change_percent: Optional[float] = None
    lessons_change_percent: Optional[float] = None


# ============= USER STREAKS =============

class UserStreakResponse(BaseModel):
    """Thông tin streak của user"""
    current_streak: int = 0
    longest_streak: int = 0
    learned_today: bool = False
    last_activity_date: Optional[date] = None
    streak_freezes_available: int = 0
    needs_activity_today: bool = True
    
    class Config:
        from_attributes = True


# ============= OVERALL PROGRESS =============

class UserOverallProgress(BaseModel):
    """Tổng quan tiến độ học tập của user"""
    user_id: int
    username: str
    current_level: int = 1
    total_experience_points: int = 0
    xp_to_next_level: int = 100
    
    # Lessons progress
    total_lessons_completed: int = 0
    total_lessons: int = 0
    
    # Topics progress
    total_topics_completed: int = 0
    total_topics: int = 0
    
    # Vocabulary
    total_vocabulary_learned: int = 0
    total_vocabulary_mastered: int = 0
    total_vocabulary: int = 0
    
    # Overall
    overall_completion_percentage: float = 0.0
    average_score: float = 0.0
    total_study_minutes: int = 0


# ============= PROGRESS BY TOPIC =============

class ProgressSummaryByTopic(BaseModel):
    """Tiến độ tóm tắt theo chủ đề"""
    topic_id: int
    topic_name: str
    topic_icon: Optional[str] = None
    total_lessons: int = 0
    completed_lessons: int = 0
    completion_percentage: float = 0.0
    average_score: Optional[float] = None


# ============= USER VOCABULARY =============

class UserVocabularyResponse(BaseModel):
    """Từ vựng đã học của user"""
    vocabulary_id: int
    word: str
    meaning: str
    pronunciation_ipa: Optional[str] = None
    example_sentence: Optional[str] = None
    times_practiced: int = 0
    correct_count: int = 0
    is_mastered: bool = False
    last_reviewed: Optional[datetime] = None
    mastery_percentage: float = 0.0
    
    class Config:
        from_attributes = True


# ============= LESSON PROGRESS =============

class LessonProgressResponse(BaseModel):
    """Tiến độ từng bài học"""
    lesson_id: int
    lesson_title: str
    lesson_type: str
    status: str  # locked, available, in_progress, completed
    best_score: Optional[float] = None
    attempt_count: int = 0
    is_passed: bool = False
    last_attempted: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============= LEADERBOARD =============

class LeaderboardEntry(BaseModel):
    """1 entry trong bảng xếp hạng"""
    rank: int
    user_id: int
    user_name: str
    avatar_url: Optional[str] = None
    
    # Metric (tuỳ loại leaderboard)
    score: float
    metric_label: str  # "Điểm", "Phút học", "Streak"


class LeaderboardResponse(BaseModel):
    """Bảng xếp hạng"""
    type: str  # "weekly_score", "monthly_minutes", "longest_streak"
    title: str
    entries: List[LeaderboardEntry]
    
    # Vị trí của user hiện tại
    current_user_rank: Optional[int] = None
    current_user_entry: Optional[LeaderboardEntry] = None


# ============= ACHIEVEMENTS =============

class Achievement(BaseModel):
    """Thành tích"""
    id: str
    title: str
    description: str
    icon_url: str
    
    # Progress
    is_unlocked: bool
    unlocked_at: Optional[datetime] = None
    progress: float = 0  # 0-100
    progress_text: str  # "3/5 lessons"


class UserAchievementsResponse(BaseModel):
    """Danh sách thành tích của user"""
    total_achievements: int
    unlocked_count: int
    achievements: List[Achievement]
