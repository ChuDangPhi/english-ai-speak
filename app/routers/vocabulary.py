"""
Vocabulary Router - API endpoints cho Từ vựng và Game nối từ

=== GIẢI QUYẾT VẤN ĐỀ GÌ? ===
1. CRUD từ vựng (Admin)
2. Game nối từ với nghĩa
3. Submit kết quả và tính điểm
4. Lưu từ vựng yêu thích của user

=== LOGIC HOẠT ĐỘNG ===
Game nối từ:
1. User vào Lesson Vocabulary → GET /lessons/{id} → Nhận 5 từ
2. Frontend hiển thị 5 từ tiếng Anh + 5 nghĩa (xáo trộn)
3. User kéo thả nối từ với nghĩa
4. User nhấn Submit → POST /vocabulary/submit-matching
5. Server kiểm tra, tính điểm, trả về kết quả
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import (
    Vocabulary, LessonAttempt, VocabularyMatchingResult,
    UserVocabulary, Lesson
)
from app.models.user import User
from app.schemas.vocabulary import (
    VocabularyCreate, VocabularyUpdate, VocabularyResponse,
    VocabularyMatchingSubmitRequest, VocabularyMatchingSummary,
    VocabularyMatchingResultResponse, VocabularyWithUserProgress,
    UserVocabularySaveRequest, UserVocabularyListResponse
)
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/vocabulary",
    tags=["Vocabulary"]
)


# ============================================================
# POST /vocabulary/submit-matching - Submit kết quả game nối từ
# ============================================================
@router.post("/submit-matching", response_model=VocabularyMatchingSummary)
def submit_vocabulary_matching(
    request: VocabularyMatchingSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🎯 SUBMIT KẾT QUẢ GAME NỐI TỪ
    
    Logic:
    1. Nhận danh sách {vocabulary_id, user_answer, time_taken}
    2. So sánh user_answer với definition trong DB
    3. Tính số đúng/sai, accuracy_percent
    4. Lưu kết quả vào vocabulary_matching_results
    5. Cập nhật lesson_attempt scores
    6. Cập nhật user_vocabulary (times_encountered, times_correct)
    
    Use case:
    - User hoàn thành game nối 5 từ
    - Submit để nhận điểm và xem kết quả chi tiết
    
    Example request:
    {
        "lesson_attempt_id": 123,
        "results": [
            {"vocabulary_id": 1, "user_answer": "Nhà hàng", "time_taken_seconds": 3},
            {"vocabulary_id": 2, "user_answer": "Bồi bàn", "time_taken_seconds": 2}
        ]
    }
    """
    # 1. Verify lesson_attempt
    attempt = db.query(LessonAttempt).filter(
        LessonAttempt.id == request.lesson_attempt_id,
        LessonAttempt.user_id == current_user.id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy phiên làm bài"
        )
    
    # 2. Get all vocabulary items
    vocab_ids = [r.vocabulary_id for r in request.results]
    vocabularies = db.query(Vocabulary).filter(Vocabulary.id.in_(vocab_ids)).all()
    vocab_map = {v.id: v for v in vocabularies}
    
    # 3. Check answers and build results
    results = []
    correct_count = 0
    total_time = 0
    
    for item in request.results:
        vocab = vocab_map.get(item.vocabulary_id)
        if not vocab:
            continue
        
        # So sánh answer (case-insensitive, strip whitespace)
        is_correct = item.user_answer.strip().lower() == vocab.definition.strip().lower()
        
        if is_correct:
            correct_count += 1
        
        total_time += item.time_taken_seconds or 0
        
        # Lưu kết quả chi tiết
        matching_result = VocabularyMatchingResult(
            lesson_attempt_id=attempt.id,
            vocabulary_id=item.vocabulary_id,
            user_answer=item.user_answer,
            is_correct=is_correct,
            time_taken_seconds=item.time_taken_seconds
        )
        db.add(matching_result)
        
        # Build response item
        results.append(VocabularyMatchingResultResponse(
            vocabulary_id=vocab.id,
            word=vocab.word,
            correct_definition=vocab.definition,
            user_answer=item.user_answer,
            is_correct=is_correct,
            time_taken_seconds=item.time_taken_seconds
        ))
        
        # 4. Update user_vocabulary
        user_vocab = db.query(UserVocabulary).filter(
            UserVocabulary.user_id == current_user.id,
            UserVocabulary.vocabulary_id == vocab.id
        ).first()
        
        if user_vocab:
            user_vocab.times_encountered += 1
            if is_correct:
                user_vocab.times_correct += 1
            # Update mastery level
            accuracy = user_vocab.times_correct / user_vocab.times_encountered
            if accuracy >= 0.9 and user_vocab.times_encountered >= 3:
                user_vocab.mastery_level = "mastered"
            elif accuracy >= 0.6:
                user_vocab.mastery_level = "familiar"
            else:
                user_vocab.mastery_level = "learning"
        else:
            user_vocab = UserVocabulary(
                user_id=current_user.id,
                vocabulary_id=vocab.id,
                times_encountered=1,
                times_correct=1 if is_correct else 0,
                mastery_level="learning"
            )
            db.add(user_vocab)
    
    # 5. Update lesson_attempt
    total_words = len(request.results)
    accuracy_percent = (correct_count / total_words * 100) if total_words > 0 else 0
    
    attempt.vocabulary_correct = correct_count
    attempt.vocabulary_total = total_words
    attempt.overall_score = accuracy_percent
    
    db.commit()
    
    # 6. Return summary
    return VocabularyMatchingSummary(
        total_words=total_words,
        correct_count=correct_count,
        incorrect_count=total_words - correct_count,
        accuracy_percent=round(accuracy_percent, 1),
        total_time_seconds=total_time,
        results=results
    )


# ============================================================
# POST /vocabulary/save - Lưu từ vựng yêu thích
# ============================================================
@router.post("/save")
def save_vocabulary(
    request: UserVocabularySaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ⭐ LƯU TỪ VỰNG YÊU THÍCH
    
    Logic:
    - Toggle is_saved = True/False cho từ vựng
    
    Use case:
    - User muốn đánh dấu từ khó để ôn tập sau
    - Hiển thị trong "Từ vựng đã lưu"
    """
    user_vocab = db.query(UserVocabulary).filter(
        UserVocabulary.user_id == current_user.id,
        UserVocabulary.vocabulary_id == request.vocabulary_id
    ).first()
    
    if user_vocab:
        user_vocab.is_saved = request.is_saved
    else:
        user_vocab = UserVocabulary(
            user_id=current_user.id,
            vocabulary_id=request.vocabulary_id,
            is_saved=request.is_saved,
            times_encountered=0,
            times_correct=0,
            mastery_level="new"
        )
        db.add(user_vocab)
    
    db.commit()
    
    return {"message": "Đã lưu từ vựng" if request.is_saved else "Đã bỏ lưu từ vựng"}


# ============================================================
# GET /vocabulary/saved - Lấy danh sách từ vựng đã lưu
# ============================================================
@router.get("/saved", response_model=UserVocabularyListResponse)
def get_saved_vocabulary(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📚 LẤY DANH SÁCH TỪ VỰNG ĐÃ LƯU
    
    Use case:
    - Màn hình "Từ vựng của tôi"
    - Hiển thị từ đã lưu kèm mastery_level
    """
    query = db.query(UserVocabulary).filter(
        UserVocabulary.user_id == current_user.id,
        UserVocabulary.is_saved == True
    )
    
    total = query.count()
    offset = (page - 1) * page_size
    
    user_vocabs = query.offset(offset).limit(page_size).all()
    
    # Get vocabulary details
    vocab_ids = [uv.vocabulary_id for uv in user_vocabs]
    vocabularies = db.query(Vocabulary).filter(Vocabulary.id.in_(vocab_ids)).all()
    vocab_map = {v.id: v for v in vocabularies}
    
    items = []
    for uv in user_vocabs:
        vocab = vocab_map.get(uv.vocabulary_id)
        if vocab:
            items.append(VocabularyWithUserProgress(
                id=vocab.id,
                word=vocab.word,
                phonetic=vocab.phonetic,
                definition=vocab.definition,
                example_sentence=vocab.example_sentence,
                audio_url=vocab.audio_url,
                part_of_speech=vocab.part_of_speech,
                times_encountered=uv.times_encountered,
                times_correct=uv.times_correct,
                mastery_level=uv.mastery_level,
                is_saved=uv.is_saved
            ))
    
    return UserVocabularyListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


# ============================================================
# CRUD APIs - Quản lý Từ vựng (Admin)
# ============================================================

@router.get("", response_model=List[VocabularyResponse])
def get_vocabulary_list(
    search: Optional[str] = Query(None, description="Tìm theo word"),
    difficulty_level: Optional[str] = Query(None),
    part_of_speech: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    📋 LẤY DANH SÁCH TỪ VỰNG (Admin/Public)
    """
    query = db.query(Vocabulary)
    
    if search:
        query = query.filter(Vocabulary.word.ilike(f"%{search}%"))
    if difficulty_level:
        query = query.filter(Vocabulary.difficulty_level == difficulty_level)
    if part_of_speech:
        query = query.filter(Vocabulary.part_of_speech == part_of_speech)
    
    offset = (page - 1) * page_size
    vocabularies = query.order_by(Vocabulary.word).offset(offset).limit(page_size).all()
    
    return [VocabularyResponse.model_validate(v) for v in vocabularies]


@router.post("", response_model=VocabularyResponse, status_code=status.HTTP_201_CREATED)
def create_vocabulary(
    vocab_data: VocabularyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ➕ THÊM TỪ VỰNG MỚI (Admin)
    
    Use case:
    - Admin thêm từ "restaurant" với nghĩa, phiên âm, ví dụ
    """
    # Check duplicate
    existing = db.query(Vocabulary).filter(Vocabulary.word == vocab_data.word).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Từ '{vocab_data.word}' đã tồn tại"
        )
    
    new_vocab = Vocabulary(
        word=vocab_data.word,
        phonetic=vocab_data.phonetic,
        definition=vocab_data.definition,
        example_sentence=vocab_data.example_sentence,
        audio_url=vocab_data.audio_url,
        difficulty_level=vocab_data.difficulty_level,
        part_of_speech=vocab_data.part_of_speech
    )
    
    db.add(new_vocab)
    db.commit()
    db.refresh(new_vocab)
    
    return VocabularyResponse.model_validate(new_vocab)


@router.get("/{vocabulary_id}", response_model=VocabularyResponse)
def get_vocabulary(
    vocabulary_id: int,
    db: Session = Depends(get_db)
):
    """
    📖 LẤY CHI TIẾT 1 TỪ VỰNG
    """
    vocab = db.query(Vocabulary).filter(Vocabulary.id == vocabulary_id).first()
    if not vocab:
        raise HTTPException(status_code=404, detail="Từ vựng không tồn tại")
    
    return VocabularyResponse.model_validate(vocab)


@router.put("/{vocabulary_id}", response_model=VocabularyResponse)
def update_vocabulary(
    vocabulary_id: int,
    vocab_data: VocabularyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✏️ CẬP NHẬT TỪ VỰNG (Admin)
    """
    vocab = db.query(Vocabulary).filter(Vocabulary.id == vocabulary_id).first()
    if not vocab:
        raise HTTPException(status_code=404, detail="Từ vựng không tồn tại")
    
    update_data = vocab_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vocab, field, value)
    
    db.commit()
    db.refresh(vocab)
    
    return VocabularyResponse.model_validate(vocab)


@router.delete("/{vocabulary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vocabulary(
    vocabulary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🗑️ XÓA TỪ VỰNG (Admin)
    """
    vocab = db.query(Vocabulary).filter(Vocabulary.id == vocabulary_id).first()
    if not vocab:
        raise HTTPException(status_code=404, detail="Từ vựng không tồn tại")
    
    db.delete(vocab)
    db.commit()
    
    return None
