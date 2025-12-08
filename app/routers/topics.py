"""
Topics Router - API endpoints cho Chủ đề học tập

=== GIẢI QUYẾT VẤN ĐỀ GÌ? ===
1. Hiển thị danh sách chủ đề cho user chọn học
2. Lấy chi tiết 1 chủ đề kèm danh sách bài học
3. Theo dõi tiến độ học của user cho từng chủ đề

=== LOGIC HOẠT ĐỘNG ===
- User mở app → GET /topics → Hiển thị danh sách chủ đề
- User click vào 1 chủ đề → GET /topics/{id} → Hiển thị lessons trong topic
- Nếu user đã login → Kèm theo tiến độ (lessons_completed, progress_percent)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.database import get_db
from app.models import Topic, Lesson, UserProgress, UserLessonProgress, LessonStatus
from app.models.user import User
from app.schemas.topic import (
    TopicCreate, TopicUpdate, TopicBasicResponse,
    TopicListResponse, TopicWithProgressResponse, TopicFilter
)
from app.schemas.lesson import TopicDetailResponse, LessonWithProgressResponse
from app.core.dependencies import get_current_user, get_current_admin

router = APIRouter(
    prefix="/topics",
    tags=["Topics"]
)


# ============================================================
# GET /topics - Lấy danh sách chủ đề
# ============================================================
@router.get("", response_model=TopicListResponse)
def get_topics(
    # Filter params
    category: Optional[str] = Query(None, description="Filter theo category: general, business, travel, daily_life"),
    difficulty_level: Optional[str] = Query(None, description="Filter theo độ khó: beginner, intermediate, advanced"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo title"),
    # Pagination
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(10, ge=1, le=50, description="Số item mỗi trang"),
    # Database
    db: Session = Depends(get_db)
):
    """
    📋 LẤY DANH SÁCH CHỦ ĐỀ
    
    Logic:
    1. Query tất cả topics đang active
    2. Apply filters nếu có (category, difficulty, search)
    3. Phân trang kết quả
    4. Trả về danh sách topics
    
    Use case:
    - Màn hình chính hiển thị danh sách chủ đề
    - Filter theo category (Daily Life, Business, Travel...)
    - Filter theo độ khó cho user mới/cũ
    """
    # Base query
    query = db.query(Topic).filter(Topic.is_active == True)
    
    # Apply filters
    if category:
        query = query.filter(Topic.category == category)
    if difficulty_level:
        query = query.filter(Topic.difficulty_level == difficulty_level)
    if search:
        query = query.filter(Topic.title.ilike(f"%{search}%"))
    
    # Count total
    total = query.count()
    
    # Pagination
    offset = (page - 1) * page_size
    topics = query.order_by(Topic.display_order, Topic.id).offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return TopicListResponse(
        items=[TopicBasicResponse.model_validate(t) for t in topics],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# ============================================================
# GET /topics/with-progress - Lấy danh sách chủ đề KÈM tiến độ
# ============================================================
@router.get("/with-progress", response_model=List[TopicWithProgressResponse])
def get_topics_with_progress(
    category: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ⚠️ Yêu cầu đăng nhập
):
    """
    📋 LẤY DANH SÁCH CHỦ ĐỀ KÈM TIẾN ĐỘ CỦA USER
    
    Logic:
    1. Query topics + LEFT JOIN với user_progress
    2. Tính progress_percent = lessons_completed / total_lessons * 100
    3. Xác định status: not_started, in_progress, completed
    
    Use case:
    - Màn hình chính khi user đã đăng nhập
    - Hiển thị thanh progress bar cho từng topic
    - Hiển thị badge "Completed" / "In Progress"
    """
    # Query topics
    query = db.query(Topic).filter(Topic.is_active == True)
    
    if category:
        query = query.filter(Topic.category == category)
    if difficulty_level:
        query = query.filter(Topic.difficulty_level == difficulty_level)
    
    topics = query.order_by(Topic.display_order, Topic.id).all()
    
    # Get user progress for all topics
    user_progress_map = {}
    user_progress_list = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id
    ).all()
    
    for up in user_progress_list:
        user_progress_map[up.topic_id] = up
    
    # Build response
    result = []
    for topic in topics:
        progress = user_progress_map.get(topic.id)
        
        # Calculate progress percent
        if progress and topic.total_lessons > 0:
            progress_percent = (progress.lessons_completed / topic.total_lessons) * 100
        else:
            progress_percent = 0.0
        
        # Determine status
        if progress is None or progress.lessons_completed == 0:
            status = "not_started"
        elif progress.lessons_completed >= topic.total_lessons:
            status = "completed"
        else:
            status = "in_progress"
        
        result.append(TopicWithProgressResponse(
            id=topic.id,
            title=topic.title,
            description=topic.description,
            category=topic.category,
            difficulty_level=topic.difficulty_level,
            thumbnail_url=topic.thumbnail_url,
            total_lessons=topic.total_lessons,
            estimated_duration_minutes=topic.estimated_duration_minutes,
            lessons_completed=progress.lessons_completed if progress else 0,
            progress_percent=round(progress_percent, 1),
            status=status,
            best_score=float(progress.best_score) if progress and progress.best_score else None,
            last_practiced_at=progress.last_practiced_at if progress else None
        ))
    
    return result


# ============================================================
# GET /topics/{topic_id} - Lấy chi tiết 1 chủ đề
# ============================================================
@router.get("/{topic_id}", response_model=TopicDetailResponse)
def get_topic_detail(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """
    📖 LẤY CHI TIẾT CHỦ ĐỀ + DANH SÁCH BÀI HỌC
    
    Logic:
    1. Query topic by ID
    2. Query tất cả lessons thuộc topic này
    3. Nếu user đã login → Query lesson progress để biết status từng lesson
    4. Lesson đầu tiên luôn "available", các lesson sau "locked"
    5. Unlock lesson tiếp theo khi lesson trước "completed"
    
    Use case:
    - User click vào 1 topic → Hiển thị danh sách 3 lessons
    - Lesson 1: Available (có thể học)
    - Lesson 2: Locked (cần hoàn thành Lesson 1)
    - Lesson 3: Locked (cần hoàn thành Lesson 2)
    
    Note: Endpoint này không yêu cầu authentication.
    Để lấy tiến độ user, sử dụng GET /topics/my-progress/{topic_id}
    """
    # Get topic
    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.is_active == True).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic không tồn tại"
        )
    
    # Get lessons
    lessons = db.query(Lesson).filter(
        Lesson.topic_id == topic_id,
        Lesson.is_active == True
    ).order_by(Lesson.lesson_order).all()
    
    # Get user progress if logged in
    # NOTE: Endpoint này public, không cần auth
    # Sử dụng endpoint riêng GET /topics/my-progress/{id} để lấy tiến độ
    lesson_progress_map = {}
    user_topic_progress = None
    current_user = None  # No authentication for this endpoint
    
    if current_user:
        # Get lesson progress
        lesson_progress_list = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == current_user.id,
            UserLessonProgress.lesson_id.in_([l.id for l in lessons])
        ).all()
        
        for lp in lesson_progress_list:
            lesson_progress_map[lp.lesson_id] = lp
        
        # Get topic progress
        user_topic_progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.topic_id == topic_id
        ).first()
    
    # Build lessons response with status
    lessons_response = []
    previous_completed = True  # Lesson đầu tiên luôn available
    
    for lesson in lessons:
        progress = lesson_progress_map.get(lesson.id)
        
        # Determine lesson status
        if progress:
            lesson_status = progress.status.value if hasattr(progress.status, 'value') else progress.status
        elif previous_completed:
            lesson_status = "available"
        else:
            lesson_status = "locked"
        
        lessons_response.append(LessonWithProgressResponse(
            id=lesson.id,
            topic_id=lesson.topic_id,
            lesson_type=lesson.lesson_type.value if hasattr(lesson.lesson_type, 'value') else lesson.lesson_type,
            title=lesson.title,
            description=lesson.description,
            lesson_order=lesson.lesson_order,
            instructions=lesson.instructions,
            estimated_minutes=lesson.estimated_minutes,
            passing_score=float(lesson.passing_score) if lesson.passing_score else 70.0,
            status=lesson_status,
            best_score=float(progress.best_score) if progress and progress.best_score else None,
            total_attempts=progress.total_attempts if progress else 0,
            last_attempt_at=progress.last_attempt_at if progress else None
        ))
        
        # Update previous_completed for next iteration
        previous_completed = (lesson_status == "completed")
    
    # Calculate topic progress
    lessons_completed = sum(1 for l in lessons_response if l.status == "completed")
    total_lessons = len(lessons_response)
    progress_percent = (lessons_completed / total_lessons * 100) if total_lessons > 0 else 0
    
    if lessons_completed == 0:
        topic_status = "not_started"
    elif lessons_completed >= total_lessons:
        topic_status = "completed"
    else:
        topic_status = "in_progress"
    
    return TopicDetailResponse(
        id=topic.id,
        title=topic.title,
        description=topic.description,
        category=topic.category,
        difficulty_level=topic.difficulty_level,
        thumbnail_url=topic.thumbnail_url,
        total_lessons=total_lessons,
        estimated_duration_minutes=topic.estimated_duration_minutes,
        lessons=lessons_response,
        lessons_completed=lessons_completed,
        progress_percent=round(progress_percent, 1),
        status=topic_status
    )


# ============================================================
# ADMIN APIs - Quản lý Topics
# ============================================================

@router.post("", response_model=TopicBasicResponse, status_code=status.HTTP_201_CREATED)
def create_topic(
    topic_data: TopicCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)  # Chỉ admin mới được tạo topic
):
    """
    ➕ TẠO CHỦ ĐỀ MỚI (Admin only)
    
    Logic:
    1. Validate dữ liệu đầu vào
    2. Tạo topic mới trong DB
    3. total_lessons = 0 (chưa có lesson nào)
    
    Use case:
    - Admin thêm chủ đề mới: "Job Interview", "Shopping", etc.
    """
    new_topic = Topic(
        title=topic_data.title,
        description=topic_data.description,
        category=topic_data.category,
        difficulty_level=topic_data.difficulty_level,
        thumbnail_url=topic_data.thumbnail_url,
        estimated_duration_minutes=topic_data.estimated_duration_minutes,
        display_order=topic_data.display_order,
        total_lessons=0,
        is_active=True
    )
    
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    
    return TopicBasicResponse.model_validate(new_topic)


@router.put("/{topic_id}", response_model=TopicBasicResponse)
def update_topic(
    topic_id: int,
    topic_data: TopicUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)  # Chỉ admin mới được sửa topic
):
    """
    ✏️ CẬP NHẬT CHỦ ĐỀ (Admin only)
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic không tồn tại")
    
    # Update fields if provided
    update_data = topic_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(topic, field, value)
    
    db.commit()
    db.refresh(topic)
    
    return TopicBasicResponse.model_validate(topic)


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)  # Chỉ admin mới được xóa topic
):
    """
    🗑️ XÓA CHỦ ĐỀ (Admin only) - Soft delete
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic không tồn tại")
    
    # Soft delete - chỉ đánh dấu inactive
    topic.is_active = False
    db.commit()
    
    return None
