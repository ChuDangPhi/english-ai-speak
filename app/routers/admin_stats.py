"""
Admin Statistics Router - API endpoints cho Admin Dashboard
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.services.admin_stats_service import AdminStatsService
from app.schemas.admin_stats import (
    OverviewStats, UserDistribution, LessonTypeStats,
    UserStatsListResponse, UserDetailStats,
    ActivityStatsResponse, LessonStatsResponse,
    LeaderboardResponse, AdminDashboardResponse
)


router = APIRouter(prefix="/admin/stats", tags=["Admin - Statistics"])


# ============= DASHBOARD OVERVIEW =============

@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Lấy tổng hợp thống kê cho Admin Dashboard
    
    Trả về:
    - Overview: Tổng quan users, lessons, study time
    - User distribution: Phân bố theo level
    - Lesson type stats: Thống kê theo loại bài học
    - Recent activity: Hoạt động 7 ngày gần đây
    - Top lessons: Bài học phổ biến nhất
    - Top users: Users điểm cao nhất
    """
    service = AdminStatsService(db)
    
    overview = service.get_overview_stats()
    user_distribution = service.get_user_distribution()
    lesson_type_stats = service.get_lesson_type_stats()
    
    # Recent activity (7 days)
    activity_data = service.get_activity_stats(days=7)
    recent_activity = activity_data["data"]
    
    # Top lessons by attempts
    top_lessons = service.get_top_lessons(metric="attempts", limit=5)
    
    # Top users by score
    top_users = service.get_leaderboard(metric="score", limit=5)
    
    return AdminDashboardResponse(
        overview=overview,
        user_distribution=user_distribution,
        lesson_type_stats=lesson_type_stats,
        recent_activity=recent_activity,
        top_lessons=top_lessons,
        top_users=top_users
    )


@router.get("/overview", response_model=OverviewStats)
def get_overview_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Lấy thống kê tổng quan hệ thống
    
    Trả về:
    - Số lượng users (total, active, new)
    - Số lessons hoàn thành
    - Tổng thời gian học
    - Điểm trung bình
    - Số lượng topics, lessons, vocabulary
    """
    service = AdminStatsService(db)
    return service.get_overview_stats()


@router.get("/user-distribution", response_model=UserDistribution)
def get_user_distribution(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Lấy phân bố users theo level (beginner, intermediate, advanced)"""
    service = AdminStatsService(db)
    return service.get_user_distribution()


# ============= USER STATISTICS =============

@router.get("/users", response_model=UserStatsListResponse)
def get_user_stats_list(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số items/trang"),
    search: Optional[str] = Query(None, description="Tìm theo email hoặc tên"),
    level: Optional[str] = Query(None, description="Filter theo level"),
    is_active: Optional[bool] = Query(None, description="Filter theo trạng thái"),
    sort_by: str = Query("created_at", description="Sort theo field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Thứ tự sort"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Lấy danh sách users với thống kê học tập
    
    Hỗ trợ:
    - Pagination
    - Search theo email/tên
    - Filter theo level, is_active
    - Sort theo các fields
    """
    service = AdminStatsService(db)
    result = service.get_user_stats_list(
        page=page,
        page_size=page_size,
        search=search,
        level=level,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return UserStatsListResponse(**result)


@router.get("/users/{user_id}", response_model=UserDetailStats)
def get_user_detail_stats(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Lấy thống kê chi tiết cho 1 user
    
    Trả về:
    - Thông tin user cơ bản
    - Progress theo topics
    - Vocabulary stats (learning/familiar/mastered)
    - Điểm theo loại bài học
    - 10 attempts gần nhất
    """
    service = AdminStatsService(db)
    result = service.get_user_detail_stats(user_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User không tồn tại"
        )
    
    return result


# ============= ACTIVITY STATISTICS =============

@router.get("/activity", response_model=ActivityStatsResponse)
def get_activity_stats(
    days: int = Query(30, ge=1, le=365, description="Số ngày lấy thống kê"),
    start_date: Optional[date] = Query(None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Ngày kết thúc (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Lấy thống kê hoạt động theo thời gian
    
    Trả về data theo ngày:
    - Số users active
    - Số sessions
    - Tổng thời gian học (phút)
    - Số lessons hoàn thành
    - Điểm trung bình
    """
    service = AdminStatsService(db)
    result = service.get_activity_stats(
        days=days,
        start_date=start_date,
        end_date=end_date
    )
    return ActivityStatsResponse(**result)


# ============= LESSON STATISTICS =============

@router.get("/lessons", response_model=LessonStatsResponse)
def get_lesson_stats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lesson_type: Optional[str] = Query(None, description="Filter theo loại (vocabulary_matching, pronunciation, conversation)"),
    topic_id: Optional[int] = Query(None, description="Filter theo topic"),
    sort_by: str = Query("total_attempts", description="Sort theo field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Lấy thống kê cho từng bài học
    
    Trả về:
    - Số attempts
    - Số users unique
    - Completion rate
    - Pass rate
    - Điểm trung bình
    - Thời gian làm bài trung bình
    """
    service = AdminStatsService(db)
    result = service.get_lesson_stats(
        page=page,
        page_size=page_size,
        lesson_type=lesson_type,
        topic_id=topic_id,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return LessonStatsResponse(**result)


@router.get("/lessons/top")
def get_top_lessons(
    metric: str = Query("attempts", regex="^(attempts|avg_score)$", description="Metric để xếp hạng"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Lấy top lessons theo metric
    
    Metrics:
    - attempts: Bài học được làm nhiều nhất
    - avg_score: Bài học có điểm trung bình cao nhất
    """
    service = AdminStatsService(db)
    return service.get_top_lessons(metric=metric, limit=limit)


# ============= LEADERBOARD =============

@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    metric: str = Query("score", regex="^(score|lessons_completed|streak|study_time)$", description="Metric xếp hạng"),
    limit: int = Query(10, ge=1, le=100),
    period: Optional[str] = Query(None, regex="^(this_week|this_month)$", description="Khoảng thời gian"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Lấy bảng xếp hạng users
    
    Metrics:
    - score: Điểm trung bình cao nhất
    - lessons_completed: Số bài học hoàn thành
    - streak: Streak học liên tục
    - study_time: Tổng thời gian học
    
    Period:
    - this_week: 7 ngày gần đây
    - this_month: 30 ngày gần đây
    - None: All time
    """
    service = AdminStatsService(db)
    items = service.get_leaderboard(
        metric=metric,
        limit=limit,
        period=period
    )
    
    return LeaderboardResponse(
        metric=metric,
        period=period or "all_time",
        items=items
    )


# ============= LESSON TYPE STATISTICS =============

@router.get("/lesson-types")
def get_lesson_type_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Lấy thống kê theo loại bài học
    
    Trả về cho mỗi loại (vocabulary_matching, pronunciation, conversation):
    - Số attempts
    - Completion rate
    - Pass rate
    - Điểm trung bình
    """
    service = AdminStatsService(db)
    return service.get_lesson_type_stats()
