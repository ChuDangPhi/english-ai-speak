# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI English Tutor - A web platform for practicing English speaking with an AI tutor. Built with FastAPI (Python) backend using MySQL database.

## Development Commands

```bash
# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative start
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/

# Format code
black app/

# Lint code
flake8 app/
```

## Environment Setup

1. Create virtual environment: `python -m venv .venv`
2. Activate (Windows PowerShell): `.\.venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and update credentials
5. Create MySQL database: `english_ai_speak`

## Architecture

### Directory Structure
```
app/
├── main.py              # FastAPI app entry point, middleware, routers
├── config.py            # Settings via pydantic-settings (from .env)
├── database.py          # SQLAlchemy engine, session, Base
├── core/
│   ├── dependencies.py  # Auth dependencies: get_current_user, get_current_admin
│   └── security.py      # JWT token creation/validation, password hashing
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── routers/             # API route handlers
├── services/            # Business logic (AI, pronunciation)
├── seeding/             # Database seed scripts
└── utils/               # Utility functions
```

### Data Models

**Core entities:**
- `User` / `UserSettings` - User accounts with role-based access (admin/user)
- `Topic` - Learning topics (e.g., "At the Restaurant")
- `Lesson` - Lessons within topics (vocabulary, pronunciation, conversation types)
- `Vocabulary` - Words with definitions, examples, pronunciation
- `LessonAttempt` - User attempts at lessons with scores

**Lesson types:** vocabulary_matching, pronunciation, conversation

**Progress tracking:** `UserLessonProgress`, `UserProgress`, `DailyStats`, `UserStreak`

### Authentication Flow

JWT-based auth with access tokens (30 min) and refresh tokens (7 days):
- `app/core/security.py` - Token creation with `create_access_token()`, `create_refresh_token()`
- `app/core/dependencies.py` - Route protection via `get_current_user`, `get_current_admin` dependencies
- Tokens include `type` field ("access" or "refresh") to prevent misuse

### AI Services

**ConversationService** (`app/services/conversation_service.py`):
- Uses OhMyGPT API (OpenAI-compatible) for conversation AI
- Generates opening messages, replies, and conversation summaries
- Analyzes user messages for grammar errors, vocabulary, sentiment

**PronunciationService** (`app/services/pronunciation_service.py`):
- Uses Deepgram API for speech-to-text
- Compares spoken words with reference text
- Calculates pronunciation, intonation, and stress scores

### API Structure

All routes prefixed with `/api/v1`:
- `/auth` - Register, login, refresh, logout, /me
- `/topics` - CRUD topics (admin protected)
- `/lessons` - CRUD lessons
- `/vocabulary` - Vocabulary management
- `/attempts` - Lesson attempts and scoring
- `/pronunciation` - Pronunciation analysis
- `/conversation` - AI conversation practice
- `/progress` - User progress tracking

API docs available at `/docs` (Swagger) and `/redoc`.

### Database

MySQL with SQLAlchemy ORM. Connection pooling enabled (10 connections, max 20 overflow).

Models auto-create tables on startup via `init_db()`. Alembic is installed but migrations are not yet configured.

### Key Patterns

**Dependency injection:** Use `Depends(get_current_user)` to protect routes
```python
@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"user": current_user.email}
```

**Admin-only routes:** Use `Depends(get_current_admin)`

**Optional auth:** Use `get_current_user_optional` for routes that work for both guests and logged-in users

**Service singletons:** Services instantiated at module level (e.g., `conversation_service = ConversationService()`)

**Pydantic schemas:** All request/response validation via schemas in `app/schemas/`
