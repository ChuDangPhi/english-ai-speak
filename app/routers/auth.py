"""
Authentication router - API endpoints cho đăng ký và đăng nhập

Giải thích luồng hoạt động:
1. Client gửi request đến endpoint
2. Pydantic Schema validate dữ liệu tự động
3. Router nhận dữ liệu đã validate
4. get_db() inject database session
5. Router xử lý logic (hash password, tạo user, tạo token)
6. Return response (FastAPI tự động convert sang JSON)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token

# Tạo router với prefix /auth
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]  # Tag để nhóm trong Swagger UI
)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,  # ← Pydantic tự động validate
    db: Session = Depends(get_db)  # ← FastAPI tự động inject session
):
    """
    Đăng ký tài khoản mới
    
    Luồng xử lý:
    1. Kiểm tra email đã tồn tại chưa
    2. Hash password
    3. Tạo user mới trong database
    4. Tạo JWT tokens (access + refresh)
    5. Trả về tokens + thông tin user
    
    Args:
        user_data: Dữ liệu đăng ký (email, password, full_name)
        db: Database session (auto-injected)
        
    Returns:
        TokenResponse: access_token, refresh_token, user info
        
    Raises:
        HTTPException 400: Email đã tồn tại
    """
    
    # Bước 1: Kiểm tra email đã tồn tại
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng"
        )
    
    # Bước 2: Hash password
    hashed_pwd = hash_password(user_data.password)
    
    # Bước 3: Tạo user mới
    new_user = User(
        email=user_data.email,
        password_hash=hashed_pwd,  # Lưu hash, không lưu plain password
        full_name=user_data.full_name,
        current_level="beginner",  # Default level
        is_active=True
    )
    
    # Lưu vào database
    db.add(new_user)  # Thêm vào session
    db.commit()  # Commit transaction
    db.refresh(new_user)  # Lấy data mới nhất từ DB (bao gồm id, created_at...)
    
    # Bước 4: Tạo JWT tokens
    token_data = {"sub": new_user.id, "email": new_user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Bước 5: Trả về response
    # FastAPI tự động convert UserResponse từ SQLAlchemy model
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)  # Convert model → schema
    )

@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,  # ← Email + password
    db: Session = Depends(get_db)
):
    """
    Đăng nhập
    
    Luồng xử lý:
    1. Tìm user theo email
    2. Verify password
    3. Tạo JWT tokens
    4. Trả về tokens + user info
    
    Args:
        credentials: Email và password
        db: Database session
        
    Returns:
        TokenResponse: access_token, refresh_token, user info
        
    Raises:
        HTTPException 401: Email không tồn tại hoặc password sai
    """
    
    # Bước 1: Tìm user theo email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Bước 2: Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Kiểm tra account active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )
    
    # Bước 3: Tạo JWT tokens
    token_data = {"sub": user.id, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Bước 4: Trả về response
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    db: Session = Depends(get_db),
    # TODO: Thêm authentication dependency sau
):
    """
    Lấy thông tin user hiện tại (dùng sau khi implement authentication)
    
    Hiện tại chưa có authentication, sẽ implement sau
    """
    return HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint chưa được implement"
    )
