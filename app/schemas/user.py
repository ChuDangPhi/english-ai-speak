"""
User schemas - Định nghĩa cấu trúc dữ liệu input/output
Pydantic sẽ tự động validate dữ liệu
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


# ============= REQUEST SCHEMAS (Input client -> server) =============

class UserRegister(BaseModel):
    """
    Schema cho đăng ký tài khoản mới
    Client gửi lên server
    """
    email: EmailStr = Field(..., description="Email hợp lệ", examples=["user@example.com"])
    password: str = Field(..., min_length=6, max_length=100, description="Mật khẩu tối thiểu 6 ký tự", examples=["password123"])
    full_name: Optional[str] = Field(None, max_length=100, description="Họ tên đầy đủ", examples=["Nguyễn Văn A"])
    
    @validator('password')
    def password_strength(cls, v):
        """
        Validator: Kiểm tra độ mạnh mật khẩu
        """
        if not any(char.isdigit() for char in v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 số')
        if not any(char.isalpha() for char in v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 chữ cái')
        return v


class UserLogin(BaseModel):
    """
    Schema cho đăng nhập
    Client gửi lên server
    """
    email: EmailStr = Field(..., description="Email", examples=["user@example.com"])
    password: str = Field(..., description="Mật khẩu", examples=["password123"])


class RefreshTokenRequest(BaseModel):
    """
    Schema cho refresh token request
    Client gửi refresh_token để lấy access_token mới
    """
    refresh_token: str = Field(..., description="Refresh token nhận được khi đăng ký/đăng nhập")


# ============= RESPONSE SCHEMAS (Output sever => client) =============

class UserResponse(BaseModel):
    """
    Schema trả về thông tin user (KHÔNG bao gồm password_hash)
    Server trả về client
    """
    id: int = Field(..., description="ID của user")
    email: str = Field(..., description="Email")
    full_name: Optional[str] = Field(None, description="Họ tên")
    avatar_url: Optional[str] = Field(None, description="URL avatar")
    current_level: str = Field(..., description="Trình độ hiện tại")
    is_active: bool = Field(..., description="Trạng thái active")
    role: str = Field(default="user", description="Vai trò người dùng")
    created_at: datetime = Field(..., description="Thời gian tạo")
    
    class Config:
        """
        Config cho phép convert từ SQLAlchemy model sang Pydantic
        """
        from_attributes = True  # Đọc data từ attributes (SQLAlchemy model)


class TokenResponse(BaseModel):
    """
    Schema trả về token sau khi đăng nhập thành công
    """
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Loại token")
    user: UserResponse = Field(..., description="Thông tin user")


# ============= PASSWORD RESET & EMAIL VERIFICATION SCHEMAS =============

class ForgotPasswordRequest(BaseModel):
    """
    Schema cho yêu cầu quên mật khẩu
    Client gửi email để nhận link reset
    """
    email: EmailStr = Field(..., description="Email đã đăng ký", examples=["user@example.com"])


class ResetPasswordRequest(BaseModel):
    """
    Schema cho đặt lại mật khẩu
    Client gửi token (từ email) + mật khẩu mới
    """
    token: str = Field(..., description="Token từ email reset password")
    new_password: str = Field(..., min_length=6, max_length=100, description="Mật khẩu mới")
    
    @validator('new_password')
    def password_strength(cls, v):
        """Kiểm tra độ mạnh mật khẩu mới"""
        if not any(char.isdigit() for char in v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 số')
        if not any(char.isalpha() for char in v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 chữ cái')
        return v


class ResendVerificationRequest(BaseModel):
    """
    Schema cho yêu cầu gửi lại email xác thực
    """
    email: EmailStr = Field(..., description="Email cần gửi lại xác thực", examples=["user@example.com"])


class MessageResponse(BaseModel):
    """
    Schema response đơn giản chỉ chứa message
    Dùng cho các API không cần trả về data phức tạp
    """
    message: str = Field(..., description="Thông báo kết quả")
    success: bool = Field(default=True, description="Trạng thái thành công")