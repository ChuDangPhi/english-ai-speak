"""
Lessons Router - API endpoints cho Bài học

=== GIẢI QUYẾT VẤN ĐỀ GÌ? ===
1. Lấy chi tiết bài học theo loại (vocabulary, pronunciation, conversation)
2. Mỗi loại lesson có data structure khác nhau
3. Khởi tạo lesson attempt khi user bắt đầu học

=== LOGIC HOẠT ĐỘNG ===
- User click "Học" trên 1 lesson → POST /attempts (tạo attempt)
- Sau đó GET /lessons/{id} → Lấy nội dung bài học tương ứng
- Lesson type = vocabulary_matching → Trả về danh sách từ vựng
- Lesson type = pronunciation → Trả về danh sách bài tập phát âm
- Lesson type = conversation → Trả về template hội thoại AI
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models import (
    Lesson, LessonVocabulary, Vocabulary,
    PronunciationExercise, ConversationTemplate,
    UserLessonProgress, LessonType
)
from app.models.user import User
from app.schemas.lesson import (
    LessonCreate, LessonBasicResponse,
    VocabularyMatchingLessonDetail, PronunciationLessonDetail,
    ConversationLessonDetail, PronunciationExerciseResponse,
    ConversationTemplateResponse
)
from app.schemas.vocabulary import VocabularyForMatchingGame
from app.core.dependencies import get_current_user, get_current_admin

router = APIRouter(
    prefix="/lessons",
    tags=["Lessons"]
)


# ============================================================
# GET /lessons/{lesson_id} - Lấy chi tiết bài học
# ============================================================
@router.get("/{lesson_id}")
def get_lesson_detail(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📖 LẤY CHI TIẾT BÀI HỌC
    
    Logic:
    1. Query lesson by ID
    2. Kiểm tra user có quyền truy cập không (lesson phải available hoặc completed)
    3. Tuỳ theo lesson_type, trả về data khác nhau:
       - vocabulary_matching → List từ vựng
       - pronunciation → List bài tập phát âm
       - conversation → Template hội thoại
    
    Use case:
    - User click "Bắt đầu học" → Hiển thị nội dung bài học
    - Vocabulary: Hiển thị game nối từ
    - Pronunciation: Hiển thị từ/cụm từ để đọc
    - Conversation: Hiển thị chat với AI
    """
    # 1. Get lesson
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.is_active == True
    ).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bài học không tồn tại"
        )
    
    # NOTE: Tạm bỏ kiểm tra quyền truy cập - cho phép truy cập mọi lesson
    # TODO: Bật lại sau khi test xong
    
    # 3. Return data based on lesson_type
    lesson_type = lesson.lesson_type.value if hasattr(lesson.lesson_type, 'value') else lesson.lesson_type
    
    if lesson_type == "vocabulary_matching":
        return get_vocabulary_matching_lesson(lesson, db)
    
    elif lesson_type == "pronunciation":
        return get_pronunciation_lesson(lesson, db)
    
    elif lesson_type == "conversation":
        return get_conversation_lesson(lesson, db)
    
    else:  # mixed hoặc loại khác
        return get_mixed_lesson(lesson, db)


def get_vocabulary_matching_lesson(lesson: Lesson, db: Session) -> VocabularyMatchingLessonDetail:
    """
    🔤 VOCABULARY MATCHING LESSON
    
    Trả về danh sách 3-5 từ vựng để chơi game nối từ với nghĩa
    
    Data structure:
    {
        "id": 1,
        "title": "Restaurant Vocabulary",
        "lesson_type": "vocabulary_matching",
        "vocabulary_list": [
            {"id": 1, "word": "restaurant", "definition": "Nhà hàng"},
            {"id": 2, "word": "waiter", "definition": "Bồi bàn"},
            ...
        ]
    }
    """
    # Query từ vựng qua bảng lesson_vocabulary
    lesson_vocab = db.query(LessonVocabulary).filter(
        LessonVocabulary.lesson_id == lesson.id
    ).order_by(LessonVocabulary.display_order).all()
    
    vocab_ids = [lv.vocabulary_id for lv in lesson_vocab]
    vocabularies = db.query(Vocabulary).filter(Vocabulary.id.in_(vocab_ids)).all()
    
    # Maintain order
    vocab_map = {v.id: v for v in vocabularies}
    ordered_vocab = [vocab_map[vid] for vid in vocab_ids if vid in vocab_map]
    
    return VocabularyMatchingLessonDetail(
        id=lesson.id,
        title=lesson.title,
        description=lesson.description,
        instructions=lesson.instructions or "Nối từ tiếng Anh với nghĩa tiếng Việt tương ứng",
        lesson_type="vocabulary_matching",
        passing_score=float(lesson.passing_score) if lesson.passing_score else 70.0,
        estimated_minutes=lesson.estimated_minutes,
        vocabulary_list=[
            VocabularyForMatchingGame(
                id=v.id,
                word=v.word,
                definition=v.definition
            ) for v in ordered_vocab
        ]
    )


def get_pronunciation_lesson(lesson: Lesson, db: Session) -> PronunciationLessonDetail:
    """
    🎤 PRONUNCIATION LESSON
    
    Trả về danh sách bài tập phát âm: từ đơn, cụm từ, câu
    
    Data structure:
    {
        "id": 2,
        "title": "Restaurant Pronunciation",
        "lesson_type": "pronunciation",
        "exercises": [
            {"id": 1, "exercise_type": "word", "content": "restaurant", "phonetic": "/ˈrestərɒnt/"},
            {"id": 2, "exercise_type": "phrase", "content": "I'd like to order"},
            {"id": 3, "exercise_type": "sentence", "content": "Can I have the menu, please?"}
        ]
    }
    """
    # Query pronunciation exercises
    exercises = db.query(PronunciationExercise).filter(
        PronunciationExercise.lesson_id == lesson.id
    ).order_by(PronunciationExercise.display_order).all()
    
    return PronunciationLessonDetail(
        id=lesson.id,
        title=lesson.title,
        description=lesson.description,
        instructions=lesson.instructions or "Nhấn vào mic và đọc theo nội dung hiển thị. AI sẽ đánh giá phát âm của bạn.",
        lesson_type="pronunciation",
        passing_score=float(lesson.passing_score) if lesson.passing_score else 70.0,
        estimated_minutes=lesson.estimated_minutes,
        exercises=[
            PronunciationExerciseResponse(
                id=ex.id,
                exercise_type=ex.exercise_type.value if hasattr(ex.exercise_type, 'value') else ex.exercise_type,
                content=ex.content,
                phonetic=ex.phonetic,
                audio_url=ex.audio_url,
                target_pronunciation_score=float(ex.target_pronunciation_score) if ex.target_pronunciation_score else 70.0,
                display_order=ex.display_order
            ) for ex in exercises
        ]
    )


def get_conversation_lesson(lesson: Lesson, db: Session) -> ConversationLessonDetail:
    """
    💬 CONVERSATION LESSON
    
    Trả về template hội thoại với AI
    
    Data structure:
    {
        "id": 3,
        "title": "Restaurant Conversation",
        "lesson_type": "conversation",
        "conversation_template": {
            "ai_role": "Waiter at restaurant",
            "scenario_context": "You are ordering food at a restaurant...",
            "starter_prompts": ["Hi, I'd like to see the menu", "What do you recommend?"],
            "min_turns": 5
        }
    }
    """
    # Query conversation template
    template = db.query(ConversationTemplate).filter(
        ConversationTemplate.lesson_id == lesson.id
    ).first()
    
    template_response = None
    if template:
        # Parse JSON strings if needed
        import json
        
        starter_prompts = template.starter_prompts
        if isinstance(starter_prompts, str):
            try:
                starter_prompts = json.loads(starter_prompts)
            except:
                starter_prompts = []
        
        suggested_topics = template.suggested_topics
        if isinstance(suggested_topics, str):
            try:
                suggested_topics = json.loads(suggested_topics)
            except:
                suggested_topics = []
        
        template_response = ConversationTemplateResponse(
            id=template.id,
            ai_role=template.ai_role,
            scenario_context=template.scenario_context,
            starter_prompts=starter_prompts or [],
            suggested_topics=suggested_topics or [],
            min_turns=template.min_turns,
            max_duration_minutes=template.max_duration_minutes
        )
    
    return ConversationLessonDetail(
        id=lesson.id,
        title=lesson.title,
        description=lesson.description,
        instructions=lesson.instructions or "Trò chuyện với AI về chủ đề này. Cố gắng sử dụng từ vựng đã học.",
        lesson_type="conversation",
        passing_score=float(lesson.passing_score) if lesson.passing_score else 70.0,
        estimated_minutes=lesson.estimated_minutes,
        conversation_template=template_response
    )


def get_mixed_lesson(lesson: Lesson, db: Session):
    """
    🎯 MIXED LESSON - Kết hợp nhiều loại
    """
    # Trả về tất cả data
    vocab_data = get_vocabulary_matching_lesson(lesson, db)
    pronunciation_data = get_pronunciation_lesson(lesson, db)
    conversation_data = get_conversation_lesson(lesson, db)
    
    return {
        "id": lesson.id,
        "title": lesson.title,
        "lesson_type": "mixed",
        "vocabulary_list": vocab_data.vocabulary_list,
        "pronunciation_exercises": pronunciation_data.exercises,
        "conversation_template": conversation_data.conversation_template
    }


# ============================================================
# ADMIN APIs - Quản lý Lessons
# ============================================================

@router.post("", response_model=LessonBasicResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    lesson_data: LessonCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)  # Chỉ admin mới được tạo lesson
):
    """
    ➕ TẠO BÀI HỌC MỚI (Admin only)
    
    Logic:
    1. Tạo lesson trong topic
    2. Cập nhật total_lessons của topic
    
    Use case:
    - Admin thêm Lesson 1 (Vocabulary) vào Topic "Restaurant"
    - Admin thêm Lesson 2 (Pronunciation) vào Topic "Restaurant"
    """
    # Verify topic exists
    from app.models import Topic
    topic = db.query(Topic).filter(Topic.id == lesson_data.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic không tồn tại")
    
    # Create lesson
    new_lesson = Lesson(
        topic_id=lesson_data.topic_id,
        lesson_type=lesson_data.lesson_type,
        title=lesson_data.title,
        description=lesson_data.description,
        lesson_order=lesson_data.lesson_order,
        instructions=lesson_data.instructions,
        difficulty_level=lesson_data.difficulty_level,
        estimated_minutes=lesson_data.estimated_minutes,
        passing_score=lesson_data.passing_score,
        is_active=True
    )
    
    db.add(new_lesson)
    
    # Update topic total_lessons
    topic.total_lessons = db.query(Lesson).filter(
        Lesson.topic_id == topic.id,
        Lesson.is_active == True
    ).count() + 1
    
    db.commit()
    db.refresh(new_lesson)
    
    return LessonBasicResponse.model_validate(new_lesson)


# ============================================================
# API thêm từ vựng vào lesson
# ============================================================
@router.post("/{lesson_id}/vocabulary")
def add_vocabulary_to_lesson(
    lesson_id: int,
    vocabulary_ids: List[int],
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)  # Chỉ admin mới được thêm vocabulary
):
    """
    ➕ THÊM TỪ VỰNG VÀO LESSON (Admin only)
    
    Logic:
    - Thêm liên kết lesson_vocabulary cho mỗi vocabulary_id
    
    Use case:
    - Admin chọn 5 từ vựng để thêm vào Lesson Vocabulary Matching
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson không tồn tại")
    
    # Add vocabulary links
    for order, vocab_id in enumerate(vocabulary_ids):
        existing = db.query(LessonVocabulary).filter(
            LessonVocabulary.lesson_id == lesson_id,
            LessonVocabulary.vocabulary_id == vocab_id
        ).first()
        
        if not existing:
            link = LessonVocabulary(
                lesson_id=lesson_id,
                vocabulary_id=vocab_id,
                display_order=order
            )
            db.add(link)
    
    db.commit()
    
    return {"message": f"Đã thêm {len(vocabulary_ids)} từ vựng vào lesson"}
