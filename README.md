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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Hoặc:

```bash
python -m uvicorn app.main:app --reload
```

## 📖 API Documentation

Sau khi chạy server, truy cập:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔐 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Đăng ký tài khoản mới |
| POST | `/api/v1/auth/login` | Đăng nhập |
| GET | `/api/v1/auth/me` | Lấy thông tin user hiện tại |

### Example: Đăng ký

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "Nguyễn Văn A"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "Nguyễn Văn A",
    "current_level": "beginner",
    "is_active": true,
    "created_at": "2025-11-04T10:00:00"
  }
}
```

## 📁 Cấu trúc project

```
ai_beginer_tutor/
├── app/
│   ├── core/           # Core functionality (security, config)
│   ├── models/         # Database models (SQLAlchemy)
│   ├── routers/        # API routes
│   ├── schemas/        # Pydantic schemas (validation)
│   ├── services/       # Business logic
│   ├── utils/          # Utility functions
│   ├── config.py       # Application config
│   ├── database.py     # Database connection
│   └── main.py         # FastAPI app entry point
├── tests/              # Unit & integration tests
├── uploads/            # User uploaded files
├── logs/               # Application logs
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 🧪 Testing

### Chạy tests

```bash
pytest
```

### Test với coverage

```bash
pytest --cov=app tests/
```

## 🔒 Security

- Passwords được hash bằng bcrypt
- JWT tokens với expiration time
- SQL injection protection với SQLAlchemy ORM
- CORS configuration
- Rate limiting (TODO)

## 🚀 Deployment

### Với Docker (Coming soon)

```bash
docker-compose up -d
```

### Với Heroku

```bash
heroku create your-app-name
git push heroku main
```

## 📝 Roadmap

- [x] Authentication (JWT)
- [x] User management
- [ ] AI conversation practice
- [ ] Pronunciation scoring
- [ ] Vocabulary management
- [ ] Progress tracking
- [ ] Admin dashboard
- [ ] Mobile app (React Native)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Chu Dang Phi** - *Initial work* - [GitHub Profile](https://github.com/your-username)

## 🙏 Acknowledgments

- FastAPI documentation
- OpenAI API
- Google Gemini API
- SQLAlchemy docs

## 📧 Contact

- Email: your-email@example.com
- GitHub: [@your-username](https://github.com/your-username)
- Project Link: [https://github.com/your-username/ai_beginer_tutor](https://github.com/your-username/ai_beginer_tutor)

---

⭐ **Nếu project hữu ích, đừng quên star repo nhé!** ⭐
