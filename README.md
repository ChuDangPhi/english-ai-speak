# 🎯 AI English Tutor

Web luyện nói tiếng Anh với trợ lý AI - Nền tảng học tiếng Anh thông minh sử dụng công nghệ AI

## 🚀 Tính năng

- ✅ **Đăng ký/Đăng nhập** - JWT Authentication
- 🗣️ **Luyện hội thoại với AI** - Practice speaking với AI tutor
- 📝 **Chấm phát âm tự động** - AI đánh giá phát âm
- 📚 **Quản lý từ vựng** - Lưu và ôn tập từ vựng cá nhân
- 📊 **Theo dõi tiến độ** - Dashboard hiển thị progress học tập
- 🎓 **Phân cấp độ** - Beginner, Intermediate, Advanced

## 🛠️ Công nghệ sử dụng

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM cho Python
- **MySQL** - Database
- **JWT** - Authentication
- **Bcrypt** - Password hashing
- **Pydantic** - Data validation

### AI Services
- **OpenAI GPT** - Conversational AI
- **Google Gemini** - Alternative AI model
- **Speech Recognition** - Voice processing

## 📋 Yêu cầu hệ thống

- Python 3.9+
- MySQL 8.0+
- pip (Python package manager)

## 🔧 Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/your-username/ai_beginer_tutor.git
cd ai_beginer_tutor
```

### 2. Tạo virtual environment

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình database

Tạo database trong MySQL:

```sql
CREATE DATABASE english_ai_speak CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Cấu hình environment variables

Copy file `.env.example` thành `.env` và cập nhật thông tin:

```bash
cp .env.example .env
```

Sửa file `.env`:

```env
# Database
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=your_password
DATABASE_NAME=english_ai_speak

# JWT Security
SECRET_KEY=your-secret-key-change-in-production

# AI API Keys
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### 6. Chạy ứng dụng

```bash
Push-Location D:\Personal\WEB_ENGLISH\ai_tutor_BE; D:\Personal\WEB_ENGLISH\ai_tutor_BE\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Hoặc:

```bash
python -m uvicorn app.main:app --reload
```

