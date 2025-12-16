"""
Pronunciation Router - API endpoints cho Phát âm

=== GIẢI QUYẾT VẤN ĐỀ GÌ? ===
1. Nhận audio user ghi âm
2. Gọi Deepgram API để phân tích phát âm
3. Tính điểm 3 tiêu chí: pronunciation, intonation, stress
4. Trả về feedback chi tiết
5. Lưu kết quả vào DB

=== LOGIC HOẠT ĐỘNG ===
1. User nhấn mic, đọc "restaurant"
2. Frontend ghi audio (WebM format)
3. Frontend gửi audio_base64 lên server
4. Server gọi Deepgram API (via PronunciationService)
5. Server tính điểm, generate feedback
6. Trả về kết quả cho frontend hiển thị
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import base64
import os
from datetime import datetime

from app.database import get_db
from app.models import (
    LessonAttempt, PronunciationExercise, PronunciationAttempt
)
from app.models.user import User
from app.schemas.pronunciation import (
    PronunciationSubmitRequest, PronunciationSubmitBase64Request,
    PronunciationAttemptResponse, PronunciationScoreDetail,
    PronunciationFeedback, PronunciationLessonSummary
)
from app.core.dependencies import get_current_user
from app.config import settings

# Import service
from app.services.pronunciation_service import pronunciation_service, PronunciationService

router = APIRouter(
    prefix="/pronunciation",
    tags=["Pronunciation"]
)

# Directory để lưu audio tạm
UPLOAD_DIR = "uploads/audio/user_recordings"


# ============================================================
# POST /pronunciation/submit - Submit audio để đánh giá
# ============================================================
@router.post("/submit", response_model=PronunciationAttemptResponse)
async def submit_pronunciation(
    request: PronunciationSubmitBase64Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🎤 SUBMIT AUDIO PHÁT ÂM ĐỂ ĐÁNH GIÁ
    
    Logic:
    1. Decode audio base64 và lưu file tạm
    2. Gọi Deepgram API để speech-to-text + analysis
    3. Tính điểm 3 tiêu chí
    4. Generate feedback chi tiết
    5. Lưu kết quả vào pronunciation_attempts
    6. Cập nhật lesson_attempt scores
    
    Request body:
    {
        "lesson_attempt_id": 123,
        "exercise_id": 1,
        "audio_base64": "data:audio/webm;base64,GkXfo59...",
        "audio_format": "webm"
    }
    
    Response:
    - transcription: "restaurant" (user đọc được gì)
    - scores: {pronunciation: 85, intonation: 78, stress: 90}
    - feedback: {overall: "Tốt!", suggestions: [...]}
    """
    # 1. Verify lesson_attempt
    lesson_attempt = db.query(LessonAttempt).filter(
        LessonAttempt.id == request.lesson_attempt_id,
        LessonAttempt.user_id == current_user.id
    ).first()
    
    if not lesson_attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy phiên làm bài"
        )
    
    # 2. Get exercise info
    exercise = db.query(PronunciationExercise).filter(
        PronunciationExercise.id == request.exercise_id
    ).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy bài tập phát âm"
        )
    
    # 3. Count previous attempts for this exercise
    previous_attempts = db.query(PronunciationAttempt).filter(
        PronunciationAttempt.lesson_attempt_id == request.lesson_attempt_id,
        PronunciationAttempt.exercise_id == request.exercise_id
    ).count()
    
    attempt_number = previous_attempts + 1
    
    # 4. Process audio and get analysis
    # Save audio temporarily
    audio_url = save_audio_from_base64(
        request.audio_base64,
        current_user.id,
        request.exercise_id,
        request.audio_format
    )
    
    # 5. Call Deepgram API for analysis
    analysis_result = await analyze_pronunciation_with_deepgram(
        audio_url,
        exercise.content,
        request.audio_format
    )
    
    # 6. Calculate scores
    scores = calculate_pronunciation_scores(analysis_result, exercise.content)
    
    # 7. Generate feedback
    feedback = generate_pronunciation_feedback(scores, analysis_result, exercise.content)
    
    # 8. Save to database
    target_score = float(exercise.target_pronunciation_score) if exercise.target_pronunciation_score else 70.0
    is_passed = scores.accuracy_score >= target_score
    
    pronunciation_attempt = PronunciationAttempt(
        lesson_attempt_id=request.lesson_attempt_id,
        exercise_id=request.exercise_id,
        audio_url=audio_url,
        transcription=analysis_result.get("transcription", ""),
        pronunciation_score=scores.pronunciation_score,
        intonation_score=scores.intonation_score,
        stress_score=scores.stress_score,
        accuracy_score=scores.accuracy_score,
        detailed_feedback=feedback.model_dump(),
        suggestions=feedback.overall,
        attempt_number=attempt_number
    )
    
    db.add(pronunciation_attempt)
    
    # 9. Update lesson_attempt average scores
    update_lesson_attempt_pronunciation_scores(db, lesson_attempt)
    
    db.commit()
    db.refresh(pronunciation_attempt)
    
    # 10. Return response
    return PronunciationAttemptResponse(
        id=pronunciation_attempt.id,
        exercise_id=exercise.id,
        attempt_number=attempt_number,
        expected_content=exercise.content,
        transcription=analysis_result.get("transcription", ""),
        scores=scores,
        feedback=feedback,
        word_analysis=analysis_result.get("word_analysis"),
        is_passed=is_passed,
        target_score=target_score,
        created_at=pronunciation_attempt.created_at
    )


# ============================================================
# GET /pronunciation/summary/{lesson_attempt_id} - Tổng kết
# ============================================================
@router.get("/summary/{lesson_attempt_id}", response_model=PronunciationLessonSummary)
def get_pronunciation_summary(
    lesson_attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 TỔNG KẾT BÀI HỌC PHÁT ÂM
    
    Trả về điểm trung bình và kết quả từng bài tập
    """
    # Get lesson attempt
    lesson_attempt = db.query(LessonAttempt).filter(
        LessonAttempt.id == lesson_attempt_id,
        LessonAttempt.user_id == current_user.id
    ).first()
    
    if not lesson_attempt:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên làm bài")
    
    # Get all pronunciation attempts
    from app.models import Lesson
    lesson = db.query(Lesson).filter(Lesson.id == lesson_attempt.lesson_id).first()
    
    # Get exercises count
    total_exercises = db.query(PronunciationExercise).filter(
        PronunciationExercise.lesson_id == lesson_attempt.lesson_id
    ).count()
    
    # Get completed attempts (best score for each exercise)
    pronunciation_attempts = db.query(PronunciationAttempt).filter(
        PronunciationAttempt.lesson_attempt_id == lesson_attempt_id
    ).all()
    
    # Calculate averages
    if pronunciation_attempts:
        avg_pronunciation = sum(float(a.pronunciation_score or 0) for a in pronunciation_attempts) / len(pronunciation_attempts)
        avg_intonation = sum(float(a.intonation_score or 0) for a in pronunciation_attempts) / len(pronunciation_attempts)
        avg_stress = sum(float(a.stress_score or 0) for a in pronunciation_attempts) / len(pronunciation_attempts)
        overall_score = (avg_pronunciation + avg_intonation + avg_stress) / 3
    else:
        avg_pronunciation = avg_intonation = avg_stress = overall_score = 0
    
    passing_score = float(lesson.passing_score) if lesson and lesson.passing_score else 70.0
    
    # Build exercise results
    exercise_results = []
    for attempt in pronunciation_attempts:
        exercise = db.query(PronunciationExercise).filter(
            PronunciationExercise.id == attempt.exercise_id
        ).first()
        
        exercise_results.append(PronunciationAttemptResponse(
            id=attempt.id,
            exercise_id=attempt.exercise_id,
            attempt_number=attempt.attempt_number,
            expected_content=exercise.content if exercise else "",
            transcription=attempt.transcription,
            scores=PronunciationScoreDetail(
                pronunciation_score=float(attempt.pronunciation_score or 0),
                intonation_score=float(attempt.intonation_score or 0),
                stress_score=float(attempt.stress_score or 0),
                accuracy_score=float(attempt.accuracy_score or 0)
            ),
            feedback=PronunciationFeedback(
                overall=attempt.suggestions or "",
                pronunciation_feedback="",
                intonation_feedback="",
                stress_feedback="",
                suggestions=[]
            ),
            is_passed=float(attempt.accuracy_score or 0) >= passing_score,
            target_score=passing_score,
            created_at=attempt.created_at
        ))
    
    return PronunciationLessonSummary(
        lesson_id=lesson_attempt.lesson_id,
        lesson_title=lesson.title if lesson else "",
        total_exercises=total_exercises,
        completed_exercises=len(set(a.exercise_id for a in pronunciation_attempts)),
        average_pronunciation=round(avg_pronunciation, 1),
        average_intonation=round(avg_intonation, 1),
        average_stress=round(avg_stress, 1),
        overall_score=round(overall_score, 1),
        exercise_results=exercise_results,
        is_passed=overall_score >= passing_score,
        passing_score=passing_score,
        ai_summary_feedback=f"Điểm phát âm trung bình: {overall_score:.1f}/100"
    )


# ============================================================
# Helper Functions
# ============================================================

def save_audio_from_base64(audio_base64: str, user_id: int, exercise_id: int, audio_format: str) -> str:
    """Lưu audio từ base64 thành file"""
    
    # Tạo thư mục nếu chưa có
    user_folder = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    
    # Decode base64
    # Format: "data:audio/webm;base64,GkXfo59..."
    if "," in audio_base64:
        base64_part = audio_base64.split(",")[1]
        print(f"📦 Base64 data length: {len(base64_part)} chars")
        audio_data = base64.b64decode(base64_part)
    else:
        print(f"📦 Base64 data length (no header): {len(audio_base64)} chars")
        audio_data = base64.b64decode(audio_base64)
    
    print(f"📊 Decoded audio size: {len(audio_data)} bytes")
    
    # Validate audio size - ít nhất 1KB để có data hợp lệ
    if len(audio_data) < 1000:
        print(f"⚠️ WARNING: Audio file too small ({len(audio_data)} bytes). May be corrupt!")
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{exercise_id}.{audio_format}"
    file_path = os.path.join(user_folder, filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(audio_data)
    
    print(f"💾 Saved audio to: {file_path}")
    
    return f"/uploads/audio/user_recordings/{user_id}/{filename}"


async def analyze_pronunciation_with_deepgram(audio_url: str, expected_text: str, audio_format: str) -> dict:
    """
    Gọi Deepgram REST API trực tiếp (không cần SDK)
    
    Returns:
        {
            "transcription": "restaurant",
            "confidence": 0.95,
            "words": [...],
            "is_mock": False
        }
    """
    import httpx
    
    # Đọc file audio
    file_path = audio_url.replace("/uploads/", "uploads/")
    
    print(f"📁 Audio file path: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ Audio file not found: {file_path}")
        return mock_deepgram_response(expected_text, is_mock=True)
    
    # Check API key
    if not settings.DEEPGRAM_API_KEY:
        print("❌ DEEPGRAM_API_KEY not configured!")
        return mock_deepgram_response(expected_text, is_mock=True)
    
    print(f"🔑 Using Deepgram API Key: {settings.DEEPGRAM_API_KEY[:10]}...")
    
    try:
        # Đọc file audio
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()
        
        print(f"📊 Audio size: {len(audio_data)} bytes")
        
        # Xác định mimetype
        mimetype_map = {
            "webm": "audio/webm",
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "m4a": "audio/m4a",
            "ogg": "audio/ogg"
        }
        mimetype = mimetype_map.get(audio_format, "audio/webm")
        
        # Deepgram REST API endpoint
        url = "https://api.deepgram.com/v1/listen"
        
        # Query parameters
        params = {
            "model": settings.DEEPGRAM_MODEL or "nova-2",
            "language": settings.DEEPGRAM_LANGUAGE or "en-US",
            "punctuate": "true" if settings.DEEPGRAM_PUNCTUATE else "false",
            "smart_format": "true" if settings.DEEPGRAM_SMART_FORMAT else "false",
        }
        
        # Headers
        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": mimetype,
        }
        
        print(f"🎯 Calling Deepgram REST API...")
        print(f"   URL: {url}")
        print(f"   Model: {params['model']}")
        print(f"   Language: {params['language']}")
        
        # Call API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                params=params,
                headers=headers,
                content=audio_data
            )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Deepgram API error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return mock_deepgram_response(expected_text, is_mock=True)
        
        # Parse response
        data = response.json()
        
        # Extract results
        channels = data.get("results", {}).get("channels", [])
        if not channels:
            print("❌ No channels in response")
            return mock_deepgram_response(expected_text, is_mock=True)
        
        alternatives = channels[0].get("alternatives", [])
        if not alternatives:
            print("❌ No alternatives in response")
            return mock_deepgram_response(expected_text, is_mock=True)
        
        result = alternatives[0]
        transcription = result.get("transcript", "")
        confidence = result.get("confidence", 0)
        words = [
            {"word": w.get("word", ""), "confidence": w.get("confidence", 0)}
            for w in result.get("words", [])
        ]
        
        print(f"✅ Deepgram SUCCESS!")
        print(f"   📝 Transcription: '{transcription}'")
        print(f"   🎯 Expected: '{expected_text}'")
        print(f"   📊 Confidence: {confidence}")
        print(f"   📖 Words: {len(words)}")
        
        return {
            "transcription": transcription,
            "confidence": confidence,
            "words": words,
            "is_mock": False
        }
        
    except httpx.TimeoutException:
        print(f"❌ Deepgram API timeout!")
        return mock_deepgram_response(expected_text, is_mock=True)
    except Exception as e:
        print(f"❌ Deepgram error: {type(e).__name__}: {e}")
        return mock_deepgram_response(expected_text, is_mock=True)


def mock_deepgram_response(expected_text: str, is_mock: bool = True) -> dict:
    """
    Mock response khi không có Deepgram API
    QUAN TRỌNG: Trả về transcription có thể sai để test chính xác
    """
    import random
    
    print(f"⚠️ Using MOCK Deepgram response (is_mock={is_mock})")
    
    # Tạo transcription sai để test - KHÔNG giả sử đọc đúng nữa
    mock_errors = [
        "",  # Không nhận diện được
        "something else",  # Hoàn toàn sai
        expected_text[:len(expected_text)//2] if len(expected_text) > 4 else "",  # Chỉ đọc được nửa
    ]
    
    # 20% chance đọc đúng, 80% đọc sai (để test chính xác)
    if random.random() < 0.2:
        transcription = expected_text
        confidence = random.uniform(0.85, 0.98)
        print(f"   🎲 Mock: Giả sử đọc ĐÚNG")
    else:
        transcription = random.choice(mock_errors)
        confidence = random.uniform(0.3, 0.6)
        print(f"   🎲 Mock: Giả sử đọc SAI")
    
    print(f"   📝 Mock transcription: '{transcription}'")
    print(f"   📊 Mock confidence: {confidence}")
    
    return {
        "transcription": transcription,
        "confidence": confidence,
        "words": [],
        "is_mock": True
    }


def calculate_pronunciation_scores(analysis_result: dict, expected_text: str) -> PronunciationScoreDetail:
    """
    Tính điểm 3 tiêu chí từ kết quả Deepgram
    
    - pronunciation_score: Dựa trên confidence và transcription accuracy
    - intonation_score: Dựa trên variance trong pitch (simplified)
    - stress_score: Dựa trên word-level confidence
    """
    confidence = analysis_result.get("confidence", 0)
    transcription = analysis_result.get("transcription", "").lower().strip()
    expected = expected_text.lower().strip()
    is_mock = analysis_result.get("is_mock", False)
    
    print(f"📊 Calculating scores:")
    print(f"   📝 Transcription: '{transcription}'")
    print(f"   🎯 Expected: '{expected}'")
    print(f"   📊 Confidence: {confidence}")
    print(f"   🎭 Is Mock: {is_mock}")
    
    # Nếu không nhận diện được gì
    if not transcription:
        print(f"   ❌ Empty transcription -> All scores = 0")
        return PronunciationScoreDetail(
            pronunciation_score=0,
            intonation_score=0,
            stress_score=0,
            accuracy_score=0
        )
    
    # 1. Pronunciation score: So sánh transcription với expected
    similarity = calculate_text_similarity(transcription, expected)
    print(f"   📏 Text similarity: {similarity:.2f}")
    
    if transcription == expected:
        pronunciation_score = confidence * 100
        print(f"   ✅ Exact match! pronunciation_score = {pronunciation_score:.1f}")
    else:
        # Điểm = similarity * confidence * 100
        pronunciation_score = similarity * confidence * 100
        print(f"   ⚠️ Not exact match. pronunciation_score = {similarity:.2f} * {confidence:.2f} * 100 = {pronunciation_score:.1f}")
    
    # 2. Intonation score (simplified - based on confidence and similarity)
    if similarity >= 0.8:
        intonation_score = confidence * 100
    elif similarity >= 0.5:
        intonation_score = confidence * 80
    else:
        intonation_score = confidence * 50
    print(f"   🎵 Intonation score: {intonation_score:.1f}")
    
    # 3. Stress score (based on word-level analysis)
    words = analysis_result.get("words", [])
    if words and similarity >= 0.5:
        word_confidences = [w.get("confidence", confidence) for w in words]
        avg_word_confidence = sum(word_confidences) / len(word_confidences)
        stress_score = avg_word_confidence * 100
    else:
        stress_score = pronunciation_score * 0.9  # Giảm nếu không có word data
    print(f"   💪 Stress score: {stress_score:.1f}")
    
    # Accuracy = weighted average (pronunciation quan trọng nhất)
    accuracy_score = (pronunciation_score * 0.5 + intonation_score * 0.25 + stress_score * 0.25)
    print(f"   🎯 Accuracy score: {accuracy_score:.1f}")
    
    return PronunciationScoreDetail(
        pronunciation_score=round(max(0, min(100, pronunciation_score)), 1),
        intonation_score=round(max(0, min(100, intonation_score)), 1),
        stress_score=round(max(0, min(100, stress_score)), 1),
        accuracy_score=round(max(0, min(100, accuracy_score)), 1)
    )


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Tính độ tương tự giữa 2 đoạn text (0-1) bằng Levenshtein distance
    Chính xác hơn so với character-based
    """
    if not text1 or not text2:
        return 0.0
    
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    
    if text1 == text2:
        return 1.0
    
    # Levenshtein distance
    len1, len2 = len(text1), len(text2)
    
    # Nếu một chuỗi quá ngắn so với chuỗi kia
    if len1 == 0:
        return 0.0
    if len2 == 0:
        return 0.0
    
    # DP table
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    distance = dp[len1][len2]
    max_len = max(len1, len2)
    similarity = 1 - (distance / max_len)
    
    return max(0, similarity)


def generate_pronunciation_feedback(
    scores: PronunciationScoreDetail,
    analysis_result: dict,
    expected_text: str
) -> PronunciationFeedback:
    """Generate feedback chi tiết"""
    
    suggestions = []
    transcription = analysis_result.get("transcription", "")
    is_mock = analysis_result.get("is_mock", False)
    
    # Overall feedback based on accuracy
    if scores.accuracy_score >= 90:
        overall = "🌟 Xuất sắc! Phát âm rất chuẩn!"
    elif scores.accuracy_score >= 80:
        overall = "✅ Rất tốt! Phát âm gần như chuẩn."
    elif scores.accuracy_score >= 70:
        overall = "👍 Tốt! Phát âm khá ổn."
    elif scores.accuracy_score >= 50:
        overall = "💪 Cần cải thiện. Hãy nghe lại audio mẫu và thử lại."
    elif scores.accuracy_score >= 30:
        overall = "📚 Cần luyện tập thêm. Hãy đọc chậm và rõ ràng hơn."
    else:
        overall = "❌ Phát âm chưa đúng. Nghe lại mẫu và thử lại."
    
    # Thêm thông tin transcription nếu khác expected
    if transcription and transcription.lower().strip() != expected_text.lower().strip():
        overall += f"\n📝 Nhận diện được: \"{transcription}\""
        overall += f"\n🎯 Cần đọc: \"{expected_text}\""
    
    # Nếu dùng mock, thêm warning
    if is_mock:
        overall += "\n⚠️ (Kết quả từ mock - Deepgram chưa kết nối)"
    
    # Pronunciation feedback
    if scores.pronunciation_score >= 80:
        pronunciation_feedback = "Phát âm các âm tiết khá chuẩn."
    elif scores.pronunciation_score >= 50:
        pronunciation_feedback = "Một số âm tiết chưa rõ ràng."
        suggestions.append("Phát âm từng âm tiết rõ ràng hơn")
    else:
        pronunciation_feedback = "Cần chú ý phát âm rõ ràng từng âm tiết."
        suggestions.append(f"Luyện tập đọc chậm từ: {expected_text}")
    
    # Intonation feedback
    if scores.intonation_score >= 80:
        intonation_feedback = "Ngữ điệu tự nhiên, tốt!"
    elif scores.intonation_score >= 50:
        intonation_feedback = "Ngữ điệu cần tự nhiên hơn."
        suggestions.append("Chú ý ngữ điệu lên ở cuối câu hỏi")
    else:
        intonation_feedback = "Cần cải thiện ngữ điệu lên xuống."
    
    # Stress feedback
    if scores.stress_score >= 80:
        stress_feedback = "Trọng âm đúng vị trí!"
    elif scores.stress_score >= 50:
        stress_feedback = "Trọng âm cần chính xác hơn."
    else:
        stress_feedback = "Cần chú ý nhấn đúng trọng âm."
        suggestions.append(f"Từ '{expected_text}' cần nhấn đúng trọng âm")
    
    return PronunciationFeedback(
        overall=overall,
        pronunciation_feedback=pronunciation_feedback,
        intonation_feedback=intonation_feedback,
        stress_feedback=stress_feedback,
        suggestions=suggestions
    )


def update_lesson_attempt_pronunciation_scores(db: Session, lesson_attempt: LessonAttempt):
    """Cập nhật điểm phát âm trung bình cho lesson_attempt"""
    
    attempts = db.query(PronunciationAttempt).filter(
        PronunciationAttempt.lesson_attempt_id == lesson_attempt.id
    ).all()
    
    if attempts:
        lesson_attempt.pronunciation_score = sum(float(a.pronunciation_score or 0) for a in attempts) / len(attempts)
        lesson_attempt.intonation_score = sum(float(a.intonation_score or 0) for a in attempts) / len(attempts)
        lesson_attempt.stress_score = sum(float(a.stress_score or 0) for a in attempts) / len(attempts)
