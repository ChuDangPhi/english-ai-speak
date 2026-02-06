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
