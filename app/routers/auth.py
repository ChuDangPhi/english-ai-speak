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
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from jose import JWTError, jwt

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse, UserResponse, RefreshTokenRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ResendVerificationRequest, MessageResponse
)
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.dependencies import get_current_user
from app.config import settings
from app.utils.token import generate_verification_token, generate_password_reset_token
from app.utils.email import send_verification_email, send_password_reset_email

# Tạo router với prefix /auth
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]  # Tag để nhóm trong Swagger UI
)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,  # ← Pydantic tự động validate
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)  # ← FastAPI tự động inject session
):
    """
    Đăng ký tài khoản mới
    
    Luồng xử lý:
    1. Kiểm tra email đã tồn tại chưa
    2. Hash password
    3. Tạo user mới trong database
    4. Tạo verification token + gửi email xác thực
    5. Tạo JWT tokens (access + refresh)
    6. Trả về tokens + thông tin user
    
    Args:
        user_data: Dữ liệu đăng ký (email, password, full_name)
        background_tasks: Background tasks để gửi email async
        db: Database session (auto-injected)
        
    Returns:
        TokenResponse: access_token, refresh_token, user info
        
    Raises:
        HTTPException 400: Email đã tồn tại
    """
    
    try:
        # Bước 1: Kiểm tra email đã tồn tại
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email đã được sử dụng"
            )
        
        # Bước 2: Hash password
        hashed_pwd = hash_password(user_data.password)
        
        # Bước 3: Tạo verification token
        verification_token = generate_verification_token()
        
        # Bước 4: Tạo user mới
        new_user = User(
            email=user_data.email,
            password_hash=hashed_pwd,  # Lưu hash, không lưu plain password
            full_name=user_data.full_name,
            current_level="beginner",  # Default level
            is_active=True,
            email_verified=False,  # Chưa xác thực email
            email_verification_token=verification_token,
            email_verification_sent_at=datetime.utcnow()
        )
        
        # Lưu vào database
        db.add(new_user)  # Thêm vào session
        db.commit()  # Commit transaction
        db.refresh(new_user)  # Lấy data mới nhất từ DB (bao gồm id, created_at...)
        
        # Bước 5: Gửi email xác thực (background task - không block response)
        background_tasks.add_task(
            send_verification_email,
            email=new_user.email,
            full_name=new_user.full_name,
            verification_token=verification_token
        )
        
        # Bước 6: Tạo JWT tokens
        token_data = {"sub": str(new_user.id), "email": new_user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Bước 7: Trả về response
        # FastAPI tự động convert UserResponse từ SQLAlchemy model
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(new_user)  # Convert model → schema
        )
        
    except IntegrityError as e:
        # Lỗi unique constraint (email duplicate)
        # Rollback transaction để cleanup
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng (database constraint)"
        )
    
    except SQLAlchemyError as e:
        # Lỗi database khác (connection, query, etc.)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    except Exception as e:
        # Lỗi không mong đợi khác
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
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
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Bước 4: Trả về response
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse, summary="Lấy thông tin user hiện tại")
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    # Endpoint to return current user info. Description intentionally minimal to keep Swagger clean.
    # Authentication: Bearer token required (handled by dependency).
    # Returns: UserResponse
    return current_user


@router.post("/refresh", response_model=TokenResponse, summary="Làm mới access token")
def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    # Refresh access token. Minimal description for Swagger.
    
    try:
        # ===== BƯỚC 1: DECODE REFRESH TOKEN =====
        payload = jwt.decode(
            request.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # ===== BƯỚC 2: LẤY THÔNG TIN TỪ PAYLOAD =====
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        # ===== BƯỚC 3: VERIFY TOKEN TYPE =====
        # Quan trọng! Phải check token type = "refresh"
        # Nếu không, user có thể dùng access token để refresh → không an toàn
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token, got access token."
            )
        
        # ===== BƯỚC 4: TÌM USER TRONG DATABASE =====
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check user active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # ===== BƯỚC 5: TẠO TOKENS MỚI =====
        # Tạo cả access và refresh token mới
        # Lý do: Refresh token rotation - tăng bảo mật
        new_access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id), "email": user.email})
        
        # ===== BƯỚC 6: TRẢ VỀ RESPONSE =====
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
        
    except JWTError:
        # Token expired, invalid signature, hoặc malformed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.post("/logout", summary="Đăng xuất")
def logout(
    current_user: User = Depends(get_current_user)
):
    # Logout endpoint. Minimal description for Swagger.
    # Note: JWT is stateless; client must remove tokens.
    
    # TODO (Optional): Implement token blacklist
    # - Lưu token vào Redis với TTL = expiration time
    # - Check blacklist trong get_current_user dependency
    # 
    # redis_client.setex(
    #     f"blacklist_token:{current_user.id}",
    #     settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    #     "1"
    # )
    
    return {
        "message": "Logged out successfully",
        "user_email": current_user.email,
        "note": "Please remove tokens from client storage (localStorage/sessionStorage)"
    }


# ============= EMAIL VERIFICATION ENDPOINTS =============

@router.post("/forgot-password", response_model=MessageResponse, summary="Yêu cầu đặt lại mật khẩu")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Gửi email đặt lại mật khẩu
    
    Luồng xử lý:
    1. Tìm user theo email
    2. Tạo reset token + thời gian hết hạn
    3. Lưu token vào database
    4. Gửi email (background task)
    5. Trả về message (LUÔN thành công để không lộ email có tồn tại không)
    
    Args:
        request: Email cần reset password
        background_tasks: FastAPI background tasks để gửi email async
        db: Database session
        
    Returns:
        MessageResponse: Thông báo đã gửi email
    """
    # Tìm user theo email
    user = db.query(User).filter(User.email == request.email).first()
    
    if user:
        # Tạo reset token
        reset_token = generate_password_reset_token()
        
        # Tính thời gian hết hạn (1 giờ)
        expires_at = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_EXPIRE_HOURS)
        
        # Lưu token vào database
        user.password_reset_token = reset_token
        user.password_reset_token_expires_at = expires_at
        db.commit()
        
        # Gửi email trong background (không block response)
        background_tasks.add_task(
            send_password_reset_email,
            email=user.email,
            full_name=user.full_name,
            reset_token=reset_token
        )
    
    # LUÔN trả về thành công (bảo mật - không tiết lộ email có tồn tại không)
    return MessageResponse(
        message="Nếu email tồn tại trong hệ thống, chúng tôi đã gửi link đặt lại mật khẩu. Vui lòng kiểm tra hộp thư.",
        success=True
    )


@router.post("/reset-password", response_model=MessageResponse, summary="Đặt lại mật khẩu")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Đặt lại mật khẩu với token từ email
    
    Luồng xử lý:
    1. Tìm user theo reset token
    2. Kiểm tra token chưa hết hạn
    3. Hash mật khẩu mới
    4. Cập nhật password + xóa token
    5. Trả về thành công
    
    Args:
        request: Token + mật khẩu mới
        db: Database session
        
    Returns:
        MessageResponse: Thông báo đã đổi mật khẩu
        
    Raises:
        HTTPException 400: Token không hợp lệ hoặc hết hạn
    """
    # Tìm user theo reset token
    user = db.query(User).filter(User.password_reset_token == request.token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token không hợp lệ hoặc đã được sử dụng"
        )
    
    # Kiểm tra token chưa hết hạn
    if user.password_reset_token_expires_at < datetime.utcnow():
        # Xóa token hết hạn
        user.password_reset_token = None
        user.password_reset_token_expires_at = None
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token đã hết hạn. Vui lòng yêu cầu đặt lại mật khẩu mới."
        )
    
    # Hash mật khẩu mới
    user.password_hash = hash_password(request.new_password)
    
    # Xóa reset token (đã sử dụng)
    user.password_reset_token = None
    user.password_reset_token_expires_at = None
    
    db.commit()
    
    return MessageResponse(
        message="Mật khẩu đã được đặt lại thành công. Vui lòng đăng nhập với mật khẩu mới.",
        success=True
    )


@router.get("/verify-email/{token}", response_model=MessageResponse, summary="Xác thực email")
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Xác thực email với token từ link trong email
    
    Luồng xử lý:
    1. Tìm user theo verification token
    2. Kiểm tra token còn hạn (24 giờ)
    3. Set email_verified = True
    4. Xóa token
    5. Trả về thành công
    
    Args:
        token: Token từ URL (path parameter)
        db: Database session
        
    Returns:
        MessageResponse: Thông báo đã xác thực
        
    Raises:
        HTTPException 400: Token không hợp lệ hoặc hết hạn
    """
    # Tìm user theo verification token
    user = db.query(User).filter(User.email_verification_token == token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token không hợp lệ hoặc đã được sử dụng"
        )
    
    # Kiểm tra đã verify chưa
    if user.email_verified:
        return MessageResponse(
            message="Email đã được xác thực trước đó.",
            success=True
        )
    
    # Kiểm tra token còn hạn (24 giờ từ lúc gửi)
    if user.email_verification_sent_at:
        expires_at = user.email_verification_sent_at + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)
        if datetime.utcnow() > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link xác thực đã hết hạn. Vui lòng yêu cầu gửi lại email xác thực."
            )
    
    # Xác thực email
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_sent_at = None
    
    db.commit()
    
    return MessageResponse(
        message="Email đã được xác thực thành công! Bạn có thể đăng nhập và sử dụng đầy đủ tính năng.",
        success=True
    )


@router.post("/resend-verification", response_model=MessageResponse, summary="Gửi lại email xác thực")
async def resend_verification_email(
    request: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Gửi lại email xác thực cho user chưa verify
    
    Luồng xử lý:
    1. Tìm user theo email
    2. Kiểm tra đã verify chưa
    3. Tạo token mới
    4. Gửi email
    5. Trả về message
    
    Args:
        request: Email cần gửi lại
        background_tasks: Background tasks
        db: Database session
        
    Returns:
        MessageResponse: Thông báo đã gửi email
    """
    # Tìm user theo email
    user = db.query(User).filter(User.email == request.email).first()
    
    if user:
        # Kiểm tra đã verify chưa
        if user.email_verified:
            return MessageResponse(
                message="Email đã được xác thực trước đó. Bạn có thể đăng nhập bình thường.",
                success=True
            )
        
        # Tạo token mới
        verification_token = generate_verification_token()
        
        # Cập nhật token và thời gian gửi
        user.email_verification_token = verification_token
        user.email_verification_sent_at = datetime.utcnow()
        db.commit()
        
        # Gửi email trong background
        background_tasks.add_task(
            send_verification_email,
            email=user.email,
            full_name=user.full_name,
            verification_token=verification_token
        )
    
    # LUÔN trả về thành công (bảo mật)
    return MessageResponse(
        message="Nếu email tồn tại và chưa được xác thực, chúng tôi đã gửi link xác thực mới. Vui lòng kiểm tra hộp thư.",
        success=True
    )
