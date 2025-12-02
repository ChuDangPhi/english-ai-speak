"""
Progress Router - API endpoints cho Tiến độ học tập và Streak

=== GIẢI QUYẾT VẤN ĐỀ GÌ? ===
1. Hiển thị tiến độ tổng quan (dashboard)
2. Quản lý streak (chuỗi ngày học liên tiếp)
3. Thống kê chi tiết theo ngày/tuần/tháng
4. Xem lại lịch sử học từ vựng

=== LOGIC HOẠT ĐỘNG ===
- Streak được reset nếu 1 ngày không học
- Điểm kinh nghiệm (XP) tính từ các lesson completed
- Level up khi đủ XP threshold
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta, date
from typing import List, Optional

from app.database import get_db
from app.models import (
    UserProgress, UserLessonProgress, UserVocabulary, UserStreak,
    DailyStats, LessonAttempt, Lesson, Topic, Vocabulary, LessonStatus
)
from app.models.user import User
from app.schemas.progress import (
    UserOverallProgress, UserStreakResponse, DailyStatsResponse,
    UserVocabularyResponse, LessonProgressResponse,
    ProgressSummaryByTopic, WeeklyStatsResponse, MonthlyStatsResponse
)
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/progress",
    tags=["Progress"]
)


# ============================================================
# GET /progress/overview - Tổng quan tiến độ
# ============================================================
@router.get("/overview", response_model=UserOverallProgress)
def get_progress_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 LẤY TỔNG QUAN TIẾN ĐỘ HỌC TẬP
    
    Logic:
    1. Lấy hoặc tạo UserProgress record
    2. Đếm lessons completed, topics completed
    3. Đếm vocabulary learned, vocab mastered
    4. Tính phần trăm hoàn thành overall
    
    Use case:
    - Hiển thị dashboard "Tiến độ của tôi"
    - Widget tiến độ trên trang chủ
    
    Returns:
    - total_lessons_completed: 15
    - total_vocabulary_learned: 120
    - current_level: 5
    - total_experience_points: 2500
    """
    # Get or create user progress
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            total_experience_points=0,
            current_level=1
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    # Count completed lessons
    lessons_completed = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == current_user.id,
        UserLessonProgress.status == LessonStatus.COMPLETED
    ).count()
    
    # Count total lessons
    total_lessons = db.query(Lesson).filter(Lesson.is_active == True).count()
    
    # Count completed topics (all lessons in topic completed)
    topics_completed = get_completed_topics_count(db, current_user.id)
    total_topics = db.query(Topic).filter(Topic.is_active == True).count()
    
    # Count vocabulary
    vocab_stats = db.query(
        func.count(UserVocabulary.id).label('total'),
        func.sum(func.cast(UserVocabulary.is_mastered, int)).label('mastered')
    ).filter(UserVocabulary.user_id == current_user.id).first()
    
    vocab_learned = vocab_stats.total or 0
    vocab_mastered = vocab_stats.mastered or 0
    
    # Total vocabulary in system
    total_vocab = db.query(Vocabulary).filter(Vocabulary.is_active == True).count()
    
    # Calculate overall percentage
    if total_lessons > 0:
        overall_percentage = round((lessons_completed / total_lessons) * 100, 1)
    else:
        overall_percentage = 0
    
    # Get average score
    avg_score_result = db.query(func.avg(LessonAttempt.overall_score)).filter(
        LessonAttempt.user_id == current_user.id,
        LessonAttempt.is_passed == True
    ).scalar()
    avg_score = round(float(avg_score_result), 1) if avg_score_result else 0
    
    # Total study time
    total_time_result = db.query(func.sum(LessonAttempt.duration_seconds)).filter(
        LessonAttempt.user_id == current_user.id
    ).scalar()
    total_study_minutes = (total_time_result or 0) // 60
    
    return UserOverallProgress(
        user_id=current_user.id,
        username=current_user.username,
        current_level=progress.current_level,
        total_experience_points=progress.total_experience_points,
        xp_to_next_level=calculate_xp_to_next_level(progress.current_level, progress.total_experience_points),
        total_lessons_completed=lessons_completed,
        total_lessons=total_lessons,
        total_topics_completed=topics_completed,
        total_topics=total_topics,
        total_vocabulary_learned=vocab_learned,
        total_vocabulary_mastered=vocab_mastered,
        total_vocabulary=total_vocab,
        overall_completion_percentage=overall_percentage,
        average_score=avg_score,
        total_study_minutes=total_study_minutes
    )


# ============================================================
# GET /progress/streak - Thông tin streak
# ============================================================
@router.get("/streak", response_model=UserStreakResponse)
def get_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🔥 LẤY THÔNG TIN STREAK
    
    Logic:
    1. Lấy hoặc tạo UserStreak record
    2. Kiểm tra xem hôm nay đã học chưa
    3. Nếu hôm qua không học → reset streak
    4. Trả về current streak và longest streak
    
    Use case:
    - Hiển thị "🔥 5 ngày liên tiếp"
    - Motivation widget trên dashboard
    
    Returns:
    - current_streak: 5 (days)
    - longest_streak: 12 (days)  
    - learned_today: true
    - last_activity_date: "2024-01-15"
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Get or create streak
    streak = db.query(UserStreak).filter(
        UserStreak.user_id == current_user.id
    ).first()
    
    if not streak:
        streak = UserStreak(
            user_id=current_user.id,
            current_streak=0,
            longest_streak=0
        )
        db.add(streak)
        db.commit()
        db.refresh(streak)
    
    # Check today's activity
    today_stats = db.query(DailyStats).filter(
        DailyStats.user_id == current_user.id,
        DailyStats.date == today
    ).first()
    
    learned_today = today_stats is not None and today_stats.lessons_completed > 0
    
    # Check if streak should be reset
    if streak.last_activity_date:
        days_since_last = (today - streak.last_activity_date).days
        if days_since_last > 1:
            # Missed a day, reset streak
            streak.current_streak = 1 if learned_today else 0
            if learned_today:
                streak.last_activity_date = today
            db.commit()
    
    # Calculate streak freezes (can be implemented with premium feature)
    streak_freezes_available = 0  # TODO: Implement freeze system
    
    return UserStreakResponse(
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        learned_today=learned_today,
        last_activity_date=streak.last_activity_date,
        streak_freezes_available=streak_freezes_available,
        needs_activity_today=not learned_today
    )


# ============================================================
# POST /progress/streak/update - Cập nhật streak (internal)
# ============================================================
@router.post("/streak/update")
def update_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ➕ CẬP NHẬT STREAK SAU KHI HOÀN THÀNH BÀI HỌC
    
    Logic:
    1. Kiểm tra xem hôm nay đã có activity chưa
    2. Nếu chưa → tăng streak lên 1
    3. Cập nhật longest_streak nếu cần
    
    Note: 
    - Endpoint này thường được gọi tự động sau khi complete lesson
    - Không cần gọi thủ công từ frontend
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    streak = db.query(UserStreak).filter(
        UserStreak.user_id == current_user.id
    ).first()
    
    if not streak:
        streak = UserStreak(
            user_id=current_user.id,
            current_streak=1,
            longest_streak=1,
            last_activity_date=today
        )
        db.add(streak)
    else:
        # Check if already updated today
        if streak.last_activity_date == today:
            return {"message": "Streak already updated today", "current_streak": streak.current_streak}
        
        # Check continuity
        if streak.last_activity_date == yesterday:
            streak.current_streak += 1
        else:
            # Gap in streak, reset
            streak.current_streak = 1
        
        streak.last_activity_date = today
        
        # Update longest if needed
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
    
    db.commit()
    
    return {
        "message": "Streak updated",
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak
    }


# ============================================================
# GET /progress/daily - Thống kê theo ngày
# ============================================================
@router.get("/daily", response_model=List[DailyStatsResponse])
def get_daily_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📅 LẤY THỐNG KÊ THEO NGÀY
    
    Logic:
    1. Query DailyStats cho N ngày gần nhất
    2. Fill missing days với giá trị 0
    3. Trả về array để vẽ chart
    
    Use case:
    - Biểu đồ hoạt động 7 ngày gần nhất
    - Calendar view
    
    Params:
    - days: 7 (default) - số ngày cần lấy
    
    Returns:
    [
        {"date": "2024-01-15", "lessons_completed": 2, "minutes_studied": 45, ...},
        {"date": "2024-01-14", "lessons_completed": 1, "minutes_studied": 30, ...},
        ...
    ]
    """
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    # Get actual stats
    stats = db.query(DailyStats).filter(
        DailyStats.user_id == current_user.id,
        DailyStats.date >= start_date,
        DailyStats.date <= today
    ).order_by(DailyStats.date.desc()).all()
    
    # Create dict for easy lookup
    stats_dict = {s.date: s for s in stats}
    
    # Fill in missing days
    result = []
    for i in range(days):
        current_date = today - timedelta(days=i)
        
        if current_date in stats_dict:
            s = stats_dict[current_date]
            result.append(DailyStatsResponse(
                date=s.date,
                lessons_completed=s.lessons_completed,
                vocabulary_reviewed=s.vocabulary_reviewed,
                minutes_studied=s.minutes_studied,
                experience_points_earned=s.experience_points_earned,
                pronunciation_exercises=s.pronunciation_exercises or 0,
                conversation_turns=s.conversation_turns or 0
            ))
        else:
            result.append(DailyStatsResponse(
                date=current_date,
                lessons_completed=0,
                vocabulary_reviewed=0,
                minutes_studied=0,
                experience_points_earned=0,
                pronunciation_exercises=0,
                conversation_turns=0
            ))
    
    return result


# ============================================================
# GET /progress/weekly - Thống kê theo tuần
# ============================================================
@router.get("/weekly", response_model=WeeklyStatsResponse)
def get_weekly_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 LẤY THỐNG KÊ TUẦN NÀY
    """
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    
    stats = db.query(
        func.sum(DailyStats.lessons_completed).label('lessons'),
        func.sum(DailyStats.vocabulary_reviewed).label('vocab'),
        func.sum(DailyStats.minutes_studied).label('minutes'),
        func.sum(DailyStats.experience_points_earned).label('xp')
    ).filter(
        DailyStats.user_id == current_user.id,
        DailyStats.date >= start_of_week,
        DailyStats.date <= today
    ).first()
    
    # Get same period last week for comparison
    last_week_start = start_of_week - timedelta(days=7)
    last_week_end = last_week_start + timedelta(days=today.weekday())
    
    last_week_stats = db.query(
        func.sum(DailyStats.lessons_completed).label('lessons'),
        func.sum(DailyStats.minutes_studied).label('minutes')
    ).filter(
        DailyStats.user_id == current_user.id,
        DailyStats.date >= last_week_start,
        DailyStats.date <= last_week_end
    ).first()
    
    current_lessons = stats.lessons or 0
    current_minutes = stats.minutes or 0
    last_lessons = last_week_stats.lessons or 0
    last_minutes = last_week_stats.minutes or 0
    
    return WeeklyStatsResponse(
        week_start=start_of_week,
        week_end=today,
        lessons_completed=current_lessons,
        vocabulary_reviewed=stats.vocab or 0,
        minutes_studied=current_minutes,
        experience_points_earned=stats.xp or 0,
        lessons_change_from_last_week=current_lessons - last_lessons,
        minutes_change_from_last_week=current_minutes - last_minutes
    )


# ============================================================
# GET /progress/topics - Tiến độ theo chủ đề
# ============================================================
@router.get("/topics", response_model=List[ProgressSummaryByTopic])
def get_progress_by_topic(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📚 TIẾN ĐỘ THEO TỪNG CHỦ ĐỀ
    
    Returns:
    [
        {
            "topic_id": 1,
            "topic_name": "At the Restaurant",
            "total_lessons": 5,
            "completed_lessons": 3,
            "completion_percentage": 60.0,
            "average_score": 85.5
        },
        ...
    ]
    """
    topics = db.query(Topic).filter(Topic.is_active == True).all()
    
    result = []
    for topic in topics:
        # Count lessons in topic
        total_lessons = db.query(Lesson).filter(
            Lesson.topic_id == topic.id,
            Lesson.is_active == True
        ).count()
        
        # Count completed lessons
        completed_lessons = db.query(UserLessonProgress).join(Lesson).filter(
            Lesson.topic_id == topic.id,
            UserLessonProgress.user_id == current_user.id,
            UserLessonProgress.status == LessonStatus.COMPLETED
        ).count()
        
        # Average score for this topic
        avg_score = db.query(func.avg(LessonAttempt.overall_score)).join(Lesson).filter(
            Lesson.topic_id == topic.id,
            LessonAttempt.user_id == current_user.id,
            LessonAttempt.is_passed == True
        ).scalar()
        
        completion_pct = round((completed_lessons / total_lessons * 100), 1) if total_lessons > 0 else 0
        
        result.append(ProgressSummaryByTopic(
            topic_id=topic.id,
            topic_name=topic.name,
            topic_icon=topic.icon_name,
            total_lessons=total_lessons,
            completed_lessons=completed_lessons,
            completion_percentage=completion_pct,
            average_score=round(float(avg_score), 1) if avg_score else None
        ))
    
    return result


# ============================================================
# GET /progress/vocabulary - Vocabulary đã học
# ============================================================
@router.get("/vocabulary", response_model=List[UserVocabularyResponse])
def get_vocabulary_progress(
    limit: int = Query(50, le=200),
    mastered_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📝 DANH SÁCH TỪ VỰNG ĐÃ HỌC
    
    Use case:
    - Trang "Từ vựng của tôi"
    - Review từ vựng đã học
    
    Params:
    - limit: số lượng tối đa
    - mastered_only: chỉ lấy từ đã thành thạo
    """
    query = db.query(UserVocabulary).filter(
        UserVocabulary.user_id == current_user.id
    )
    
    if mastered_only:
        query = query.filter(UserVocabulary.is_mastered == True)
    
    user_vocabs = query.order_by(UserVocabulary.last_reviewed.desc()).limit(limit).all()
    
    result = []
    for uv in user_vocabs:
        vocab = db.query(Vocabulary).filter(Vocabulary.id == uv.vocabulary_id).first()
        if vocab:
            result.append(UserVocabularyResponse(
                vocabulary_id=vocab.id,
                word=vocab.word,
                meaning=vocab.meaning,
                pronunciation_ipa=vocab.pronunciation_ipa,
                example_sentence=vocab.example_sentence,
                times_practiced=uv.times_practiced,
                correct_count=uv.correct_count,
                is_mastered=uv.is_mastered,
                last_reviewed=uv.last_reviewed,
                mastery_percentage=round((uv.correct_count / max(uv.times_practiced, 1)) * 100, 1)
            ))
    
    return result


# ============================================================
# GET /progress/lessons - Tiến độ từng bài học
# ============================================================
@router.get("/lessons", response_model=List[LessonProgressResponse])
def get_lessons_progress(
    topic_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📋 TIẾN ĐỘ TỪNG BÀI HỌC
    
    Use case:
    - Danh sách bài học với status
    - Filter theo topic
    """
    query = db.query(Lesson).filter(Lesson.is_active == True)
    
    if topic_id:
        query = query.filter(Lesson.topic_id == topic_id)
    
    lessons = query.order_by(Lesson.order_index).all()
    
    result = []
    for lesson in lessons:
        # Get user's progress for this lesson
        progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == current_user.id,
            UserLessonProgress.lesson_id == lesson.id
        ).first()
        
        # Get best attempt
        best_attempt = db.query(LessonAttempt).filter(
            LessonAttempt.user_id == current_user.id,
            LessonAttempt.lesson_id == lesson.id
        ).order_by(LessonAttempt.overall_score.desc()).first()
        
        # Get attempt count
        attempt_count = db.query(LessonAttempt).filter(
            LessonAttempt.user_id == current_user.id,
            LessonAttempt.lesson_id == lesson.id
        ).count()
        
        result.append(LessonProgressResponse(
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            lesson_type=lesson.lesson_type.value if hasattr(lesson.lesson_type, 'value') else lesson.lesson_type,
            status=progress.status.value if progress and hasattr(progress.status, 'value') else (progress.status if progress else "available"),
            best_score=float(best_attempt.overall_score) if best_attempt and best_attempt.overall_score else None,
            attempt_count=attempt_count,
            is_passed=best_attempt.is_passed if best_attempt else False,
            last_attempted=best_attempt.completed_at if best_attempt else None
        ))
    
    return result


# ============================================================
# Helper Functions
# ============================================================

def get_completed_topics_count(db: Session, user_id: int) -> int:
    """Đếm số topic đã hoàn thành tất cả lessons"""
    topics = db.query(Topic).filter(Topic.is_active == True).all()
    completed_count = 0
    
    for topic in topics:
        total_lessons = db.query(Lesson).filter(
            Lesson.topic_id == topic.id,
            Lesson.is_active == True
        ).count()
        
        if total_lessons == 0:
            continue
        
        completed_lessons = db.query(UserLessonProgress).join(Lesson).filter(
            Lesson.topic_id == topic.id,
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.status == LessonStatus.COMPLETED
        ).count()
        
        if completed_lessons >= total_lessons:
            completed_count += 1
    
    return completed_count


def calculate_xp_to_next_level(current_level: int, current_xp: int) -> int:
    """Tính XP cần để lên level tiếp theo"""
    # Simple formula: each level needs level * 100 XP
    # Level 1: 100 XP, Level 2: 200 XP, Level 3: 300 XP...
    xp_needed_for_current = sum(i * 100 for i in range(1, current_level))
    xp_needed_for_next = sum(i * 100 for i in range(1, current_level + 1))
    
    return max(xp_needed_for_next - current_xp, 0)
