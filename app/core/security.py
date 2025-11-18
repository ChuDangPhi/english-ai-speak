"""
Security utilities - Xử lý JWT token và password hashing
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings


# ============= PASSWORD HASHING =============

# Khởi tạo password context với bcrypt
# bcrypt là thuật toán hash mạnh, khó crack
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash password sử dụng bcrypt
    
    Args:
        password: Mật khẩu plain text
        
    Returns:
        Mật khẩu đã hash (không thể reverse về plain text)
        
    Example:
        >>> hash_password("mypassword123")
        '$2b$12$KIXxLV...'
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra password có đúng không
    
    Args:
        plain_password: Password user nhập vào
        hashed_password: Password đã hash trong database
        
    Returns:
        True nếu khớp, False nếu không khớp
        
    Example:
        >>> verify_password("mypassword123", "$2b$12$KIXxLV...")
        True
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============= JWT TOKEN =============

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Tạo JWT access token
    
    Args:
        data: Dictionary chứa thông tin cần encode (user_id, username, role)
        expires_delta: Thời gian sống của token (mặc định 30 phút)
        
    Returns:
        JWT token string
        
    Example:
        >>> create_access_token({"sub": "user123", "email": "user@example.com"})
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    # Copy data để không thay đổi dict gốc
    to_encode = data.copy()
    
    # Tính thời gian hết hạn
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Mặc định 30 phút (lấy từ config)
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Thêm thông tin vào payload
    to_encode.update({
        "exp": expire,              # Expiration time
        "type": "access"            # Token type để phân biệt access vs refresh
    })
    
    # Encode JWT token
    # SECRET_KEY: Key bí mật để mã hóa (KHÔNG được để lộ)
    # ALGORITHM: Thuật toán mã hóa (HS256)
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Tạo JWT refresh token (thời gian sống lâu hơn)
    
    Args:
        data: Dictionary chứa thông tin cần encode
        
    Returns:
        JWT refresh token string
        
    Example:
        >>> create_refresh_token({"sub": "user123", "email": "user@example.com"})
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    to_encode = data.copy()
    
    # Refresh token sống lâu hơn (7 ngày)
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Thêm thông tin vào payload
    to_encode.update({
        "exp": expire,              # Expiration time
        "type": "refresh"           # Token type: refresh (quan trọng!)
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Giải mã JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary chứa payload nếu hợp lệ, None nếu không hợp lệ
        
    Example:
        >>> decode_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        {'sub': 'user123', 'role': 'student', 'exp': 1234567890}
    """
    try:
        # Giải mã token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        # Token không hợp lệ hoặc đã hết hạn
        return None