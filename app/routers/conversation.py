"""
Conversation Router - API endpoints cho Hội thoại với AI (Groq/OpenAI-compatible)

=== GIẢI QUYẾT VẤN ĐỀ GÌ? ===
1. Bắt đầu conversation với AI theo scenario
2. Gửi/nhận tin nhắn realtime
3. AI đánh giá grammar, vocabulary của user
4. Tổng kết và chấm điểm cuối conversation

=== LOGIC HOẠT ĐỘNG ===
1. POST /conversation/start → AI gửi tin nhắn mở đầu
2. POST /conversation/message → User gửi tin, AI reply
3. Lặp lại bước 2 đến khi đủ min_turns
4. POST /conversation/end → Tổng kết, chấm điểm

=== AI API (Groq) ===
- Base URL: https://api.groq.com/openai/v1
- Model: llama-3.3-70b-versatile (hoặc model khác)
- Compatible với OpenAI API format
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from app.database import get_db
from app.models import (
    LessonAttempt, Lesson, ConversationTemplate, ConversationMessage,
    SpeakerType
)
from app.models.user import User
from app.schemas.conversation import (
    ConversationStartRequest, ConversationStartResponse,
    ConversationMessageCreate, ConversationMessageResponse,
    ConversationMessageWithAudio,
    AIConversationResponse, ConversationEndRequest,
    ConversationSummary, GrammarError, ConversationHistoryResponse
)
from app.core.dependencies import get_current_user
from app.config import settings

# Import services
from app.services.conversation_service import conversation_service, ConversationContext
from app.services.tts_service import tts_service

router = APIRouter(
    prefix="/conversation",
    tags=["Conversation"]
)


# ============================================================
# POST /conversation/chat - Chat đơn giản với AI (cho frontend cũ)
# ============================================================
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    topic_id: Optional[int] = None

class ChatResponse(BaseModel):
    reply: str
    audio_url: Optional[str] = None
    error: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def simple_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    💬 CHAT ĐƠN GIẢN VỚI AI
    
    Endpoint này cho phép gửi messages array trực tiếp đến AI
    và nhận response. Không cần lesson_attempt.
    
    Dùng cho:
    - Chat tự do với AI
    - Frontend cũ gọi /conversation/chat
    """
    import httpx
    
    print(f"💬 Simple chat - {len(request.messages)} messages from user {current_user.id}")
    
    try:
        # Build messages for Groq API
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        # Add system prompt if not exists
        if not any(m["role"] == "system" for m in messages):
            messages.insert(0, {
                "role": "system",
                "content": "You are a helpful English tutor. Help the user practice English conversation. Keep responses natural and encouraging. Correct grammar mistakes gently."
            })
        
        # Call Groq/OhMyGPT API
        groq_url = f"{settings.OHMYGPT_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OHMYGPT_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.OHMYGPT_MODEL or "llama-3.3-70b-versatile",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(groq_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            ai_reply = data["choices"][0]["message"]["content"]
            
            # Generate TTS audio
            audio_url = await tts_service.text_to_speech(text=ai_reply, voice="female_us")
            
            print(f"✅ AI reply: {ai_reply[:50]}...")
            return ChatResponse(reply=ai_reply, audio_url=audio_url)
        else:
            error_msg = f"Groq API error: {response.status_code}"
            print(f"❌ {error_msg}")
            return ChatResponse(
                reply="I'm sorry, I'm having trouble responding right now. Please try again.",
                error=error_msg
            )
            
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return ChatResponse(
            reply="I'm sorry, something went wrong. Please try again.",
            error=str(e)
        )


# ============================================================
# POST /conversation/start - Bắt đầu hội thoại
# ============================================================
@router.post("/start", response_model=ConversationStartResponse)
async def start_conversation(
    request: ConversationStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🚀 BẮT ĐẦU HỘI THOẠI VỚI AI
    
    Logic:
    1. Lấy lesson info và conversation template
    2. Tạo lesson_attempt mới
    3. Generate opening message từ AI dựa vào scenario
    4. Lưu opening message vào DB
    5. Trả về context và tin nhắn đầu tiên
    
    Use case:
    - User click "Bắt đầu hội thoại" ở Lesson Conversation
    - AI giới thiệu tình huống và bắt đầu cuộc trò chuyện
    
    Example:
    - ai_role: "Waiter at restaurant"
    - scenario: "You are ordering food..."
    - opening: "Good evening! Welcome to our restaurant. How can I help you?"
    """
    print(f"🚀 Starting conversation for lesson_id={request.lesson_id}, user_id={current_user.id}")
    
    try:
        # 1. Get lesson
        lesson = db.query(Lesson).filter(
            Lesson.id == request.lesson_id,
            Lesson.is_active == True
        ).first()
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Bài học không tồn tại")
        
        print(f"📚 Found lesson: {lesson.title}")
        
        # 2. Get conversation template
        template = db.query(ConversationTemplate).filter(
            ConversationTemplate.lesson_id == request.lesson_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Không tìm thấy template hội thoại")
        
        print(f"🎭 Found template: ai_role={template.ai_role}")
        
        # 3. Create lesson attempt
        previous_attempts = db.query(LessonAttempt).filter(
            LessonAttempt.user_id == current_user.id,
            LessonAttempt.lesson_id == request.lesson_id
        ).count()
        
        lesson_attempt = LessonAttempt(
            user_id=current_user.id,
            lesson_id=request.lesson_id,
            attempt_number=previous_attempts + 1,
            started_at=datetime.utcnow(),
            conversation_turns=0,
            is_completed=False
        )
        db.add(lesson_attempt)
        db.flush()  # Get ID
        
        print(f"📝 Created lesson_attempt: id={lesson_attempt.id}")
        
        # 4. Generate AI opening message
        opening_text = await generate_ai_opening(template)
        
        print(f"💬 Opening message: {opening_text[:50]}...")
        
        # 5. Generate TTS audio for opening message
        opening_audio_url = await tts_service.text_to_speech(text=opening_text, voice="female_us")
        print(f"🔊 Opening audio: {opening_audio_url}")
        
        # 6. Save opening message
        opening_message = ConversationMessage(
            lesson_attempt_id=lesson_attempt.id,
            message_order=1,
            speaker=SpeakerType.AI,
            message_text=opening_text,
            audio_url=opening_audio_url
        )
        db.add(opening_message)
        db.commit()
        db.refresh(opening_message)
        
        print(f"✅ Saved opening message: id={opening_message.id}")
        
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
        
        # 7. Return response
        return ConversationStartResponse(
            lesson_attempt_id=lesson_attempt.id,
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            ai_role=template.ai_role,
            scenario_context=template.scenario_context,
            starter_prompts=starter_prompts or [],
            suggested_topics=suggested_topics or [],
            min_turns=template.min_turns,
            max_duration_minutes=template.max_duration_minutes,
            opening_message=ConversationMessageResponse(
                id=opening_message.id,
                message_order=opening_message.message_order,
                speaker="ai",
                message_text=opening_message.message_text,
                audio_url=opening_audio_url,
                grammar_errors=None,
                vocabulary_used=None,
                sentiment=None,
                created_at=opening_message.created_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in start_conversation: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# POST /conversation/message-voice - Gửi tin nhắn bằng giọng nói
# ============================================================
@router.post("/message-voice", response_model=AIConversationResponse)
async def send_message_voice(
    request: ConversationMessageWithAudio,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🎤 GỬI TIN NHẮN BẰNG GIỌNG NÓI
    
    Flow:
    1. Nhận audio base64 từ frontend
    2. Gọi Deepgram API để Speech-to-Text
    3. Lưu tin nhắn user (text + audio)
    4. Phân tích grammar, vocabulary
    5. Gọi AI để generate reply
    6. Generate TTS cho AI reply
    7. Trả về text + audio cho cả 2
    
    Request:
    {
        "lesson_attempt_id": 123,
        "audio_base64": "data:audio/webm;base64,...",
        "audio_format": "webm"
    }
    """
    # 1. Verify lesson_attempt
    lesson_attempt = db.query(LessonAttempt).filter(
        LessonAttempt.id == request.lesson_attempt_id,
        LessonAttempt.user_id == current_user.id
    ).first()
    
    if not lesson_attempt:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hội thoại")
    
    if lesson_attempt.is_completed:
        raise HTTPException(status_code=400, detail="Hội thoại đã kết thúc")
    
    # 2. Get conversation template
    template = db.query(ConversationTemplate).filter(
        ConversationTemplate.lesson_id == lesson_attempt.lesson_id
    ).first()
    
    # 3. Get message history
    history = db.query(ConversationMessage).filter(
        ConversationMessage.lesson_attempt_id == request.lesson_attempt_id
    ).order_by(ConversationMessage.message_order).all()
    
    current_order = len(history) + 1
    
    # 4. Speech-to-Text: Convert audio to text
    user_audio_url, transcription = await speech_to_text(
        request.audio_base64,
        current_user.id,
        request.audio_format
    )
    
    if not transcription:
        raise HTTPException(status_code=400, detail="Không nhận diện được giọng nói")
    
    print(f"🎤 User said: '{transcription}'")
    
    # 5. Analyze user message
    analysis = analyze_user_message(transcription)
    
    # 6. Save user message with audio
    user_message = ConversationMessage(
        lesson_attempt_id=request.lesson_attempt_id,
        message_order=current_order,
        speaker=SpeakerType.USER,
        message_text=transcription,
        audio_url=user_audio_url,
        grammar_errors=analysis.get("grammar_errors"),
        vocabulary_used=analysis.get("vocabulary_used"),
        sentiment=analysis.get("sentiment")
    )
    db.add(user_message)
    
    # 7. Generate AI reply
    ai_reply_text = await generate_ai_reply(
        template=template,
        history=history,
        user_message=transcription
    )
    
    # 8. Generate TTS for AI reply
    ai_audio_url = await tts_service.text_to_speech(text=ai_reply_text, voice="female_us")
    print(f"🔊 AI reply audio (voice): {ai_audio_url}")
    
    # 9. Save AI message
    ai_message = ConversationMessage(
        lesson_attempt_id=request.lesson_attempt_id,
        message_order=current_order + 1,
        speaker=SpeakerType.AI,
        message_text=ai_reply_text,
        audio_url=ai_audio_url
    )
    db.add(ai_message)
    
    # 10. Update conversation turns
    lesson_attempt.conversation_turns = (current_order + 1) // 2
    
    db.commit()
    db.refresh(ai_message)
    db.refresh(user_message)
    
    # 11. Generate suggested replies
    suggested_replies = generate_suggested_replies(template, ai_reply_text)
    
    # 12. Check if can end
    can_end = lesson_attempt.conversation_turns >= template.min_turns
    
    return AIConversationResponse(
        ai_message=ConversationMessageResponse(
            id=ai_message.id,
            message_order=ai_message.message_order,
            speaker="ai",
            message_text=ai_message.message_text,
            audio_url=ai_audio_url,
            grammar_errors=None,
            vocabulary_used=None,
            sentiment=None,
            created_at=ai_message.created_at
        ),
        user_message_analysis=analysis,
        user_transcription=transcription,
        user_audio_url=user_audio_url,
        suggested_replies=suggested_replies,
        current_turn=lesson_attempt.conversation_turns,
        min_turns=template.min_turns,
        can_end=can_end
    )


# ============================================================
# POST /conversation/message - Gửi tin nhắn
# ============================================================
@router.post("/message", response_model=AIConversationResponse)
async def send_message(
    request: ConversationMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    💬 GỬI TIN NHẮN TRONG HỘI THOẠI
    
    Logic:
    1. Lưu tin nhắn của user
    2. Phân tích grammar, vocabulary của user
    3. Gọi AI (Groq) để generate reply
    4. Lưu tin nhắn AI
    5. Trả về AI reply + phân tích user message
    
    Use case:
    - User gõ "I'd like to order a pizza"
    - AI phân tích grammar (OK), vocabulary (order, pizza)
    - AI reply: "Great choice! What size would you like?"
    
    Request:
    {
        "lesson_attempt_id": 123,
        "message_text": "I'd like to order a pizza"
    }
    """
    # 1. Verify lesson_attempt
    lesson_attempt = db.query(LessonAttempt).filter(
        LessonAttempt.id == request.lesson_attempt_id,
        LessonAttempt.user_id == current_user.id
    ).first()
    
    if not lesson_attempt:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hội thoại")
    
    if lesson_attempt.is_completed:
        raise HTTPException(status_code=400, detail="Hội thoại đã kết thúc")
    
    # 2. Get conversation template
    template = db.query(ConversationTemplate).filter(
        ConversationTemplate.lesson_id == lesson_attempt.lesson_id
    ).first()
    
    # 3. Get message history
    history = db.query(ConversationMessage).filter(
        ConversationMessage.lesson_attempt_id == request.lesson_attempt_id
    ).order_by(ConversationMessage.message_order).all()
    
    current_order = len(history) + 1
    
    # 4. Analyze user message
    analysis = analyze_user_message(request.message_text)
    
    # 5. Save user message
    user_message = ConversationMessage(
        lesson_attempt_id=request.lesson_attempt_id,
        message_order=current_order,
        speaker=SpeakerType.USER,
        message_text=request.message_text,
        audio_url=request.audio_url if hasattr(request, 'audio_url') else None,
        grammar_errors=analysis.get("grammar_errors"),
        vocabulary_used=analysis.get("vocabulary_used"),
        sentiment=analysis.get("sentiment")
    )
    db.add(user_message)
    
    # 6. Generate AI reply
    ai_reply_text = await generate_ai_reply(
        template=template,
        history=history,
        user_message=request.message_text
    )
    
    # 7. Generate TTS audio for AI reply
    ai_audio_url = await tts_service.text_to_speech(text=ai_reply_text, voice="female_us")
    print(f"🔊 AI reply audio (text): {ai_audio_url}")
    
    # 8. Save AI message
    ai_message = ConversationMessage(
        lesson_attempt_id=request.lesson_attempt_id,
        message_order=current_order + 1,
        speaker=SpeakerType.AI,
        message_text=ai_reply_text,
        audio_url=ai_audio_url
    )
    db.add(ai_message)
    
    # 9. Update conversation turns
    lesson_attempt.conversation_turns = (current_order + 1) // 2  # Count pairs
    
    db.commit()
    db.refresh(ai_message)
    
    # 10. Generate suggested replies
    suggested_replies = generate_suggested_replies(template, ai_reply_text)
    
    # 11. Check if can end
    can_end = lesson_attempt.conversation_turns >= template.min_turns
    
    return AIConversationResponse(
        ai_message=ConversationMessageResponse(
            id=ai_message.id,
            message_order=ai_message.message_order,
            speaker="ai",
            message_text=ai_message.message_text,
            audio_url=ai_audio_url,
            grammar_errors=None,
            vocabulary_used=None,
            sentiment=None,
            created_at=ai_message.created_at
        ),
        user_message_analysis=analysis,
        suggested_replies=suggested_replies,
        current_turn=lesson_attempt.conversation_turns,
        min_turns=template.min_turns,
        can_end=can_end
    )


# ============================================================
# POST /conversation/end - Kết thúc hội thoại
# ============================================================
@router.post("/end", response_model=ConversationSummary)
async def end_conversation(
    request: ConversationEndRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🏁 KẾT THÚC VÀ TỔNG KẾT HỘI THOẠI
    
    Logic:
    1. Lấy tất cả tin nhắn của conversation
    2. Tổng hợp grammar errors, vocabulary used
    3. Tính điểm fluency, grammar, vocabulary
    4. Generate AI feedback tổng hợp
    5. Cập nhật lesson_attempt scores
    
    Returns:
    - total_turns: 6
    - scores: {fluency: 82, grammar: 75, vocabulary: 88}
    - grammar_errors_summary: [...]
    - ai_feedback: "Great job! You used appropriate vocabulary..."
    """
    # 1. Get lesson_attempt
    lesson_attempt = db.query(LessonAttempt).filter(
        LessonAttempt.id == request.lesson_attempt_id,
        LessonAttempt.user_id == current_user.id
    ).first()
    
    if not lesson_attempt:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hội thoại")
    
    # 2. Get lesson and template
    lesson = db.query(Lesson).filter(Lesson.id == lesson_attempt.lesson_id).first()
    template = db.query(ConversationTemplate).filter(
        ConversationTemplate.lesson_id == lesson_attempt.lesson_id
    ).first()
    
    # 3. Get all messages
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.lesson_attempt_id == request.lesson_attempt_id
    ).order_by(ConversationMessage.message_order).all()
    
    # 4. Analyze conversation
    user_messages = [m for m in messages if m.speaker == SpeakerType.USER]
    ai_messages = [m for m in messages if m.speaker == SpeakerType.AI]
    
    # Collect all grammar errors
    all_grammar_errors = []
    all_vocabulary = set()
    
    for msg in user_messages:
        if msg.grammar_errors:
            all_grammar_errors.extend(msg.grammar_errors)
        if msg.vocabulary_used:
            all_vocabulary.update(msg.vocabulary_used)
    
    # 5. Calculate scores
    total_user_words = sum(len(m.message_text.split()) for m in user_messages)
    error_rate = len(all_grammar_errors) / max(total_user_words, 1)
    
    fluency_score = min(90 - (error_rate * 50), 100)  # Fewer errors = higher fluency
    grammar_score = max(100 - (len(all_grammar_errors) * 10), 0)
    vocabulary_score = min(len(all_vocabulary) * 5, 100)  # More vocab = higher score
    
    overall_score = (fluency_score + grammar_score + vocabulary_score) / 3
    
    # 6. Update lesson_attempt
    lesson_attempt.completed_at = datetime.utcnow()
    lesson_attempt.duration_seconds = int((lesson_attempt.completed_at - lesson_attempt.started_at).total_seconds())
    lesson_attempt.fluency_score = fluency_score
    lesson_attempt.grammar_score = grammar_score
    lesson_attempt.overall_score = overall_score
    lesson_attempt.is_completed = True
    
    passing_score = float(lesson.passing_score) if lesson and lesson.passing_score else 70.0
    lesson_attempt.is_passed = overall_score >= passing_score
    
    # 7. Generate AI feedback
    ai_feedback = generate_conversation_feedback(
        fluency_score, grammar_score, vocabulary_score,
        all_grammar_errors, list(all_vocabulary)
    )
    
    lesson_attempt.ai_feedback = ai_feedback
    
    db.commit()
    
    # 8. Build response
    grammar_errors_list = [
        GrammarError(
            original=e.get("original", ""),
            corrected=e.get("corrected", ""),
            error_type=e.get("error_type", "unknown"),
            explanation=e.get("explanation", "")
        ) for e in all_grammar_errors[:10]  # Limit to 10
    ]
    
    messages_response = [
        ConversationMessageResponse(
            id=m.id,
            message_order=m.message_order,
            speaker=m.speaker.value if hasattr(m.speaker, 'value') else m.speaker,
            message_text=m.message_text,
            audio_url=m.audio_url,
            grammar_errors=[GrammarError(**e) for e in (m.grammar_errors or [])] if m.grammar_errors else None,
            vocabulary_used=m.vocabulary_used,
            sentiment=m.sentiment,
            created_at=m.created_at
        ) for m in messages
    ]
    
    return ConversationSummary(
        lesson_attempt_id=lesson_attempt.id,
        lesson_id=lesson_attempt.lesson_id,
        lesson_title=lesson.title if lesson else "",
        total_turns=lesson_attempt.conversation_turns,
        duration_seconds=lesson_attempt.duration_seconds,
        total_user_messages=len(user_messages),
        total_ai_messages=len(ai_messages),
        fluency_score=round(fluency_score, 1),
        grammar_score=round(grammar_score, 1),
        vocabulary_score=round(vocabulary_score, 1),
        overall_score=round(overall_score, 1),
        grammar_errors_summary=grammar_errors_list,
        vocabulary_used=list(all_vocabulary),
        new_vocabulary_learned=[],  # TODO: Compare with user's known vocabulary
        strengths=get_strengths(fluency_score, grammar_score, vocabulary_score),
        areas_to_improve=get_areas_to_improve(fluency_score, grammar_score, vocabulary_score),
        ai_feedback=ai_feedback,
        is_passed=lesson_attempt.is_passed,
        passing_score=passing_score,
        messages=messages_response
    )


# ============================================================
# GET /conversation/history/{attempt_id} - Xem lại hội thoại
# ============================================================
@router.get("/history/{attempt_id}", response_model=ConversationHistoryResponse)
def get_conversation_history(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📜 XEM LẠI LỊCH SỬ HỘI THOẠI
    """
    lesson_attempt = db.query(LessonAttempt).filter(
        LessonAttempt.id == attempt_id,
        LessonAttempt.user_id == current_user.id
    ).first()
    
    if not lesson_attempt:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    
    lesson = db.query(Lesson).filter(Lesson.id == lesson_attempt.lesson_id).first()
    template = db.query(ConversationTemplate).filter(
        ConversationTemplate.lesson_id == lesson_attempt.lesson_id
    ).first()
    
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.lesson_attempt_id == attempt_id
    ).order_by(ConversationMessage.message_order).all()
    
    messages_response = [
        ConversationMessageResponse(
            id=m.id,
            message_order=m.message_order,
            speaker=m.speaker.value if hasattr(m.speaker, 'value') else m.speaker,
            message_text=m.message_text,
            audio_url=m.audio_url,
            grammar_errors=None,
            vocabulary_used=m.vocabulary_used,
            sentiment=m.sentiment,
            created_at=m.created_at
        ) for m in messages
    ]
    
    return ConversationHistoryResponse(
        lesson_attempt_id=attempt_id,
        lesson_title=lesson.title if lesson else "",
        ai_role=template.ai_role if template else "",
        scenario_context=template.scenario_context if template else "",
        started_at=lesson_attempt.started_at,
        completed_at=lesson_attempt.completed_at,
        duration_seconds=lesson_attempt.duration_seconds,
        overall_score=float(lesson_attempt.overall_score) if lesson_attempt.overall_score else None,
        is_passed=lesson_attempt.is_passed,
        messages=messages_response
    )


# ============================================================
# Helper Functions
# ============================================================

async def generate_ai_opening(template: ConversationTemplate) -> str:
    """Generate tin nhắn mở đầu từ AI (Groq/OpenAI-compatible)"""
    
    print(f"🎭 Generating AI opening for role: {template.ai_role}")
    print(f"📍 API Key: {settings.OHMYGPT_API_KEY[:20] if settings.OHMYGPT_API_KEY else 'NOT SET'}...")
    print(f"🌐 Base URL: {settings.OHMYGPT_BASE_URL}")
    print(f"🤖 Model: {settings.OHMYGPT_MODEL}")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=settings.OHMYGPT_API_KEY,
            base_url=settings.OHMYGPT_BASE_URL
        )
        
        system_prompt = f"""You are playing the role of: {template.ai_role}
Scenario: {template.scenario_context}

Generate a friendly opening message to start the conversation.
Keep it simple, 1-2 sentences, appropriate for English learners.
Respond in English only."""
        
        print(f"📝 Calling Groq API...")
        
        response = client.chat.completions.create(
            model=settings.OHMYGPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Start the conversation"}
            ],
            temperature=settings.OHMYGPT_TEMPERATURE,
            max_tokens=100
        )
        
        result = response.choices[0].message.content
        print(f"✅ Groq Response: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Groq API Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Fallback opening
        return f"Hello! I'm your {template.ai_role}. How can I help you today?"


async def generate_ai_reply(template: ConversationTemplate, history: list, user_message: str) -> str:
    """Generate AI reply dựa vào context và history (Groq/OpenAI-compatible)"""
    
    print(f"💬 Generating AI reply for message: {user_message[:50]}...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=settings.OHMYGPT_API_KEY,
            base_url=settings.OHMYGPT_BASE_URL
        )
        
        system_prompt = f"""You are playing the role of: {template.ai_role}
Scenario: {template.scenario_context}

Guidelines:
- Keep responses simple and clear (1-3 sentences)
- Use vocabulary appropriate for English learners
- Be encouraging and helpful
- Stay in character
- Ask follow-up questions to keep the conversation going
- Respond in English only"""
        
        # Build messages from history
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in history:
            role = "assistant" if msg.speaker == SpeakerType.AI else "user"
            messages.append({"role": role, "content": msg.message_text})
        
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model=settings.OHMYGPT_MODEL,
            messages=messages,
            temperature=settings.OHMYGPT_TEMPERATURE,
            max_tokens=settings.OHMYGPT_MAX_TOKENS
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"AI Error: {e}")
        return "That's interesting! Could you tell me more?"


def analyze_user_message(message: str) -> dict:
    """Phân tích grammar và vocabulary trong tin nhắn user"""
    
    # Simple analysis (in production, use NLP library)
    words = message.lower().split()
    
    # Extract vocabulary (simple approach)
    vocabulary_used = [w for w in words if len(w) > 3 and w.isalpha()]
    
    # Simple grammar check (in production, use grammar checker)
    grammar_errors = []
    
    # Check common errors
    if " i " in message.lower() and "I" not in message:
        grammar_errors.append({
            "original": message,
            "corrected": message.replace(" i ", " I "),
            "error_type": "capitalization",
            "explanation": "'I' should always be capitalized"
        })
    
    # Sentiment (simple)
    positive_words = ["good", "great", "nice", "love", "thanks", "please", "happy"]
    negative_words = ["bad", "hate", "sorry", "sad", "angry"]
    
    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)
    
    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "grammar_errors": grammar_errors,
        "vocabulary_used": list(set(vocabulary_used)),
        "sentiment": sentiment
    }


def generate_suggested_replies(template: ConversationTemplate, ai_message: str) -> List[str]:
    """Generate gợi ý câu trả lời cho user"""
    
    # Simple suggestions based on context
    suggestions = [
        "Yes, please.",
        "That sounds good.",
        "Could you tell me more?",
        "I'm not sure, what do you recommend?"
    ]
    
    return suggestions[:3]


def generate_conversation_feedback(
    fluency: float, grammar: float, vocabulary: float,
    errors: list, vocab_used: list
) -> str:
    """Generate feedback tổng hợp cho conversation"""
    
    overall = (fluency + grammar + vocabulary) / 3
    
    if overall >= 85:
        feedback = "🌟 Excellent conversation! "
    elif overall >= 70:
        feedback = "✅ Good job! "
    else:
        feedback = "💪 Keep practicing! "
    
    # Add specific feedback
    if grammar >= 80:
        feedback += "Your grammar was good. "
    else:
        feedback += f"Watch out for grammar - you had {len(errors)} errors. "
    
    if vocabulary >= 80:
        feedback += f"Great vocabulary usage with {len(vocab_used)} different words! "
    else:
        feedback += "Try to use more varied vocabulary. "
    
    return feedback


def get_strengths(fluency: float, grammar: float, vocabulary: float) -> List[str]:
    """Get list of strengths"""
    strengths = []
    if fluency >= 80:
        strengths.append("Fluent conversation flow")
    if grammar >= 80:
        strengths.append("Good grammar usage")
    if vocabulary >= 80:
        strengths.append("Rich vocabulary")
    return strengths if strengths else ["Completed the conversation"]


def get_areas_to_improve(fluency: float, grammar: float, vocabulary: float) -> List[str]:
    """Get list of areas to improve"""
    areas = []
    if fluency < 70:
        areas.append("Practice speaking more naturally")
    if grammar < 70:
        areas.append("Review grammar rules")
    if vocabulary < 70:
        areas.append("Learn more vocabulary related to this topic")
    return areas if areas else ["Keep up the good work!"]

# ============================================================
# Speech-to-Text Helper Function
# ============================================================
import os
import base64
import uuid

STT_UPLOAD_DIR = "uploads/audio/conversation"


# ============================================================
# POST /conversation/suggest-reply - Gợi ý câu trả lời
# ============================================================
class SuggestReplyRequest(BaseModel):
    ai_message: str  # Tin nhắn gần nhất của AI
    topic: Optional[str] = None  # Chủ đề đang nói
    conversation_history: Optional[List[ChatMessage]] = None  # Lịch sử chat

class SuggestReplyResponse(BaseModel):
    suggestions: List[str]  # Các gợi ý câu trả lời
    example_sentence: str  # Mẫu câu đầy đủ
    explanation: Optional[str] = None  # Giải thích cách dùng

@router.post("/suggest-reply", response_model=SuggestReplyResponse)
async def suggest_reply(
    request: SuggestReplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    💡 GỢI Ý CÂU TRẢ LỜI CHO USER
    
    Khi user không biết trả lời gì, AI sẽ gợi ý:
    - 3-4 cách trả lời ngắn gọn
    - 1 mẫu câu đầy đủ làm ví dụ
    - Giải thích ngắn về cách dùng
    """
    print(f"💡 Generating reply suggestions for: {request.ai_message[:50]}...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=settings.OHMYGPT_API_KEY,
            base_url=settings.OHMYGPT_BASE_URL
        )
        
        topic_context = f"Topic: {request.topic}" if request.topic else ""
        
        system_prompt = f"""You are an English tutor helping a student respond in a conversation.
{topic_context}

The AI assistant just said: "{request.ai_message}"

Generate helpful response suggestions for the student:
1. Provide 4 SHORT response options (3-8 words each)
2. Provide 1 FULL example sentence (complete response)
3. Brief explanation in Vietnamese about when to use these responses

Respond in this exact JSON format:
{{
    "suggestions": ["Short reply 1", "Short reply 2", "Short reply 3", "Short reply 4"],
    "example_sentence": "A complete example response sentence that the student can say",
    "explanation": "Giải thích ngắn gọn bằng tiếng Việt về cách dùng các câu trả lời này"
}}"""
        
        response = client.chat.completions.create(
            model=settings.OHMYGPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate suggestions"}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        import json
        result_text = response.choices[0].message.content
        
        # Parse JSON response
        try:
            # Clean up response if needed
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            
            return SuggestReplyResponse(
                suggestions=result.get("suggestions", ["Yes", "No", "I'm not sure", "Can you repeat?"]),
                example_sentence=result.get("example_sentence", "I would like to know more about that."),
                explanation=result.get("explanation", "Bạn có thể chọn một trong các câu trên để trả lời.")
            )
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return SuggestReplyResponse(
                suggestions=["Yes, please.", "No, thank you.", "I'm not sure.", "Can you explain more?"],
                example_sentence="That sounds interesting, could you tell me more about it?",
                explanation="Đây là các câu trả lời thông dụng bạn có thể sử dụng."
            )
            
    except Exception as e:
        print(f"❌ Suggest reply error: {e}")
        return SuggestReplyResponse(
            suggestions=["Yes", "No", "Maybe", "I don't know"],
            example_sentence="I'm not sure, could you help me?",
            explanation="Lỗi khi tạo gợi ý. Hãy thử lại sau."
        )


# ============================================================
# POST /conversation/evaluate-message - Đánh giá tin nhắn user
# ============================================================
class EvaluateMessageRequest(BaseModel):
    user_text: str  # Nội dung user nói/gõ
    user_audio_url: Optional[str] = None  # URL audio của user (nếu có)
    ai_previous_message: Optional[str] = None  # Tin nhắn AI trước đó
    topic: Optional[str] = None

class GrammarCorrection(BaseModel):
    original: str
    corrected: str
    error_type: str  # grammar, spelling, word_choice, etc.
    explanation: str  # Giải thích bằng tiếng Việt

class PronunciationFeedback(BaseModel):
    overall_score: float  # 1-10
    clarity_score: float  # Độ rõ ràng
    fluency_score: float  # Độ trôi chảy
    accuracy_score: float  # Độ chính xác
    feedback: str  # Nhận xét bằng tiếng Việt
    words_to_practice: List[str]  # Từ cần luyện phát âm

class EvaluateMessageResponse(BaseModel):
    original_text: str
    corrected_text: str
    is_correct: bool  # Câu có đúng ngữ pháp không
    grammar_corrections: List[GrammarCorrection]
    pronunciation: Optional[PronunciationFeedback] = None
    relevance_score: float  # Điểm liên quan đến context (1-10)
    overall_feedback: str  # Nhận xét tổng hợp
    encouragement: str  # Lời động viên

@router.post("/evaluate-message", response_model=EvaluateMessageResponse)
async def evaluate_message(
    request: EvaluateMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📝 ĐÁNH GIÁ TIN NHẮN CỦA USER
    
    Phân tích:
    - Ngữ pháp: Sửa lỗi grammar
    - Phát âm: Đánh giá pronunciation (nếu có audio)
    - Liên quan: Câu trả lời có phù hợp với context không
    - Feedback: Nhận xét và động viên
    """
    print(f"📝 Evaluating user message: {request.user_text[:50]}...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=settings.OHMYGPT_API_KEY,
            base_url=settings.OHMYGPT_BASE_URL
        )
        
        context = f"Topic: {request.topic}\nAI said: {request.ai_previous_message}" if request.ai_previous_message else ""
        
        system_prompt = f"""You are an English tutor evaluating a student's response.

{context}

The student said: "{request.user_text}"

Analyze the student's response and provide feedback:
1. Check grammar and suggest corrections
2. Rate relevance to the conversation (1-10)
3. Provide encouraging feedback in Vietnamese

Respond in this exact JSON format:
{{
    "corrected_text": "The grammatically correct version of student's text",
    "is_correct": true/false,
    "grammar_corrections": [
        {{
            "original": "wrong part",
            "corrected": "correct version",
            "error_type": "grammar/spelling/word_choice",
            "explanation": "Giải thích bằng tiếng Việt"
        }}
    ],
    "relevance_score": 8.5,
    "overall_feedback": "Nhận xét tổng hợp bằng tiếng Việt",
    "encouragement": "Lời động viên bằng tiếng Việt"
}}"""
        
        response = client.chat.completions.create(
            model=settings.OHMYGPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Evaluate the student's response"}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        import json
        result_text = response.choices[0].message.content
        
        try:
            # Clean up response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            
            # Parse grammar corrections
            corrections = []
            for c in result.get("grammar_corrections", []):
                corrections.append(GrammarCorrection(
                    original=c.get("original", ""),
                    corrected=c.get("corrected", ""),
                    error_type=c.get("error_type", "grammar"),
                    explanation=c.get("explanation", "")
                ))
            
            # Pronunciation feedback (nếu có audio)
            pronunciation = None
            if request.user_audio_url:
                # Đánh giá pronunciation dựa trên text và audio
                pronunciation = await evaluate_pronunciation(
                    request.user_text, 
                    request.user_audio_url
                )
            
            return EvaluateMessageResponse(
                original_text=request.user_text,
                corrected_text=result.get("corrected_text", request.user_text),
                is_correct=result.get("is_correct", True),
                grammar_corrections=corrections,
                pronunciation=pronunciation,
                relevance_score=float(result.get("relevance_score", 8.0)),
                overall_feedback=result.get("overall_feedback", "Câu trả lời tốt!"),
                encouragement=result.get("encouragement", "Cố gắng lên! 💪")
            )
            
        except json.JSONDecodeError:
            return EvaluateMessageResponse(
                original_text=request.user_text,
                corrected_text=request.user_text,
                is_correct=True,
                grammar_corrections=[],
                pronunciation=None,
                relevance_score=7.0,
                overall_feedback="Câu trả lời của bạn ổn!",
                encouragement="Tiếp tục phát huy nhé! 👍"
            )
            
    except Exception as e:
        print(f"❌ Evaluate message error: {e}")
        return EvaluateMessageResponse(
            original_text=request.user_text,
            corrected_text=request.user_text,
            is_correct=True,
            grammar_corrections=[],
            pronunciation=None,
            relevance_score=7.0,
            overall_feedback="Không thể đánh giá lúc này.",
            encouragement="Hãy tiếp tục luyện tập! 💪"
        )


async def evaluate_pronunciation(text: str, audio_url: str) -> PronunciationFeedback:
    """Đánh giá phát âm từ audio"""
    # TODO: Integrate với service đánh giá phát âm thực sự
    # Hiện tại trả về mock data
    
    words = text.split()
    words_to_practice = words[:3] if len(words) > 3 else words
    
    return PronunciationFeedback(
        overall_score=7.5,
        clarity_score=7.0,
        fluency_score=8.0,
        accuracy_score=7.5,
        feedback="Phát âm của bạn khá tốt! Cần chú ý nhấn âm đúng vị trí.",
        words_to_practice=words_to_practice
    )


# ============================================================
# POST /conversation/end-simple - Kết thúc và đánh giá (không cần lesson_attempt)
# ============================================================
class SimpleConversationMessage(BaseModel):
    role: str  # "user" or "ai"
    content: str
    audio_url: Optional[str] = None

class EndSimpleRequest(BaseModel):
    messages: List[SimpleConversationMessage]  # Toàn bộ lịch sử chat
    topic: Optional[str] = None
    topic_id: Optional[int] = None

class ConversationScore(BaseModel):
    fluency: float  # Độ trôi chảy (1-10)
    grammar: float  # Ngữ pháp (1-10)
    vocabulary: float  # Từ vựng (1-10)
    relevance: float  # Liên quan đến chủ đề (1-10)
    overall: float  # Điểm tổng (1-10)

class EndSimpleResponse(BaseModel):
    total_turns: int
    user_messages_count: int
    ai_messages_count: int
    scores: ConversationScore
    grammar_errors: List[GrammarCorrection]
    vocabulary_used: List[str]
    strengths: List[str]  # Điểm mạnh
    areas_to_improve: List[str]  # Cần cải thiện
    overall_feedback: str  # Nhận xét tổng hợp
    tips: List[str]  # Mẹo luyện tập

@router.post("/end-simple", response_model=EndSimpleResponse)
async def end_simple_conversation(
    request: EndSimpleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🏁 KẾT THÚC VÀ ĐÁNH GIÁ HỘI THOẠI (SIMPLE VERSION)
    
    Dùng cho frontend chat đơn giản không cần lesson_attempt.
    Phân tích toàn bộ conversation và trả về đánh giá tổng hợp.
    """
    print(f"🏁 Ending simple conversation with {len(request.messages)} messages")
    
    user_messages = [m for m in request.messages if m.role == "user"]
    ai_messages = [m for m in request.messages if m.role == "ai"]
    
    # Collect all user text
    user_text_all = " ".join([m.content for m in user_messages])
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=settings.OHMYGPT_API_KEY,
            base_url=settings.OHMYGPT_BASE_URL
        )
        
        # Build conversation for analysis
        conversation_text = "\n".join([
            f"{'User' if m.role == 'user' else 'AI'}: {m.content}" 
            for m in request.messages
        ])
        
        topic_info = f"Topic: {request.topic}" if request.topic else ""
        
        system_prompt = f"""You are an English tutor evaluating a student's conversation practice.

{topic_info}

Conversation:
{conversation_text}

Analyze the student's performance and provide detailed feedback.

Respond in this exact JSON format:
{{
    "scores": {{
        "fluency": 7.5,
        "grammar": 8.0,
        "vocabulary": 7.0,
        "relevance": 8.5,
        "overall": 7.75
    }},
    "grammar_errors": [
        {{
            "original": "i am go to school",
            "corrected": "I am going to school",
            "error_type": "verb_tense",
            "explanation": "Cần dùng 'going' vì đây là thì hiện tại tiếp diễn"
        }}
    ],
    "vocabulary_used": ["restaurant", "order", "food", "menu"],
    "strengths": ["Good use of polite expressions", "Clear communication"],
    "areas_to_improve": ["Work on verb tenses", "Use more varied vocabulary"],
    "overall_feedback": "Nhận xét tổng hợp bằng tiếng Việt về buổi luyện tập",
    "tips": ["Tip 1 bằng tiếng Việt", "Tip 2 bằng tiếng Việt"]
}}"""
        
        response = client.chat.completions.create(
            model=settings.OHMYGPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Evaluate this conversation"}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        import json
        result_text = response.choices[0].message.content
        
        try:
            # Clean up response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            
            # Parse scores
            scores_data = result.get("scores", {})
            scores = ConversationScore(
                fluency=float(scores_data.get("fluency", 7.0)),
                grammar=float(scores_data.get("grammar", 7.0)),
                vocabulary=float(scores_data.get("vocabulary", 7.0)),
                relevance=float(scores_data.get("relevance", 7.0)),
                overall=float(scores_data.get("overall", 7.0))
            )
            
            # Parse grammar errors
            grammar_errors = []
            for e in result.get("grammar_errors", []):
                grammar_errors.append(GrammarCorrection(
                    original=e.get("original", ""),
                    corrected=e.get("corrected", ""),
                    error_type=e.get("error_type", "grammar"),
                    explanation=e.get("explanation", "")
                ))
            
            return EndSimpleResponse(
                total_turns=len(user_messages),
                user_messages_count=len(user_messages),
                ai_messages_count=len(ai_messages),
                scores=scores,
                grammar_errors=grammar_errors[:10],  # Limit to 10
                vocabulary_used=result.get("vocabulary_used", [])[:20],
                strengths=result.get("strengths", ["Completed the conversation"]),
                areas_to_improve=result.get("areas_to_improve", ["Keep practicing"]),
                overall_feedback=result.get("overall_feedback", "Buổi luyện tập tốt!"),
                tips=result.get("tips", ["Luyện tập mỗi ngày để tiến bộ hơn"])
            )
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            # Fallback response
            return create_fallback_evaluation(user_messages, ai_messages, user_text_all)
            
    except Exception as e:
        print(f"❌ End simple error: {e}")
        return create_fallback_evaluation(user_messages, ai_messages, user_text_all)


def create_fallback_evaluation(user_messages, ai_messages, user_text_all):
    """Tạo đánh giá mặc định khi AI gặp lỗi"""
    # Simple word count based vocabulary
    words = set(w.lower() for w in user_text_all.split() if len(w) > 3 and w.isalpha())
    
    return EndSimpleResponse(
        total_turns=len(user_messages),
        user_messages_count=len(user_messages),
        ai_messages_count=len(ai_messages),
        scores=ConversationScore(
            fluency=7.0,
            grammar=7.0,
            vocabulary=7.0,
            relevance=7.5,
            overall=7.0
        ),
        grammar_errors=[],
        vocabulary_used=list(words)[:15],
        strengths=["Đã hoàn thành cuộc hội thoại", "Tham gia tích cực"],
        areas_to_improve=["Tiếp tục luyện tập thường xuyên"],
        overall_feedback="Bạn đã hoàn thành buổi luyện tập! Hãy tiếp tục cố gắng nhé.",
        tips=[
            "Luyện tập nói mỗi ngày 15-30 phút",
            "Nghe nhiều tiếng Anh từ phim, nhạc",
            "Đừng ngại mắc lỗi - đó là cách học tốt nhất"
        ]
    )

async def speech_to_text(audio_base64: str, user_id: int, audio_format: str) -> tuple:
    """
    Chuyển đổi audio thành text sử dụng Deepgram API
    
    Args:
        audio_base64: Audio data encoded base64
        user_id: ID của user
        audio_format: Format (webm, wav, mp3)
        
    Returns:
        tuple: (audio_url, transcription)
    """
    import httpx
    
    # 1. Tạo thư mục nếu chưa có
    user_folder = os.path.join(STT_UPLOAD_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    
    # 2. Decode và lưu audio
    if "," in audio_base64:
        base64_part = audio_base64.split(",")[1]
        audio_data = base64.b64decode(base64_part)
    else:
        audio_data = base64.b64decode(audio_base64)
    
    # 3. Save audio file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"user_{timestamp}_{unique_id}.{audio_format}"
    filepath = os.path.join(user_folder, filename)
    
    with open(filepath, "wb") as f:
        f.write(audio_data)
    
    audio_url = f"/uploads/audio/conversation/{user_id}/{filename}"
    print(f"💾 Saved user audio: {audio_url}")
    
    # 4. Call Deepgram API for Speech-to-Text
    if not settings.DEEPGRAM_API_KEY:
        print("❌ DEEPGRAM_API_KEY not set!")
        return audio_url, None
    
    try:
        # Xác định mimetype
        mimetype_map = {
            "webm": "audio/webm",
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "m4a": "audio/m4a",
            "ogg": "audio/ogg"
        }
        mimetype = mimetype_map.get(audio_format, "audio/webm")
        
        # Deepgram REST API
        url = "https://api.deepgram.com/v1/listen"
        params = {
            "model": settings.DEEPGRAM_MODEL or "nova-2",
            "language": settings.DEEPGRAM_LANGUAGE or "en-US",
            "punctuate": "true",
            "smart_format": "true",
        }
        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": mimetype,
        }
        
        print(f"🎯 Calling Deepgram STT API...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                params=params,
                headers=headers,
                content=audio_data
            )
        
        if response.status_code == 200:
            data = response.json()
            channels = data.get("results", {}).get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
                if alternatives:
                    transcription = alternatives[0].get("transcript", "")
                    print(f"✅ Deepgram STT: '{transcription}'")
                    return audio_url, transcription
        else:
            print(f"❌ Deepgram error: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Deepgram STT error: {type(e).__name__}: {e}")
    
    return audio_url, None