"""
Progress Service - Xử lý tiến độ học tập, XP, Level, Streak

=== CHỨC NĂNG ===
1. Cập nhật tiến độ sau mỗi lesson
2. Tính và cập nhật XP (Experience Points)
3. Xử lý level up
4. Quản lý streak (chuỗi ngày học)
5. Cập nhật thống kê hàng ngày

=== XP SYSTEM ===
- Complete vocabulary lesson: 50 XP
- Complete pronunciation lesson: 75 XP  
- Complete conversation lesson: 100 XP
- Bonus for high score (>90): +25 XP
- Streak bonus: current_streak * 5 XP

=== LEVEL SYSTEM ===
- Level 1: 0-99 XP
- Level 2: 100-299 XP
- Level 3: 300-599 XP
- Level N: sum(i*100 for i in range(1,N)) XP

=== STREAK LOGIC ===
- +1 streak nếu học ngày mới
- Reset về 0 nếu bỏ 1 ngày
- Longest streak được lưu lại
"""
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    UserProgress, UserLessonProgress, UserVocabulary, UserStreak,
    DailyStats, LessonAttempt, Lesson, Topic, LessonStatus, LessonType
)


class ProgressService:
    """Service quản lý tiến độ học tập"""
    
    # XP configuration
    XP_VOCABULARY_LESSON = 50
    XP_PRONUNCIATION_LESSON = 75
    XP_CONVERSATION_LESSON = 100
    XP_HIGH_SCORE_BONUS = 25  # Score >= 90
    XP_PERFECT_SCORE_BONUS = 50  # Score = 100
    HIGH_SCORE_THRESHOLD = 90
    
    # Level configuration
    def get_xp_for_level(self, level: int) -> int:
        """Tính tổng XP cần để đạt level"""
        return sum(i * 100 for i in range(1, level))
    
    def get_level_from_xp(self, xp: int) -> int:
        """Tính level từ XP hiện tại"""
        level = 1
        while self.get_xp_for_level(level + 1) <= xp:
            level += 1
        return level
    
    def calculate_xp_to_next_level(self, current_level: int, current_xp: int) -> int:
        """Tính XP cần để lên level tiếp theo"""
        xp_for_next = self.get_xp_for_level(current_level + 1)
        return max(xp_for_next - current_xp, 0)
    
    # ============================================================
    # LESSON COMPLETION
    # ============================================================
    
    def on_lesson_completed(
        self,
        db: Session,
        user_id: int,
        lesson_id: int,
        score: float,
        duration_seconds: int
    ) -> Dict:
        """
        Xử lý khi user hoàn thành lesson
        
        Returns:
            Dict với thông tin XP earned, level up, streak update
        """
        # 1. Get lesson info
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            return {"error": "Lesson not found"}
        
        # 2. Calculate XP earned
        xp_earned = self._calculate_lesson_xp(lesson.lesson_type, score)
        
        # 3. Update user progress
        progress = self._get_or_create_user_progress(db, user_id)
        old_level = progress.current_level
        
        progress.total_experience_points += xp_earned
        progress.current_level = self.get_level_from_xp(progress.total_experience_points)
        
        level_up = progress.current_level > old_level
        
        # 4. Update lesson progress
        lesson_progress = self._update_lesson_progress(
            db, user_id, lesson_id, score
        )
        
        # 5. Update topic progress
        self._update_topic_progress(db, user_id, lesson.topic_id)
        
        # 6. Update streak
        streak_info = self.update_streak(db, user_id)
        
        # Add streak bonus XP
        if streak_info.get("streak_increased"):
            streak_bonus = streak_info.get("current_streak", 1) * 5
            progress.total_experience_points += streak_bonus
            xp_earned += streak_bonus
        
        # 7. Update daily stats
        self._update_daily_stats(db, user_id, duration_seconds, xp_earned)
        
        # 8. Unlock next lesson if passed
        passing_score = float(lesson.passing_score) if lesson.passing_score else 70.0
        if score >= passing_score:
            self._unlock_next_lesson(db, user_id, lesson)
        
        db.commit()
        
        return {
            "xp_earned": xp_earned,
            "total_xp": progress.total_experience_points,
            "current_level": progress.current_level,
            "level_up": level_up,
            "xp_to_next_level": self.calculate_xp_to_next_level(
                progress.current_level, 
                progress.total_experience_points
            ),
            "streak": streak_info
        }
    
    def _calculate_lesson_xp(self, lesson_type: LessonType, score: float) -> int:
        """Tính XP cho lesson dựa vào type và score"""
        
        # Base XP by type
        if lesson_type == LessonType.VOCABULARY_MATCHING:
            base_xp = self.XP_VOCABULARY_LESSON
        elif lesson_type == LessonType.PRONUNCIATION:
            base_xp = self.XP_PRONUNCIATION_LESSON
        elif lesson_type == LessonType.CONVERSATION:
            base_xp = self.XP_CONVERSATION_LESSON
        else:
            base_xp = 50  # Default
        
        # Bonus for high score
        bonus = 0
        if score >= 100:
            bonus = self.XP_PERFECT_SCORE_BONUS
        elif score >= self.HIGH_SCORE_THRESHOLD:
            bonus = self.XP_HIGH_SCORE_BONUS
        
        return base_xp + bonus
    
    # ============================================================
    # USER PROGRESS
    # ============================================================
    
    def _get_or_create_user_progress(self, db: Session, user_id: int) -> UserProgress:
        """Get hoặc tạo UserProgress record"""
        
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).first()
        
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                total_experience_points=0,
                current_level=1
            )
            db.add(progress)
            db.flush()
        
        return progress
    
    def _update_lesson_progress(
        self,
        db: Session,
        user_id: int,
        lesson_id: int,
        score: float
    ) -> UserLessonProgress:
        """Cập nhật tiến độ lesson"""
        
        lesson_progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id
        ).first()
        
        if not lesson_progress:
            lesson_progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                status=LessonStatus.IN_PROGRESS,
                total_attempts=0
            )
            db.add(lesson_progress)
        
        # Update attempts
        lesson_progress.total_attempts += 1
        lesson_progress.last_attempt_at = datetime.utcnow()
        
        # Update best score
        if lesson_progress.best_score is None or score > float(lesson_progress.best_score):
            lesson_progress.best_score = score
        
        # Get passing score from lesson
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        passing_score = float(lesson.passing_score) if lesson and lesson.passing_score else 70.0
        
        # Update status if passed
        if score >= passing_score:
            if lesson_progress.status != LessonStatus.COMPLETED:
                lesson_progress.first_completed_at = datetime.utcnow()
            lesson_progress.status = LessonStatus.COMPLETED
        elif lesson_progress.status == LessonStatus.AVAILABLE:
            lesson_progress.status = LessonStatus.IN_PROGRESS
        
        return lesson_progress
    
    def _update_topic_progress(self, db: Session, user_id: int, topic_id: int):
        """Cập nhật tiến độ topic"""
        
        # Count completed lessons in topic
        completed_count = db.query(UserLessonProgress).join(Lesson).filter(
            Lesson.topic_id == topic_id,
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.status == LessonStatus.COMPLETED
        ).count()
        
        # Total lessons in topic
        total_count = db.query(Lesson).filter(
            Lesson.topic_id == topic_id,
            Lesson.is_active == True
        ).count()
        
        # Note: If you have a separate topic progress table, update it here
        # For now, this is calculated on-the-fly in the progress router
    
    def _unlock_next_lesson(self, db: Session, user_id: int, current_lesson: Lesson):
        """Unlock lesson tiếp theo trong topic"""
        
        # Find next lesson
        next_lesson = db.query(Lesson).filter(
            Lesson.topic_id == current_lesson.topic_id,
            Lesson.lesson_order > current_lesson.lesson_order,
            Lesson.is_active == True
        ).order_by(Lesson.lesson_order).first()
        
        if next_lesson:
            # Check if progress exists
            next_progress = db.query(UserLessonProgress).filter(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_id == next_lesson.id
            ).first()
            
            if not next_progress:
                next_progress = UserLessonProgress(
                    user_id=user_id,
                    lesson_id=next_lesson.id,
                    status=LessonStatus.AVAILABLE
                )
                db.add(next_progress)
            elif next_progress.status == LessonStatus.LOCKED:
                next_progress.status = LessonStatus.AVAILABLE
    
    # ============================================================
    # STREAK MANAGEMENT
    # ============================================================
    
    def update_streak(self, db: Session, user_id: int) -> Dict:
        """
        Cập nhật streak cho user
        
        Returns:
            Dict với current_streak, longest_streak, streak_increased
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        streak = db.query(UserStreak).filter(
            UserStreak.user_id == user_id
        ).first()
        
        if not streak:
            streak = UserStreak(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_activity_date=today
            )
            db.add(streak)
            return {
                "current_streak": 1,
                "longest_streak": 1,
                "streak_increased": True
            }
        
        streak_increased = False
        
        # Check if already updated today
        if streak.last_activity_date == today:
            return {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "streak_increased": False
            }
        
        # Check streak continuity
        if streak.last_activity_date == yesterday:
            streak.current_streak += 1
            streak_increased = True
        elif streak.last_activity_date and (today - streak.last_activity_date).days > 1:
            # Streak broken
            streak.current_streak = 1
            streak_increased = True  # New streak started
        else:
            streak.current_streak = 1
            streak_increased = True
        
        streak.last_activity_date = today
        
        # Update longest streak
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        
        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "streak_increased": streak_increased
        }
    
    def get_streak_info(self, db: Session, user_id: int) -> Dict:
        """Get streak info cho user"""
        
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
        
        # Check if streak is at risk
        if streak.last_activity_date:
            days_since = (today - streak.last_activity_date).days
            if days_since > 1:
                # Streak already broken
                streak.current_streak = 0
        
        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "learned_today": learned_today,
            "last_activity_date": streak.last_activity_date,
            "needs_activity_today": not learned_today
        }
    
    # ============================================================
    # DAILY STATS
    # ============================================================
    
    def _update_daily_stats(
        self,
        db: Session,
        user_id: int,
        duration_seconds: int,
        xp_earned: int
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
        
        stats.lessons_completed += 1
        stats.minutes_studied += duration_seconds // 60
        stats.experience_points_earned += xp_earned
    
    def update_vocabulary_stats(self, db: Session, user_id: int, vocab_count: int):
        """Cập nhật số từ vựng đã review"""
        
        today = date.today()
        
        stats = db.query(DailyStats).filter(
            DailyStats.user_id == user_id,
            DailyStats.date == today
        ).first()
        
        if stats:
            stats.vocabulary_reviewed += vocab_count
    
    # ============================================================
    # VOCABULARY PROGRESS
    # ============================================================
    
    def update_vocabulary_progress(
        self,
        db: Session,
        user_id: int,
        vocabulary_id: int,
        is_correct: bool
    ):
        """Cập nhật tiến độ học từ vựng"""
        
        user_vocab = db.query(UserVocabulary).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.vocabulary_id == vocabulary_id
        ).first()
        
        if not user_vocab:
            user_vocab = UserVocabulary(
                user_id=user_id,
                vocabulary_id=vocabulary_id,
                times_practiced=0,
                correct_count=0,
                is_mastered=False
            )
            db.add(user_vocab)
        
        user_vocab.times_practiced += 1
        user_vocab.last_reviewed = datetime.utcnow()
        
        if is_correct:
            user_vocab.correct_count += 1
        
        # Check mastery (correct 5 times = mastered)
        if user_vocab.correct_count >= 5:
            user_vocab.is_mastered = True
    
    # ============================================================
    # STATISTICS QUERIES
    # ============================================================
    
    def get_user_stats_summary(self, db: Session, user_id: int) -> Dict:
        """Get tổng hợp thống kê cho user"""
        
        # Total lessons completed
        lessons_completed = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.status == LessonStatus.COMPLETED
        ).count()
        
        # Total vocabulary mastered
        vocab_mastered = db.query(UserVocabulary).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.is_mastered == True
        ).count()
        
        # Total study time
        total_time = db.query(func.sum(DailyStats.minutes_studied)).filter(
            DailyStats.user_id == user_id
        ).scalar() or 0
        
        # Average score
        avg_score = db.query(func.avg(LessonAttempt.overall_score)).filter(
            LessonAttempt.user_id == user_id,
            LessonAttempt.is_passed == True
        ).scalar() or 0
        
        # Streak info
        streak_info = self.get_streak_info(db, user_id)
        
        # User progress
        progress = self._get_or_create_user_progress(db, user_id)
        
        return {
            "lessons_completed": lessons_completed,
            "vocabulary_mastered": vocab_mastered,
            "total_study_minutes": total_time,
            "average_score": round(float(avg_score), 1),
            "current_level": progress.current_level,
            "total_xp": progress.total_experience_points,
            "current_streak": streak_info.get("current_streak", 0),
            "longest_streak": streak_info.get("longest_streak", 0)
        }


# Singleton instance
progress_service = ProgressService()
