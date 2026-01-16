"""
Email Utility - Gửi email xác thực và reset password

Sử dụng FastAPI-Mail để gửi email qua SMTP (Gmail).
Tích hợp Jinja2 để render HTML templates.
"""
import os
from pathlib import Path
from typing import Optional
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from jinja2 import Environment, FileSystemLoader

from app.config import settings


# ===== CẤU HÌNH FASTAPI-MAIL =====
# Chỉ tạo config khi có SMTP credentials
def get_mail_config() -> Optional[ConnectionConfig]:
    """
    Tạo cấu hình email từ settings
    
    Returns:
        ConnectionConfig nếu có credentials, None nếu không
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return None
    
    return ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.EMAILS_FROM_EMAIL or settings.SMTP_USER,
        MAIL_FROM_NAME=settings.EMAILS_FROM_NAME,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_STARTTLS=True,  # Gmail yêu cầu TLS
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates"
    )


# ===== JINJA2 TEMPLATE ENGINE =====
# Tạo environment để render HTML templates
template_dir = Path(__file__).parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=True  # Tự động escape HTML để tránh XSS
)


async def send_verification_email(
    email: str,
    full_name: Optional[str],
    verification_token: str
) -> bool:
    """
    Gửi email xác thực tài khoản
    
    Flow:
    1. Tạo link verification với token
    2. Render HTML template với dữ liệu
    3. Gửi email qua SMTP
    
    Args:
        email: Email người nhận
        full_name: Tên người nhận (hiển thị trong email)
        verification_token: Token để xác thực
        
    Returns:
        bool: True nếu gửi thành công, False nếu thất bại
    """
    config = get_mail_config()
    if not config:
        print("⚠️ SMTP not configured. Email verification skipped.")
        print(f"   Would send verification email to: {email}")
        print(f"   Token: {verification_token}")
        return False
    
    try:
        # Tạo verification link - trỏ đến đúng path của file verify-email.html
        verification_link = f"{settings.FRONTEND_URL}/Register_Login/verify-email.html?token={verification_token}"
        
        # Render HTML template
        template = jinja_env.get_template("email_verification.html")
        html_content = template.render(
            full_name=full_name or "bạn",
            verification_link=verification_link,
            app_name=settings.APP_NAME,
            expire_hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
        )
        
        # Tạo message
        message = MessageSchema(
            subject=f"[{settings.APP_NAME}] Xác thực email của bạn",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html
        )
        
        # Gửi email
        fm = FastMail(config)
        await fm.send_message(message)
        
        print(f"✅ Verification email sent to: {email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send verification email: {str(e)}")
        return False


async def send_password_reset_email(
    email: str,
    full_name: Optional[str],
    reset_token: str
) -> bool:
    """
    Gửi email đặt lại mật khẩu
    
    Flow:
    1. Tạo link reset với token
    2. Render HTML template
    3. Gửi email qua SMTP
    
    Args:
        email: Email người nhận
        full_name: Tên người nhận
        reset_token: Token để reset password
        
    Returns:
        bool: True nếu gửi thành công, False nếu thất bại
    """
    config = get_mail_config()
    if not config:
        print("⚠️ SMTP not configured. Password reset email skipped.")
        print(f"   Would send reset email to: {email}")
        print(f"   Token: {reset_token}")
        return False
    
    try:
        # Tạo reset link - trỏ đến đúng path của file reset-password.html
        reset_link = f"{settings.FRONTEND_URL}/Register_Login/reset-password.html?token={reset_token}"
        
        # Render HTML template
        template = jinja_env.get_template("password_reset.html")
        html_content = template.render(
            full_name=full_name or "bạn",
            reset_link=reset_link,
            app_name=settings.APP_NAME,
            expire_hours=settings.PASSWORD_RESET_EXPIRE_HOURS
        )
        
        # Tạo message
        message = MessageSchema(
            subject=f"[{settings.APP_NAME}] Đặt lại mật khẩu",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html
        )
        
        # Gửi email
        fm = FastMail(config)
        await fm.send_message(message)
        
        print(f"✅ Password reset email sent to: {email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send password reset email: {str(e)}")
        return False


def is_email_configured() -> bool:
    """
    Kiểm tra xem SMTP đã được cấu hình chưa
    
    Returns:
        bool: True nếu có SMTP credentials
    """
    return bool(settings.SMTP_USER and settings.SMTP_PASSWORD)
