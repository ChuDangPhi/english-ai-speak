"""
Attempts Router - API endpoints cho Lần làm bài

=== GIẢI QUYẾT VẤN ĐỀ GÌ? ===
1. Tạo phiên làm bài mới khi user bắt đầu lesson
2. Hoàn thành phiên làm bài và tính điểm tổng
3. Cập nhật tiến độ user (unlock lesson tiếp theo)
4. Xem lịch sử làm bài

=== LOGIC HOẠT ĐỘNG ===
Flow khi user học 1 lesson:
1. POST /attempts → Tạo lesson_attempt mới, trả về attempt_id
2. User làm bài (vocabulary/pronunciation/conversation)
3. Các API khác cập nhật scores vào attempt
4. POST /attempts/{id}/complete → Hoàn thành, tính điểm, unlock lesson tiếp
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models import (
    LessonAttempt, Lesson, UserLessonProgress, UserProgress,
    Topic, DailyStats, UserStreak, LessonStatus
)
from app.models.user import User
from app.schemas.attempt import (
    LessonAttemptCreate, LessonAttemptComplete,
    LessonAttemptResponse, LessonAttemptStartResponse,
    LessonAttemptSummary, LessonAttemptHistoryItem,
    LessonAttemptHistoryResponse
)
from app.core.dependencies import get_current_user

# Import service
from app.services.progress_service import progress_service

router = APIRouter(
    prefix="/attempts",
    tags=["Lesson Attempts"]
)


# ============================================================
# POST /attempts - Bắt đầu làm bài mới
# ============================================================
@router.post("", response_model=LessonAttemptStartResponse, status_code=status.HTTP_201_CREATED)
def start_lesson_attempt(
    request: LessonAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ▶️ BẮT ĐẦU LÀM BÀI MỚI
    
    Logic:
    1. Kiểm tra lesson tồn tại và user có quyền truy cập
    2. Đếm số lần làm bài trước đó để set attempt_number
    3. Tạo lesson_attempt mới với started_at = now()
    4. Cập nhật user_lesson_progress status = "in_progress"
    
    Use case:
    - User click "Bắt đầu học" trên 1 lesson
    - Tạo phiên làm bài để track time, scores
    
    Returns:
    - attempt_id: Dùng cho các API submit sau đó
    - attempt_number: Lần thứ mấy user làm bài này
    """
    # 1. Check lesson exists
    lesson = db.query(Lesson).filter(
        Lesson.id == request.lesson_id,
        Lesson.is_active == True
    ).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bài học không tồn tại"
        )
    
    # 2. Check access permission (similar to lessons router)
    user_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == current_user.id,
        UserLessonProgress.lesson_id == request.lesson_id
    ).first()
    
    if user_progress and user_progress.status == LessonStatus.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bài học này chưa được mở khóa"
        )
    
    # 3. Count previous attempts
    previous_attempts = db.query(LessonAttempt).filter(
        LessonAttempt.user_id == current_user.id,
        LessonAttempt.lesson_id == request.lesson_id
    ).count()
    
    attempt_number = previous_attempts + 1
    
    # 4. Create new attempt
    new_attempt = LessonAttempt(
        user_id=current_user.id,
        lesson_id=request.lesson_id,
        attempt_number=attempt_number,
        started_at=datetime.utcnow(),
        is_completed=False,
        is_passed=False
    )
    
    db.add(new_attempt)
    
    # 5. Update user_lesson_progress
    if not user_progress:
        user_progress = UserLessonProgress(
            user_id=current_user.id,
            lesson_id=request.lesson_id,
            status=LessonStatus.IN_PROGRESS,
            total_attempts=1
        )
        db.add(user_progress)
    else:
        user_progress.status = LessonStatus.IN_PROGRESS
        user_progress.total_attempts += 1
        user_progress.last_attempt_at = datetime.utcnow()
    
    db.commit()
    db.refresh(new_attempt)
    
    # 6. Return response
    lesson_type = lesson.lesson_type.value if hasattr(lesson.lesson_type, 'value') else lesson.lesson_type
    
    return LessonAttemptStartResponse(
        attempt_id=new_attempt.id,
        lesson_id=lesson.id,
        lesson_type=lesson_type,
        lesson_title=lesson.title,
        attempt_number=attempt_number,
        started_at=new_attempt.started_at,
        instructions=lesson.instructions,
        passing_score=float(lesson.passing_score) if lesson.passing_score else 70.0,
        estimated_minutes=lesson.estimated_minutes
    )


# ============================================================
# POST /attempts/{attempt_id}/complete - Hoàn thành bài học
# ============================================================
@router.post("/{attempt_id}/complete", response_model=LessonAttemptSummary)
def complete_lesson_attempt(
    attempt_id: int,
    request: Optional[LessonAttemptComplete] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ HOÀN THÀNH BÀI HỌC
    
    Logic:
    1. Tính overall_score từ các scores đã có
    2. So sánh với passing_score để xác định is_passed
    3. Cập nhật completed_at, duration_seconds
    4. Nếu passed → Unlock lesson tiếp theo
    5. Cập nhật user_progress cho topic
    6. Cập nhật daily_stats và streak
    7. Generate AI feedback
    
    Use case:
    - User hoàn thành hết bài học
    - Nhận điểm tổng kết, feedback, và unlock bài tiếp
    """
    # 1. Get attempt
    attempt = db.query(LessonAttempt).filter(
        LessonAttempt.id == attempt_id,
        LessonAttempt.user_id == current_user.id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy phiên làm bài"
        )
    
    if attempt.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bài học này đã hoàn thành rồi"
        )
    
    # 2. Get lesson info
    lesson = db.query(Lesson).filter(Lesson.id == attempt.lesson_id).first()
    passing_score = float(lesson.passing_score) if lesson.passing_score else 70.0
    lesson_type = lesson.lesson_type.value if hasattr(lesson.lesson_type, 'value') else lesson.lesson_type
    
    # 3. Calculate overall score based on lesson type
    if request and request.overall_score is not None:
        overall_score = request.overall_score
    else:
        overall_score = calculate_overall_score(attempt, lesson_type)
    
    # 4. Update attempt
    attempt.completed_at = datetime.utcnow()
    attempt.duration_seconds = int((attempt.completed_at - attempt.started_at).total_seconds())
    attempt.overall_score = overall_score
    attempt.is_passed = overall_score >= passing_score
    attempt.is_completed = True
    
    # Generate AI feedback
    attempt.ai_feedback = generate_ai_feedback(attempt, lesson_type, overall_score, passing_score)
    
    # 5. Update user_lesson_progress
    user_lesson_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == current_user.id,
        UserLessonProgress.lesson_id == lesson.id
    ).first()
    
    if user_lesson_progress:
        if attempt.is_passed:
            user_lesson_progress.status = LessonStatus.COMPLETED
            if not user_lesson_progress.first_completed_at:
                user_lesson_progress.first_completed_at = datetime.utcnow()
        
        # Update best score
        if not user_lesson_progress.best_score or overall_score > float(user_lesson_progress.best_score):
            user_lesson_progress.best_score = overall_score
        
        user_lesson_progress.last_attempt_at = datetime.utcnow()
    
    # 6. Unlock next lesson if passed
    is_new_best = False
    previous_best = None
    
    if attempt.is_passed:
        unlock_next_lesson(db, current_user.id, lesson)
        
        # Check if new best
        if user_lesson_progress and user_lesson_progress.best_score:
            previous_best = float(user_lesson_progress.best_score)
            is_new_best = overall_score > previous_best
    
    # 7. Update topic progress
    update_topic_progress(db, current_user.id, lesson.topic_id)
    
    # 8. Update daily stats and streak
    update_daily_stats(db, current_user.id, attempt.duration_seconds // 60, attempt.is_passed)
    update_user_streak(db, current_user.id)
    
    db.commit()
    
    # 9. Build score breakdown
    score_breakdown = build_score_breakdown(attempt, lesson_type)
    
    # 10. Format duration
    minutes = attempt.duration_seconds // 60
    seconds = attempt.duration_seconds % 60
    duration_formatted = f"{minutes} phút {seconds} giây"
    
    return LessonAttemptSummary(
        attempt_id=attempt.id,
        lesson_id=lesson.id,
        lesson_type=lesson_type,
        lesson_title=lesson.title,
        attempt_number=attempt.attempt_number,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        duration_seconds=attempt.duration_seconds,
        duration_formatted=duration_formatted,
        overall_score=overall_score,
        passing_score=passing_score,
        is_passed=attempt.is_passed,
        score_breakdown=score_breakdown,
        ai_feedback=attempt.ai_feedback or "Hoàn thành bài học!",
        previous_best_score=previous_best,
        is_new_best=is_new_best,
        improvement=round(overall_score - previous_best, 1) if previous_best else None
    )


# ============================================================
# GET /attempts/history - Lịch sử làm bài
# ============================================================
@router.get("/history", response_model=LessonAttemptHistoryResponse)
def get_attempt_history(
    lesson_id: Optional[int] = Query(None, description="Filter theo lesson"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📜 XEM LỊCH SỬ LÀM BÀI
    
    Use case:
    - Xem lại các bài đã làm
    - Theo dõi sự tiến bộ qua các lần làm
    """
    query = db.query(LessonAttempt).filter(
        LessonAttempt.user_id == current_user.id
    )
    
    if lesson_id:
        query = query.filter(LessonAttempt.lesson_id == lesson_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    
    attempts = query.order_by(LessonAttempt.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Get lesson info
    lesson_ids = list(set([a.lesson_id for a in attempts]))
    lessons = db.query(Lesson).filter(Lesson.id.in_(lesson_ids)).all()
    lesson_map = {l.id: l for l in lessons}
    
    items = []
    for attempt in attempts:
        lesson = lesson_map.get(attempt.lesson_id)
        lesson_type = lesson.lesson_type.value if lesson and hasattr(lesson.lesson_type, 'value') else "unknown"
        
        items.append(LessonAttemptHistoryItem(
            id=attempt.id,
            lesson_id=attempt.lesson_id,
            lesson_title=lesson.title if lesson else "Unknown",
            lesson_type=lesson_type,
            attempt_number=attempt.attempt_number,
            overall_score=float(attempt.overall_score) if attempt.overall_score else None,
            is_passed=attempt.is_passed,
            is_completed=attempt.is_completed,
            duration_seconds=attempt.duration_seconds,
            created_at=attempt.created_at
        ))
    
    return LessonAttemptHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


# ============================================================
# Helper Functions
# ============================================================

def calculate_overall_score(attempt: LessonAttempt, lesson_type: str) -> float:
    """Tính điểm tổng dựa vào loại lesson"""
    
    if lesson_type == "vocabulary_matching":
        if attempt.vocabulary_total and attempt.vocabulary_total > 0:
            return (attempt.vocabulary_correct / attempt.vocabulary_total) * 100
        return 0.0
    
    elif lesson_type == "pronunciation":
        scores = []
        if attempt.pronunciation_score:
            scores.append(float(attempt.pronunciation_score))
        if attempt.intonation_score:
            scores.append(float(attempt.intonation_score))
        if attempt.stress_score:
            scores.append(float(attempt.stress_score))
        
        return sum(scores) / len(scores) if scores else 0.0
    
    elif lesson_type == "conversation":
        scores = []
        if attempt.fluency_score:
            scores.append(float(attempt.fluency_score))
        if attempt.grammar_score:
            scores.append(float(attempt.grammar_score))
        
        return sum(scores) / len(scores) if scores else 0.0
    
    else:
        return float(attempt.overall_score) if attempt.overall_score else 0.0


def build_score_breakdown(attempt: LessonAttempt, lesson_type: str) -> dict:
    """Build chi tiết điểm theo loại lesson"""
    
    if lesson_type == "vocabulary_matching":
        return {
            "vocabulary_correct": attempt.vocabulary_correct or 0,
            "vocabulary_total": attempt.vocabulary_total or 0,
            "accuracy_percent": round((attempt.vocabulary_correct / attempt.vocabulary_total) * 100, 1) if attempt.vocabulary_total else 0
        }
    
    elif lesson_type == "pronunciation":
        return {
            "pronunciation_score": float(attempt.pronunciation_score) if attempt.pronunciation_score else 0,
            "intonation_score": float(attempt.intonation_score) if attempt.intonation_score else 0,
            "stress_score": float(attempt.stress_score) if attempt.stress_score else 0
        }
    
    elif lesson_type == "conversation":
        return {
            "fluency_score": float(attempt.fluency_score) if attempt.fluency_score else 0,
            "grammar_score": float(attempt.grammar_score) if attempt.grammar_score else 0,
            "conversation_turns": attempt.conversation_turns or 0
        }
    
    return {}


def generate_ai_feedback(attempt: LessonAttempt, lesson_type: str, score: float, passing_score: float) -> str:
    """Generate feedback dựa vào kết quả"""
    
    if score >= 90:
        prefix = "🌟 Xuất sắc!"
    elif score >= passing_score:
        prefix = "✅ Tốt lắm!"
    elif score >= 50:
        prefix = "💪 Cố gắng thêm!"
    else:
        prefix = "📚 Cần ôn tập lại!"
    
    if lesson_type == "vocabulary_matching":
        return f"{prefix} Bạn đã nối đúng {attempt.vocabulary_correct}/{attempt.vocabulary_total} từ vựng."
    
    elif lesson_type == "pronunciation":
        return f"{prefix} Điểm phát âm trung bình: {score:.1f}/100. Hãy tiếp tục luyện tập!"
    
    elif lesson_type == "conversation":
        return f"{prefix} Bạn đã hoàn thành {attempt.conversation_turns} lượt hội thoại với AI."
    
    return f"{prefix} Điểm: {score:.1f}/100"


def unlock_next_lesson(db: Session, user_id: int, current_lesson: Lesson):
    """Mở khóa lesson tiếp theo trong topic"""
    
    next_lesson = db.query(Lesson).filter(
        Lesson.topic_id == current_lesson.topic_id,
        Lesson.lesson_order == current_lesson.lesson_order + 1,
        Lesson.is_active == True
    ).first()
    
    if next_lesson:
        existing_progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == next_lesson.id
        ).first()
        
        if not existing_progress:
            new_progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=next_lesson.id,
                status=LessonStatus.AVAILABLE,
                total_attempts=0
            )
            db.add(new_progress)
        elif existing_progress.status == LessonStatus.LOCKED:
            existing_progress.status = LessonStatus.AVAILABLE


def update_topic_progress(db: Session, user_id: int, topic_id: int):
    """Cập nhật tiến độ topic"""
    
    # Count completed lessons
    completed_count = db.query(UserLessonProgress).join(Lesson).filter(
        UserLessonProgress.user_id == user_id,
        Lesson.topic_id == topic_id,
        UserLessonProgress.status == LessonStatus.COMPLETED
    ).count()
    
    # Get topic total lessons
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    total_lessons = topic.total_lessons if topic else 0
    
    # Get or create user_progress
    user_progress = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.topic_id == topic_id
    ).first()
    
    if not user_progress:
        user_progress = UserProgress(
            user_id=user_id,
            topic_id=topic_id,
            lessons_completed=completed_count,
            total_lessons=total_lessons,
            status="in_progress",
            times_practiced=1
        )
        db.add(user_progress)
    else:
        user_progress.lessons_completed = completed_count
        user_progress.total_lessons = total_lessons
        user_progress.times_practiced += 1
        user_progress.last_practiced_at = datetime.utcnow()
        
        if completed_count >= total_lessons:
            user_progress.status = "completed"
        elif completed_count > 0:
            user_progress.status = "in_progress"


def update_daily_stats(db: Session, user_id: int, minutes: int, lesson_completed: bool):
    """Cập nhật thống kê hàng ngày"""
    from datetime import date
    
    today = date.today()
    
    daily_stat = db.query(DailyStats).filter(
        DailyStats.user_id == user_id,
        DailyStats.practice_date == today
    ).first()
    
    if not daily_stat:
        daily_stat = DailyStats(
            user_id=user_id,
            practice_date=today,
            total_sessions=1,
            total_minutes=minutes,
            lessons_completed=1 if lesson_completed else 0
        )
        db.add(daily_stat)
    else:
        daily_stat.total_sessions += 1
        daily_stat.total_minutes += minutes
        if lesson_completed:
            daily_stat.lessons_completed += 1


def update_user_streak(db: Session, user_id: int):
    """Cập nhật streak học tập"""
    from datetime import date, timedelta
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    streak = db.query(UserStreak).filter(UserStreak.user_id == user_id).first()
    
    if not streak:
        streak = UserStreak(
            user_id=user_id,
            current_streak=1,
            longest_streak=1,
            last_activity_date=today
        )
        db.add(streak)
    else:
        if streak.last_activity_date == today:
            # Đã học hôm nay rồi, không cần update
            pass
        elif streak.last_activity_date == yesterday:
            # Tiếp tục streak
            streak.current_streak += 1
            streak.longest_streak = max(streak.longest_streak, streak.current_streak)
            streak.last_activity_date = today
        else:
            # Mất streak, bắt đầu lại
            streak.current_streak = 1
            streak.last_activity_date = today
