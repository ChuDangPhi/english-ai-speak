"""
Dependencies - Các hàm dependency dùng để bảo vệ routes
FastAPI sẽ tự động gọi các hàm này TRƯỚC KHI endpoint chính chạy
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.config import settings


# ============= HTTP BEARER SECURITY SCHEME =============

# HTTPBearer: Tự động lấy token từ header "Authorization: Bearer <token>"
# auto_error=True: Tự động trả 403 nếu không có header Authorization
security = HTTPBearer()


# ============= GET CURRENT USER DEPENDENCY =============

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency để lấy user hiện tại từ JWT token
    
    WORKFLOW:
    1. Lấy token từ header "Authorization: Bearer <token>"
    2. Decode JWT token để lấy user_id
    3. Tìm user trong database theo user_id
    4. Kiểm tra user có active không
    5. Return user object
    
    Args:
        credentials: HTTPAuthorizationCredentials 
            - Được inject tự động bởi HTTPBearer()
            - Chứa: credentials.credentials = "token_string"
        db: Database session
            - Được inject tự động bởi Depends(get_db)
    
    Returns:
        User: User object từ database
    
    Raises:
        HTTPException 401: Nếu token invalid, expired, hoặc user không tồn tại
        HTTPException 403: Nếu user bị deactivate
    
    Example usage trong route:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"message": f"Hello {current_user.email}"}
    """
    
    # Lấy token string từ credentials
    # credentials.credentials chứa phần sau "Bearer "
    token = credentials.credentials
    
    # Exception sẽ raise nếu token invalid
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # ===== BƯỚC 1: DECODE JWT TOKEN =====
        # jwt.decode() sẽ:
        # - Verify signature với SECRET_KEY
        # - Check expiration time
        # - Return payload dict nếu OK
        payload = jwt.decode(
            token,                      # Token string
            settings.SECRET_KEY,        # Secret key để verify
            algorithms=[settings.ALGORITHM]  # Algorithm: HS256
        )
        
        # ===== BƯỚC 2: LẤY USER_ID TỪ PAYLOAD =====
        # Payload structure: {"sub": "user_id", "email": "...", "exp": ...}
        # "sub" (subject) là convention để lưu user identifier
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
    except JWTError as e:
        # JWTError bao gồm:
        # - ExpiredSignatureError: Token hết hạn
        # - JWTClaimsError: Claims không hợp lệ
        # - JWTError: Lỗi khác (signature invalid, etc.)
        raise credentials_exception
    
    # ===== BƯỚC 3: TÌM USER TRONG DATABASE =====
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        # User không tồn tại (có thể đã bị xóa)
        raise credentials_exception
    
    # ===== BƯỚC 4: CHECK USER ACTIVE =====
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # ===== BƯỚC 5: RETURN USER =====
    # FastAPI sẽ inject user này vào endpoint parameter
    return user


# ============= GET CURRENT ACTIVE USER DEPENDENCY =============

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency bổ sung để lấy user active
    
    WORKFLOW:
    1. Gọi get_current_user() (đã verify token + check active)
    2. Có thể thêm logic check premium, verified email, etc.
    3. Return user
    
    Note: Hiện tại chỉ wrap get_current_user()
          Có thể mở rộng sau này để check:
          - Email verified
          - Premium account
          - Subscription active
          - etc.
    
    Args:
        current_user: User object từ get_current_user()
    
    Returns:
        User: User object
    
    Example usage:
        @router.get("/premium-feature")
        def premium_route(user: User = Depends(get_current_active_user)):
            # Có thể thêm logic check premium ở đây
            if user.subscription_type != "premium":
                raise HTTPException(403, "Premium only")
            return {"data": "premium content"}
    """
    
    # Hiện tại chỉ return user
    # Sau này có thể thêm check:
    # if not current_user.email_verified:
    #     raise HTTPException(403, "Email not verified")
    # if not current_user.is_premium:
    #     raise HTTPException(403, "Premium required")
    
    return current_user


# ============= OPTIONAL: GET CURRENT USER OR NONE =============

def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> User | None:
    """
    Dependency để lấy user hiện tại HOẶC None nếu không có token
    
    Use case: Endpoint có thể dùng cho cả guest và logged-in user
    
    Example:
        @router.get("/posts")
        def get_posts(current_user: User | None = Depends(get_current_user_optional)):
            if current_user:
                # Logged in: Show personalized posts
                return get_personalized_posts(current_user)
            else:
                # Guest: Show public posts only
                return get_public_posts()
    
    Args:
        credentials: Có thể None nếu không có token
        db: Database session
    
    Returns:
        User | None: User nếu có token hợp lệ, None nếu không có token
    """
    
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if user and user.is_active:
            return user
        
        return None
        
    except JWTError:
        return None
