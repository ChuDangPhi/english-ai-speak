# AI English Tutor — Project Analysis & Roadmap

Đây là tài liệu README chi tiết tổng hợp phân tích dự án, trạng thái hiện tại, roadmap, các tasks ưu tiên và hướng phát triển để bạn dễ theo dõi và điều phối công việc.

## 1. TỔNG QUAN

Mục tiêu: Xây dựng nền tảng luyện nói tiếng Anh với trợ lý AI, bao gồm:
- Luyện hội thoại với AI tutor
- Chấm phát âm tự động
- Quản lý từ vựng cá nhân
- Theo dõi tiến độ học tập

Tech stack chính:
- Backend: FastAPI (Python)
- ORM: SQLAlchemy
- Database: MySQL
- Auth: JWT (python-jose)
- Password hashing: bcrypt (passlib)
- AI APIs: OpenAI / Google Gemini
- Speech: OpenAI Whisper / SpeechRecognition

---

## 2. HIỆN TRẠNG DỰ ÁN (Tóm tắt)

Đã có:
- FastAPI app cấu trúc rõ ràng (`app/main.py`)
- Config với `pydantic-settings` (`app/config.py`)
- Kết nối DB MySQL + SQLAlchemy (`app/database.py`)
- Model `User` cơ bản (`app/models/user.py`)
- Router auth: register, login (`app/routers/auth.py`)
- Pydantic schemas cho user & token (`app/schemas/user.py`)
- Middleware CORS, request timing, health endpoints, logging
- Swagger UI & ReDoc sẵn sàng khi server chạy

Chưa hoàn thiện / thiếu:
- Middleware/dependency để xác thực JWT (`get_current_user`) và bảo vệ route
- Refresh token, logout, password reset, email verification
- Models chính cho Conversation, Message, Vocabulary, LearningSession
- Alembic migrations chưa có (folder trống)
- AI service tích hợp (OpenAI/Gemini) chưa có
- Speech processing (STT/TTS, pronunciation scoring) chưa có
- Tests (unit/integration) còn thiếu
- Docker / CI/CD / production deploy chưa cấu hình

---

## 3. CHI TIẾT PHÂN TÍCH & KHU VỰC CẦN PHÁT TRIỂN

1) Authentication (priority cao)
- Implement `get_current_user` dependency dùng Bearer token
- Thêm endpoint `/auth/refresh`, `/auth/me`
- Protected routes sử dụng dependency
- Role-based access control (nếu cần)

2) Database & Migrations
- Thêm models: Conversation, Message, Vocabulary, LearningSession
- Cấu hình Alembic và tạo initial migration
- Tạo seed data cho dev

3) AI Conversation (core feature)
- Tạo `app/services/ai_service.py` để gọi OpenAI/Gemini
- Conversation endpoints: start, message, end
- Lưu lịch sử, quản lý ngữ cảnh (context)
- Xử lý rate limiting & error handling

4) Speech Processing
- `app/services/speech_service.py`: transcription, pronunciation scoring, TTS
- Router endpoints cho upload audio, trả về transcript & score
- Lưu audio trên storage (local S3/MinIO in prod)

5) Vocabulary & Learning
- CRUD vocabulary, spaced-repetition (SM-2) hoặc đơn giản
- Practice endpoints, review scheduling

6) Analytics & Progress
- Learning sessions, dashboard endpoints
- Thống kê: conversation count, minutes, vocab mastered, avg pronunciation

7) Testing & QA
- Unit tests cho services
- Integration tests cho API
- Test coverage target >= 80%
- Load testing (Locust)

8) DevOps
- Dockerfile & docker-compose
- CI: GitHub Actions (lint, tests, build)
- Deploy lên Heroku / Render / Railway / AWS
- Monitoring (Sentry), logging central

---

## 4. ĐỀ XUẤT KIẾN TRÚC CHI TIẾT (Models chính)

- `Conversation` (id, user_id, topic, difficulty_level, status, created_at)
- `Message` (id, conversation_id, role[user/assistant], content, audio_url, pronunciation_score, created_at)
- `Vocabulary` (id, user_id, word, definition, example, pronunciation, level, mastery_level, next_review_date, review_count)
- `LearningSession` (id, user_id, session_type, duration_minutes, words_practiced, accuracy_score, created_at)

---

## 5. ROADMAP & PHASES (gợi ý thời gian)

Thời gian tham khảo: 3 tháng (các tuần tuần tự)

Tháng 1 - Foundation
- Week 1: Authentication completion (get_current_user, refresh, /me)
- Week 2: DB models + Alembic initial migrations
- Week 3: Basic AI Conversation (integrate OpenAI, start/message)
- Week 4: Tests for auth & conversation

Tháng 2 - Core features
- Week 5-6: Speech processing (STT/TTS, scoring)
- Week 7: Vocabulary management & spaced repetition
- Week 8: Progress tracking & analytics

Tháng 3 - Polish & Deploy
- Week 9: Tests & bug fixes
- Week 10: Docker + CI/CD
- Week 11: Performance optimizations (caching, indexes)
- Week 12: Documentation & release

---

## 6. TASKS NGAY (Action items)

Critical (làm ngay):
- Implement `get_current_user` dependency (JWT verification)
- Update `/auth/me` to use dependency
- Add `refresh` token endpoint
- Setup Alembic và tạo migration

Important (tuần tiếp theo):
- Implement Conversation + Message models
- Integrate minimal AIService (OpenAI) để trả lời
- Implement audio upload + STT endpoint
- Add unit tests cho auth & ai_service

Lower priority:
- Vocabulary features
- Analytics endpoints
- Docker & deployment

---

## 7. HƯỚNG DẪN CHẠY NGAY TẠI MÁY DEV (PowerShell)

1) Tạo virtualenv và kích hoạt (PowerShell):

```powershell
python -m venv .venv
# Kích hoạt
.\.venv\Scripts\Activate.ps1
```

2) Cài dependencies:

```powershell
pip install -r requirements.txt
```

3) Copy `.env.example` thành `.env` và cập nhật thông tin DB, keys:

```powershell
copy .env.example .env
# Sửa .env bằng editor: DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD, DATABASE_NAME, OPENAI_API_KEY, v.v.
```

4) Chạy server (development):

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5) Mở Swagger UI:

- http://localhost:8000/docs
- http://localhost:8000/redoc


---

## 8. Sự cố phổ biến & cách khắc phục nhanh

- Lỗi SQLAlchemy / Python version: cập nhật `sqlalchemy` (ví dụ `pip install --upgrade sqlalchemy`) hoặc dùng Python 3.11 nếu chỗ nào không tương thích
- ModuleNotFoundError: kiểm tra virtualenv đã active và `pip install -r requirements.txt`
- `ModuleNotFoundError: No module named 'app'`: chạy lệnh từ thư mục gốc dự án (`d:\Personal\WEB_ENGLISH\ai_tutor_BE`) hoặc dùng `PYTHONPATH`/module path đúng

---

## 9. GỢI Ý NGẮN HẠN (Quick wins)

1. Implement `get_current_user` và update `/auth/me` (1-2 ngày)
2. Tạo Alembic initial migration và seed vài user (1-2 ngày)
3. Tạo service wrapper `AIService` gọi OpenAI — trả về response cơ bản (1 tuần)
4. Thêm 10 tests cơ bản cho auth + ai_service (1 tuần)

---

## 10. TIẾP THEO (Bạn muốn tôi làm ngay)

Tôi có thể bắt đầu implement phần **Authentication Middleware** (`get_current_user`) và cập nhật endpoint `/auth/me`, hoặc tạo Alembic + models cho Conversation — bạn muốn ưu tiên phần nào?


---

*File này được tạo tự động theo yêu cầu của bạn. Nếu cần đổi tên file hoặc muốn hợp nhất vào `README.md` gốc, tôi có thể thực hiện.*
