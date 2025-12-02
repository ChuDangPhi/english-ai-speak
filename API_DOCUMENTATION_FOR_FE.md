# 📚 API Documentation - Học theo Chủ đề với AI

## Mục lục
1. [Tổng quan](#1-tổng-quan)
2. [Authentication](#2-authentication)
3. [Topics API](#3-topics-api)
4. [Lessons API](#4-lessons-api)
5. [Attempts API](#5-attempts-api)
6. [Pronunciation API](#6-pronunciation-api)
7. [Conversation API](#7-conversation-api)
8. [Progress API](#8-progress-api)
9. [Flow hoạt động](#9-flow-hoạt-động)

---

## 1. Tổng quan

### Base URL
```
http://127.0.0.1:8000/api/v1
```

### Authentication Header
```
Authorization: Bearer <access_token>
```

### Response Format
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

### Error Format
```json
{
  "detail": "Error message"
}
```

---

## 2. Authentication

### 2.1. Đăng ký
```
POST /auth/register
```

**Request Body:**
```json
{
  "full_name": "Nguyễn Văn A",
  "email": "user@example.com",
  "password": "123456"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Nguyễn Văn A",
  "is_active": true,
  "created_at": "2024-12-02T10:00:00"
}
```

### 2.2. Đăng nhập
```
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "123456"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Nguyễn Văn A"
  }
}
```

### 2.3. Lấy thông tin user
```
GET /auth/profile
```
**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Nguyễn Văn A",
  "avatar_url": null,
  "total_xp": 500,
  "current_level": 3,
  "created_at": "2024-12-02T10:00:00"
}
```

---

## 3. Topics API

### 3.1. Lấy danh sách chủ đề
```
GET /topics
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| page | int | Số trang (default: 1) |
| page_size | int | Số item/trang (default: 10, max: 50) |
| category | string | Filter: general, business, travel, daily_life |
| difficulty_level | string | Filter: beginner, intermediate, advanced |
| search | string | Tìm theo title |

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "title": "At the Restaurant",
      "description": "Learn vocabulary and conversations for dining out",
      "category": "daily_life",
      "difficulty_level": "beginner",
      "thumbnail_url": null,
      "total_lessons": 3,
      "estimated_duration_minutes": 45,
      "display_order": 1
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

### 3.2. Lấy chi tiết chủ đề (kèm lessons)
```
GET /topics/{topic_id}
```

**Response (200):**
```json
{
  "id": 1,
  "title": "At the Restaurant",
  "description": "Learn vocabulary and conversations for dining out",
  "category": "daily_life",
  "difficulty_level": "beginner",
  "thumbnail_url": null,
  "total_lessons": 3,
  "estimated_duration_minutes": 45,
  "lessons": [
    {
      "id": 1,
      "topic_id": 1,
      "lesson_type": "vocabulary_matching",
      "title": "Vocabulary: At the Restaurant",
      "description": "Learn and practice vocabulary related to restaurants",
      "lesson_order": 1,
      "instructions": "Match each English word with its Vietnamese meaning",
      "estimated_minutes": 15,
      "passing_score": 70.0,
      "status": "available",
      "best_score": null,
      "total_attempts": 0,
      "last_attempt_at": null
    },
    {
      "id": 2,
      "topic_id": 1,
      "lesson_type": "pronunciation",
      "title": "Pronunciation: At the Restaurant",
      "description": "Practice pronouncing key words and phrases",
      "lesson_order": 2,
      "status": "locked",
      ...
    },
    {
      "id": 3,
      "topic_id": 1,
      "lesson_type": "conversation",
      "title": "Conversation: At the Restaurant",
      "description": "Practice real conversations with AI",
      "lesson_order": 3,
      "status": "locked",
      ...
    }
  ],
  "lessons_completed": 0,
  "progress_percent": 0.0,
  "status": "not_started"
}
```

**Lesson Status Values:**
- `available`: Có thể học
- `locked`: Chưa mở khóa (cần hoàn thành bài trước)
- `in_progress`: Đang học
- `completed`: Đã hoàn thành

---

## 4. Lessons API

### 4.1. Lấy chi tiết bài học
```
GET /lessons/{lesson_id}
```
**Headers:** `Authorization: Bearer <token>`

**Response tùy theo lesson_type:**

#### A. Vocabulary Matching Lesson
```json
{
  "id": 1,
  "title": "Vocabulary: At the Restaurant",
  "description": "Learn and practice vocabulary",
  "instructions": "Match each English word with its Vietnamese meaning",
  "lesson_type": "vocabulary_matching",
  "passing_score": 70.0,
  "estimated_minutes": 15,
  "vocabulary_list": [
    {
      "id": 1,
      "word": "menu",
      "definition": "thực đơn"
    },
    {
      "id": 2,
      "word": "waiter",
      "definition": "người phục vụ (nam)"
    },
    {
      "id": 3,
      "word": "bill",
      "definition": "hóa đơn"
    }
  ]
}
```

#### B. Pronunciation Lesson
```json
{
  "id": 2,
  "title": "Pronunciation: At the Restaurant",
  "description": "Practice pronouncing key words",
  "instructions": "Listen and repeat. Record your voice for AI evaluation.",
  "lesson_type": "pronunciation",
  "passing_score": 70.0,
  "estimated_minutes": 20,
  "exercises": [
    {
      "id": 1,
      "exercise_type": "word",
      "content": "menu",
      "phonetic": "/ˈmenjuː/",
      "audio_url": null,
      "target_pronunciation_score": 70,
      "display_order": 1
    },
    {
      "id": 2,
      "exercise_type": "phrase",
      "content": "I'd like to order",
      "phonetic": "/aɪd laɪk tuː ˈɔːrdər/",
      "audio_url": null,
      "target_pronunciation_score": 65,
      "display_order": 2
    }
  ]
}
```

#### C. Conversation Lesson
```json
{
  "id": 3,
  "title": "Conversation: At the Restaurant",
  "description": "Practice real conversations with AI",
  "instructions": "Have a conversation with the AI tutor",
  "lesson_type": "conversation",
  "passing_score": 60.0,
  "estimated_minutes": 15,
  "conversation_template": {
    "id": 1,
    "ai_role": "Waiter at an Italian restaurant",
    "scenario_context": "You are a customer at a restaurant. Order food and drinks.",
    "starter_prompts": ["I'd like to see the menu", "What do you recommend?"],
    "suggested_topics": ["ordering food", "asking about ingredients"],
    "min_turns": 5
  }
}
```

---

## 5. Attempts API

### 5.1. Bắt đầu làm bài
```
POST /attempts
```
**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "lesson_id": 1
}
```

**Response (201):**
```json
{
  "id": 123,
  "lesson_id": 1,
  "attempt_number": 1,
  "lesson_type": "vocabulary_matching",
  "started_at": "2024-12-02T10:30:00",
  "passing_score": 70.0,
  "estimated_minutes": 15
}
```

⚠️ **Quan trọng:** Lưu `id` (attempt_id) để dùng cho các API submit sau đó.

### 5.2. Hoàn thành bài học
```
POST /attempts/{attempt_id}/complete
```
**Headers:** `Authorization: Bearer <token>`

**Request Body (optional):**
```json
{
  "lesson_attempt_id": 123,
  "overall_score": 85.5,
  "vocabulary_correct": 8,
  "vocabulary_total": 10,
  "pronunciation_score": 80.0,
  "intonation_score": 75.0,
  "stress_score": 85.0,
  "conversation_turns": 6,
  "fluency_score": 78.0,
  "grammar_score": 82.0
}
```

**Response (200):**
```json
{
  "attempt_id": 123,
  "lesson_id": 1,
  "lesson_type": "vocabulary_matching",
  "overall_score": 85.5,
  "is_passed": true,
  "xp_earned": 55,
  "duration_seconds": 420,
  "feedback": "Excellent work! You've mastered the vocabulary.",
  "next_lesson_unlocked": true,
  "next_lesson_id": 2
}
```

### 5.3. Lấy lịch sử làm bài
```
GET /attempts/history
```
**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| lesson_id | int | Filter theo lesson |
| topic_id | int | Filter theo topic |
| page | int | Số trang |
| page_size | int | Số item/trang |

---

## 6. Pronunciation API

### 6.1. Submit audio phát âm
```
POST /pronunciation/submit
```
**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "lesson_attempt_id": 123,
  "exercise_id": 1,
  "audio_base64": "data:audio/webm;base64,GkXfo59ChoEBQveB...",
  "audio_format": "webm"
}
```

**Response (200):**
```json
{
  "id": 456,
  "exercise_id": 1,
  "transcription": "menu",
  "target_text": "menu",
  "pronunciation_score": 85.0,
  "intonation_score": 78.0,
  "stress_score": 90.0,
  "accuracy_score": 88.0,
  "overall_score": 85.25,
  "is_correct": true,
  "feedback": {
    "overall": "Great pronunciation!",
    "suggestions": ["Pay attention to the stress on first syllable"],
    "word_scores": [
      {"word": "menu", "score": 85, "phonetic": "/ˈmenjuː/"}
    ]
  }
}
```

### 6.2. Lấy tổng kết phát âm
```
GET /pronunciation/summary/{lesson_attempt_id}
```
**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "lesson_attempt_id": 123,
  "total_exercises": 8,
  "completed_exercises": 8,
  "average_pronunciation_score": 82.5,
  "average_intonation_score": 78.0,
  "average_stress_score": 85.0,
  "overall_score": 81.8,
  "exercises_detail": [...]
}
```

---

## 7. Conversation API

### 7.1. Bắt đầu hội thoại
```
POST /conversation/start
```
**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "lesson_id": 3,
  "attempt_id": 123
}
```

**Response (200):**
```json
{
  "message": "Hello! Welcome to our restaurant. I'm your waiter today. How can I help you?",
  "ai_role": "Waiter at an Italian restaurant",
  "scenario_context": "You are a customer at a restaurant",
  "suggested_responses": ["I'd like to see the menu", "Do you have any specials today?"]
}
```

### 7.2. Gửi tin nhắn
```
POST /conversation/message
```
**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "attempt_id": 123,
  "message": "I'd like to order a pizza"
}
```

**Response (200):**
```json
{
  "reply": "Excellent choice! We have several types of pizza. Would you prefer Margherita, Pepperoni, or our special Quattro Formaggi?",
  "analysis": {
    "grammar_correct": true,
    "grammar_note": null,
    "vocabulary_used": ["order", "pizza"],
    "sentiment": "positive"
  },
  "suggestions": ["I'll have the Margherita", "What's in the Quattro Formaggi?"],
  "turn_number": 2
}
```

### 7.3. Kết thúc hội thoại
```
POST /conversation/end
```
**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "attempt_id": 123
}
```

**Response (200):**
```json
{
  "overall_score": 78.5,
  "turns_completed": 6,
  "fluency_score": 75.0,
  "grammar_score": 80.0,
  "vocabulary_score": 82.0,
  "vocabulary_used": ["menu", "order", "pizza", "recommend", "bill"],
  "grammar_mistakes": [
    {"original": "I want pizza", "corrected": "I'd like a pizza", "explanation": "More polite form"}
  ],
  "feedback": "Good conversation! You successfully ordered food. Try using more polite expressions.",
  "xp_earned": 100
}
```

### 7.4. Lấy lịch sử hội thoại
```
GET /conversation/history/{attempt_id}
```
**Headers:** `Authorization: Bearer <token>`

---

## 8. Progress API

### 8.1. Tổng quan tiến độ
```
GET /progress/overview
```
**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "total_xp": 1250,
  "current_level": 5,
  "xp_to_next_level": 250,
  "current_streak": 7,
  "longest_streak": 14,
  "total_lessons_completed": 12,
  "total_topics_completed": 3,
  "total_vocabulary_learned": 85,
  "average_score": 82.5,
  "total_practice_time_minutes": 320
}
```

### 8.2. Streak hiện tại
```
GET /progress/streak
```
**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "current_streak": 7,
  "longest_streak": 14,
  "last_practice_date": "2024-12-02",
  "streak_frozen": false,
  "freeze_count": 2
}
```

### 8.3. Thống kê theo ngày
```
GET /progress/daily
```
**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| days | int | Số ngày (default: 7) |

**Response (200):**
```json
[
  {
    "date": "2024-12-02",
    "xp_earned": 150,
    "lessons_completed": 2,
    "practice_time_minutes": 45,
    "vocabulary_learned": 12
  },
  {
    "date": "2024-12-01",
    "xp_earned": 100,
    "lessons_completed": 1,
    "practice_time_minutes": 30,
    "vocabulary_learned": 8
  }
]
```

### 8.4. Tiến độ theo topic
```
GET /progress/topics
```
**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
[
  {
    "topic_id": 1,
    "topic_title": "At the Restaurant",
    "lessons_completed": 2,
    "total_lessons": 3,
    "progress_percent": 66.7,
    "best_score": 85.0,
    "status": "in_progress"
  }
]
```

### 8.5. Từ vựng đã học
```
GET /progress/vocabulary
```
**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| topic_id | int | Filter theo topic |
| status | string | mastered, learning, new |
| page | int | Số trang |
| page_size | int | Số item/trang |

---

## 9. Flow hoạt động

### 9.1. Flow học Vocabulary Matching

```
1. GET /topics                          → Hiển thị danh sách chủ đề
2. GET /topics/{topic_id}               → Lấy chi tiết topic + lessons
3. POST /attempts {lesson_id}           → Bắt đầu làm bài (lưu attempt_id)
4. GET /lessons/{lesson_id}             → Lấy vocabulary_list
5. User làm bài matching trên FE
6. POST /attempts/{attempt_id}/complete → Hoàn thành + nhận kết quả
```

### 9.2. Flow học Pronunciation

```
1. POST /attempts {lesson_id}           → Bắt đầu làm bài
2. GET /lessons/{lesson_id}             → Lấy exercises list
3. Với mỗi exercise:
   a. Hiển thị text + phonetic
   b. User ghi âm
   c. POST /pronunciation/submit        → Gửi audio, nhận điểm
4. GET /pronunciation/summary/{attempt_id} → Tổng kết
5. POST /attempts/{attempt_id}/complete → Hoàn thành
```

### 9.3. Flow học Conversation

```
1. POST /attempts {lesson_id}           → Bắt đầu làm bài
2. GET /lessons/{lesson_id}             → Lấy conversation_template
3. POST /conversation/start             → Nhận opening message từ AI
4. Loop:
   a. User nhập/nói message
   b. POST /conversation/message        → Gửi message, nhận reply + analysis
   c. Hiển thị AI reply
5. POST /conversation/end               → Kết thúc + nhận summary
6. POST /attempts/{attempt_id}/complete → Hoàn thành
```

---

## 10. Audio Format

### Recording
- Format: WebM (recommended) hoặc WAV
- Sample rate: 16000 Hz
- Channels: Mono
- Encoding: Base64

### Gửi lên server
```javascript
// Convert Blob to Base64
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

// Example
const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
const audioBase64 = await blobToBase64(audioBlob);
// audioBase64 = "data:audio/webm;base64,GkXfo59..."
```

---

## 11. XP System

| Action | XP Earned |
|--------|-----------|
| Complete Vocabulary Lesson | 50 XP |
| Complete Pronunciation Lesson | 75 XP |
| Complete Conversation Lesson | 100 XP |
| Perfect Score Bonus (100%) | +20 XP |
| High Score Bonus (≥90%) | +10 XP |
| First Attempt Bonus | +15 XP |
| Daily Streak Bonus | +5 XP per day |

---

## 12. Error Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Token invalid/expired |
| 403 | Forbidden - No permission (lesson locked) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## 13. Swagger UI

Truy cập Swagger UI để test API:
```
http://127.0.0.1:8000/docs
```

---

**Cập nhật lần cuối:** 2024-12-02
