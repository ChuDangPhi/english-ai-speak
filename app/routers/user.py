"""
User Router - API endpoints cho User Profile và Settings

=== ENDPOINTS ===
1. GET /user/profile - Lấy thông tin profile
2. PUT /user/profile - Cập nhật profile  
3. PUT /user/change-password - Đổi mật khẩu
4. POST /user/avatar - Upload avatar
5. GET /user/settings - Lấy settings
6. PUT /user/settings - Cập nhật settings
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os
import uuid
from pathlib import Path

from app.database import get_db
from app.models.user import User, UserSettings
from app.models import UserStreak, UserVocabulary
from app.core.dependencies import get_current_user
from app.core.security import verify_password, hash_password
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/user",
    tags=["User Profile"]
)


# ============================================================
# SCHEMAS
# ============================================================

class UserProfileResponse(BaseModel):
    """Response khi lấy profile"""
    id: int
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    current_level: str = "beginner"
    is_active: bool = True
    role: str = "user"
    email_verified: bool = False
    created_at: Optional[datetime] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    
    # Stats
    days_streak: int = 0
    words_learned: int = 0
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Request body để cập nhật profile"""
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    current_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")


class ChangePasswordRequest(BaseModel):
    """Request body để đổi mật khẩu"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)


class UserSettingsResponse(BaseModel):
    """Response khi lấy settings"""
    ai_voice_type: str = "female_us"
    daily_goal_minutes: int = 15
    notification_enabled: bool = True
    theme: str = "dark"
    
    class Config:
        from_attributes = True


class UserSettingsUpdate(BaseModel):
    """Request body để cập nhật settings"""
    ai_voice_type: Optional[str] = None
    daily_goal_minutes: Optional[int] = Field(None, ge=5, le=120)
    notification_enabled: Optional[bool] = None
    theme: Optional[str] = None


# ============================================================
# GET /user/profile - Lấy thông tin profile
# ============================================================
@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📋 LẤY THÔNG TIN PROFILE
    
    Trả về thông tin cá nhân của user đang đăng nhập
    bao gồm stats: days_streak, words_learned
    """
    # Get streak
    streak = db.query(UserStreak).filter(
        UserStreak.user_id == current_user.id
    ).first()
    days_streak = streak.current_streak if streak else 0
    
    # Get words learned count
    words_learned = db.query(UserVocabulary).filter(
        UserVocabulary.user_id == current_user.id,
        UserVocabulary.mastery_level >= 3  # Đã học thuộc
    ).count()
    
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        current_level=current_user.current_level or "beginner",
        is_active=current_user.is_active,
        role=current_user.role,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        days_streak=days_streak,
        words_learned=words_learned
    )


# ============================================================
# PUT /user/profile - Cập nhật profile
# ============================================================
@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✏️ CẬP NHẬT PROFILE
    
    Cập nhật thông tin cá nhân: full_name, phone, bio, current_level
    """
    # Update fields nếu có
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.phone is not None:
        current_user.phone = data.phone
    if data.bio is not None:
        current_user.bio = data.bio
    if data.current_level is not None:
        current_user.current_level = data.current_level
    
    # Commit changes
    db.commit()
    db.refresh(current_user)
    
    # Get stats
    streak = db.query(UserStreak).filter(
        UserStreak.user_id == current_user.id
    ).first()
    days_streak = streak.current_streak if streak else 0
    
    words_learned = db.query(UserVocabulary).filter(
        UserVocabulary.user_id == current_user.id,
        UserVocabulary.mastery_level >= 3
    ).count()
    
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        bio=current_user.bio,
        avatar_url=current_user.avatar_url,
        current_level=current_user.current_level or "beginner",
        is_active=current_user.is_active,
        role=current_user.role,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        days_streak=days_streak,
        words_learned=words_learned
    )


# ============================================================
# PUT /user/change-password - Đổi mật khẩu
# ============================================================
@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🔐 ĐỔI MẬT KHẨU
    
    Yêu cầu nhập mật khẩu hiện tại để xác thực
    """
    # Verify current password
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không đúng"
        )
    
    # Check new password confirmation
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Xác nhận mật khẩu không khớp"
        )
    
    # Check password strength
    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu mới phải có ít nhất 6 ký tự"
        )
    
    # Update password
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    
    return {"success": True, "message": "Đổi mật khẩu thành công"}


# ============================================================
# POST /user/avatar - Upload avatar
# ============================================================
@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📷 UPLOAD AVATAR
    
    Chấp nhận file ảnh: jpg, jpeg, png, gif
    Kích thước tối đa: 5MB
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ chấp nhận file ảnh (jpg, png, gif)"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size (max 5MB)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File ảnh tối đa 5MB"
        )
    
    # Create upload directory
    upload_dir = Path("uploads/avatars")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = upload_dir / filename
    
    # Delete old avatar if exists
    if current_user.avatar_url:
        old_path = Path(current_user.avatar_url.lstrip("/"))
        if old_path.exists():
            try:
                old_path.unlink()
            except:
                pass
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Update user avatar_url
    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar_url = avatar_url
    db.commit()
    
    return {
        "success": True,
        "avatar_url": avatar_url,
        "message": "Upload avatar thành công"
    }


# ============================================================
# GET /user/settings - Lấy settings
# ============================================================
@router.get("/settings", response_model=UserSettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ⚙️ LẤY CÀI ĐẶT USER
    
    Trả về settings: ai_voice_type, daily_goal, notification, theme
    """
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        # Tạo settings mặc định nếu chưa có
        settings = UserSettings(
            user_id=current_user.id,
            ai_voice_type="female_us",
            daily_goal_minutes=15,
            notification_enabled=True,
            theme="dark"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return UserSettingsResponse(
        ai_voice_type=settings.ai_voice_type,
        daily_goal_minutes=settings.daily_goal_minutes,
        notification_enabled=settings.notification_enabled,
        theme=settings.theme
    )


# ============================================================
# PUT /user/settings - Cập nhật settings
# ============================================================
@router.put("/settings", response_model=UserSettingsResponse)
async def update_settings(
    data: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ⚙️ CẬP NHẬT CÀI ĐẶT
    
    Cập nhật các cài đặt cá nhân
    """
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    # Update fields
    if data.ai_voice_type is not None:
        settings.ai_voice_type = data.ai_voice_type
    if data.daily_goal_minutes is not None:
        settings.daily_goal_minutes = data.daily_goal_minutes
    if data.notification_enabled is not None:
        settings.notification_enabled = data.notification_enabled
    if data.theme is not None:
        settings.theme = data.theme
    
    db.commit()
    db.refresh(settings)
    
    return UserSettingsResponse(
        ai_voice_type=settings.ai_voice_type,
        daily_goal_minutes=settings.daily_goal_minutes,
        notification_enabled=settings.notification_enabled,
        theme=settings.theme
    )
