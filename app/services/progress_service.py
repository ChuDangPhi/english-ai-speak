"""
Progress Service - Xử lý tiến độ học tập & Streak

=== CHỨC NĂNG ===
1. Cập nhật tiến độ sau mỗi lesson
2. Quản lý streak (chuỗi ngày học)
3. Cập nhật thống kê hàng ngày

=== STREAK LOGIC ===
- +1 streak nếu học ngày mới
- Reset về 0 nếu bỏ 1 ngày
- Longest streak được lưu lại
"""
from datetime import date, timedelta
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.progress import UserStreak, DailyStats, UserLessonProgress, LessonStatus
from app.models.attempt import LessonAttempt


class ProgressService:
    """Service quản lý tiến độ học tập"""
    
    # ============================================================
    # STREAK MANAGEMENT
    # ============================================================
    
    def update_streak(self, db: Session, user_id: int) -> Dict:
        """
        Cập nhật streak cho user
        
        Logic:
        - Nếu đã học hôm nay: không thay đổi
        - Nếu học liên tiếp từ hôm qua: +1 streak
        - Nếu bỏ > 1 ngày: reset streak = 1
        
        Returns:
            Dict với current_streak, longest_streak, streak_increased
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        streak = db.query(UserStreak).filter(
            UserStreak.user_id == user_id
        ).first()
        
        # Tạo mới nếu chưa có
        if not streak:
            streak = UserStreak(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_activity_date=today
            )
            db.add(streak)
            db.flush()
            return {
                "current_streak": 1,
                "longest_streak": 1,
                "streak_increased": True
            }
        
        # Đã học hôm nay rồi
        if streak.last_activity_date == today:
            return {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "streak_increased": False
            }
        
        # Kiểm tra liên tục
        streak_increased = True
        if streak.last_activity_date == yesterday:
            # Tiếp tục streak
            streak.current_streak += 1
        else:
            # Bị gián đoạn, reset
            streak.current_streak = 1
        
        streak.last_activity_date = today
        
        # Cập nhật longest streak
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        
        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "streak_increased": streak_increased
        }
    
    def get_streak_info(self, db: Session, user_id: int) -> Dict:
        """Lấy thông tin streak cho user"""
        today = date.today()
        
        streak = db.query(UserStreak).filter(
            UserStreak.user_id == user_id
        ).first()
        
        if not streak:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "learned_today": False,
                "needs_activity_today": True
            }
        
        learned_today = streak.last_activity_date == today
        
        # Kiểm tra streak có bị broken không
        if streak.last_activity_date:
            days_since = (today - streak.last_activity_date).days
            if days_since > 1:
                # Streak đã bị gián đoạn
                current = 0
            else:
                current = streak.current_streak
        else:
            current = 0
        
        return {
            "current_streak": current,
            "longest_streak": streak.longest_streak,
            "learned_today": learned_today,
            "last_activity_date": streak.last_activity_date,
            "needs_activity_today": not learned_today
        }
    
    # ============================================================
    # DAILY STATS
    # ============================================================
    
    def update_daily_stats(
        self,
        db: Session,
        user_id: int,
        duration_seconds: int = 0,
        lesson_completed: bool = False
    ):
        """Cập nhật thống kê hàng ngày"""
        today = date.today()
        
        stats = db.query(DailyStats).filter(
            DailyStats.user_id == user_id,
            DailyStats.date == today
        ).first()
        
        if not stats:
            stats = DailyStats(
                user_id=user_id,
                date=today,
                lessons_completed=0,
                vocabulary_reviewed=0,
                minutes_studied=0,
                experience_points_earned=0
            )
            db.add(stats)
        
        if lesson_completed:
            stats.lessons_completed += 1
        stats.minutes_studied += duration_seconds // 60
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_user_stats_summary(self, db: Session, user_id: int) -> Dict:
        """Lấy tổng hợp thống kê cho user"""
        
        # Số lessons đã hoàn thành
        lessons_completed = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.status == LessonStatus.COMPLETED
        ).count()
        
        # Tổng thời gian học
        total_time = db.query(func.sum(DailyStats.minutes_studied)).filter(
            DailyStats.user_id == user_id
        ).scalar() or 0
        
        # Điểm trung bình
        avg_score = db.query(func.avg(LessonAttempt.overall_score)).filter(
            LessonAttempt.user_id == user_id,
            LessonAttempt.is_passed == True
        ).scalar() or 0
        
        # Streak info
        streak_info = self.get_streak_info(db, user_id)
        
        return {
            "lessons_completed": lessons_completed,
            "total_study_minutes": total_time,
            "average_score": round(float(avg_score), 1) if avg_score else 0,
            "current_streak": streak_info.get("current_streak", 0),
            "longest_streak": streak_info.get("longest_streak", 0)
        }


# Singleton instance
progress_service = ProgressService()
