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
    AIConversationResponse, ConversationEndRequest,
    ConversationSummary, GrammarError, ConversationHistoryResponse
)
from app.core.dependencies import get_current_user
from app.config import settings

# Import services
from app.services.conversation_service import conversation_service, ConversationContext

router = APIRouter(
    prefix="/conversation",
    tags=["Conversation"]
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
        
        # 5. Save opening message
        opening_message = ConversationMessage(
            lesson_attempt_id=lesson_attempt.id,
            message_order=1,
            speaker=SpeakerType.AI,
            message_text=opening_text
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
        
        # 6. Return response
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
                audio_url=None,
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
    
    # 7. Save AI message
    ai_message = ConversationMessage(
        lesson_attempt_id=request.lesson_attempt_id,
        message_order=current_order + 1,
        speaker=SpeakerType.AI,
        message_text=ai_reply_text
    )
    db.add(ai_message)
    
    # 8. Update conversation turns
    lesson_attempt.conversation_turns = (current_order + 1) // 2  # Count pairs
    
    db.commit()
    db.refresh(ai_message)
    
    # 9. Generate suggested replies
    suggested_replies = generate_suggested_replies(template, ai_reply_text)
    
    # 10. Check if can end
    can_end = lesson_attempt.conversation_turns >= template.min_turns
    
    return AIConversationResponse(
        ai_message=ConversationMessageResponse(
            id=ai_message.id,
            message_order=ai_message.message_order,
            speaker="ai",
            message_text=ai_message.message_text,
            audio_url=None,
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
