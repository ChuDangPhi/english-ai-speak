"""
Token Utility - Tạo token ngẫu nhiên an toàn

Sử dụng secrets module của Python để tạo token cryptographically secure.
Token này được dùng cho:
- Email verification
- Password reset
"""
import secrets
from typing import Optional


def generate_secure_token(length: int = 32) -> str:
    """
    Tạo token ngẫu nhiên an toàn (cryptographically secure)
    
    Sử dụng secrets.token_urlsafe() vì:
    - An toàn cho cryptographic purposes
    - URL-safe (có thể đưa vào URL mà không cần encode)
    - Không có ký tự đặc biệt gây lỗi
    
    Args:
        length: Số bytes để tạo token (mặc định 32)
                Token thực tế sẽ dài hơn do base64 encoding
                32 bytes → khoảng 43 ký tự
    
    Returns:
        str: Token ngẫu nhiên URL-safe
        
    Example:
        >>> token = generate_secure_token()
        >>> print(token)
        'dGhpcyBpcyBhIHNlY3VyZSB0b2tlbiBleGFtcGxl'
    """
    return secrets.token_urlsafe(length)


def generate_verification_token() -> str:
    """
    Tạo token cho email verification
    
    Returns:
        str: Token 43 ký tự (32 bytes)
    """
    return generate_secure_token(32)


def generate_password_reset_token() -> str:
    """
    Tạo token cho password reset
    
    Returns:
        str: Token 43 ký tự (32 bytes)
    """
    return generate_secure_token(32)
