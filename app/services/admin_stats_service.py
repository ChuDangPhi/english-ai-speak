"""
Admin Statistics Service - Logic xử lý thống kê cho Admin Dashboard
"""
from typing import Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case, distinct
from decimal import Decimal

from app.models.user import User
from app.models.attempt import LessonAttempt
from app.models.progress import (
    DailyStats, UserStreak, UserLessonProgress, 
    UserProgress, UserVocabulary
)
from app.models.lesson import Lesson
from app.models.topic import Topic
from app.models.vocabulary import Vocabulary
from app.schemas.admin_stats import (
    OverviewStats, UserDistribution, LessonTypeStats,
    UserStatsItem, DailyActivityItem, LessonStatsItem,
    LeaderboardItem, TopLessonItem, UserDetailStats
)


class AdminStatsService:
    """Service class để xử lý các thống kê cho Admin"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============= OVERVIEW STATISTICS =============
    
    def get_overview_stats(self) -> OverviewStats:
        """Lấy thống kê tổng quan hệ thống"""
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # User counts
        total_users = self.db.query(func.count(User.id)).filter(
            User.role == "user"
        ).scalar() or 0
        
        active_users = self.db.query(func.count(User.id)).filter(
            User.role == "user",
            User.is_active == True
        ).scalar() or 0
        
        new_users_today = self.db.query(func.count(User.id)).filter(
            User.role == "user",
            func.date(User.created_at) == today
        ).scalar() or 0
        
        new_users_this_week = self.db.query(func.count(User.id)).filter(
            User.role == "user",
            func.date(User.created_at) >= week_ago
        ).scalar() or 0
        
        new_users_this_month = self.db.query(func.count(User.id)).filter(
            User.role == "user",
            func.date(User.created_at) >= month_ago
        ).scalar() or 0
        
        # Learning stats from LessonAttempt
        lesson_stats = self.db.query(
            func.count(LessonAttempt.id).label("total_completed"),
            func.sum(LessonAttempt.duration_seconds).label("total_seconds"),
            func.avg(LessonAttempt.overall_score).label("avg_score")
        ).filter(
            LessonAttempt.is_completed == True
        ).first()
        
        total_lessons_completed = lesson_stats.total_completed or 0
        total_seconds = lesson_stats.total_seconds or 0
        total_study_time_minutes = int(total_seconds / 60) if total_seconds else 0
        avg_score = float(lesson_stats.avg_score) if lesson_stats.avg_score else None
        
        # Content counts
        total_topics = self.db.query(func.count(Topic.id)).filter(
            Topic.is_active == True
        ).scalar() or 0
        
        total_lessons = self.db.query(func.count(Lesson.id)).filter(
            Lesson.is_active == True
        ).scalar() or 0
        
        total_vocabulary = self.db.query(func.count(Vocabulary.id)).scalar() or 0
        
        return OverviewStats(
            total_users=total_users,
            active_users=active_users,
            new_users_today=new_users_today,
            new_users_this_week=new_users_this_week,
            new_users_this_month=new_users_this_month,
            total_lessons_completed=total_lessons_completed,
            total_study_time_minutes=total_study_time_minutes,
            average_score=round(avg_score, 2) if avg_score else None,
            total_topics=total_topics,
            total_lessons=total_lessons,
            total_vocabulary=total_vocabulary
        )
    
    def get_user_distribution(self) -> UserDistribution:
        """Lấy phân bố users theo level"""
        level_counts = self.db.query(
            User.current_level,
            func.count(User.id).label("count")
        ).filter(
            User.role == "user",
            User.is_active == True
        ).group_by(User.current_level).all()
        
        distribution = {"beginner": 0, "intermediate": 0, "advanced": 0}
        for level, count in level_counts:
            if level in distribution:
                distribution[level] = count
        
        return UserDistribution(**distribution)
    
    def get_lesson_type_stats(self) -> List[LessonTypeStats]:
        """Lấy thống kê theo loại bài học"""
        stats = self.db.query(
            Lesson.lesson_type,
            func.count(LessonAttempt.id).label("total_attempts"),
            func.sum(case((LessonAttempt.is_completed == True, 1), else_=0)).label("completed"),
            func.sum(case((LessonAttempt.is_passed == True, 1), else_=0)).label("passed"),
            func.avg(LessonAttempt.overall_score).label("avg_score")
        ).join(
            LessonAttempt, Lesson.id == LessonAttempt.lesson_id
        ).group_by(Lesson.lesson_type).all()
        
        result = []
        for stat in stats:
            total = stat.total_attempts or 0
            completed = stat.completed or 0
            passed = stat.passed or 0
            
            result.append(LessonTypeStats(
                lesson_type=stat.lesson_type or "unknown",
                total_attempts=total,
                completed_count=completed,
                pass_count=passed,
                average_score=round(float(stat.avg_score), 2) if stat.avg_score else None,
                completion_rate=round((completed / total * 100), 2) if total > 0 else None,
                pass_rate=round((passed / total * 100), 2) if total > 0 else None
            ))
        
        return result
    
    # ============= USER STATISTICS =============
    
    def get_user_stats_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        level: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> dict:
        """Lấy danh sách user với thống kê học tập"""
        query = self.db.query(User).filter(User.role == "user")
        
        # Apply filters
        if search:
            query = query.filter(
                (User.email.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%"))
            )
        
        if level:
            query = query.filter(User.current_level == level)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Count total
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Pagination
        offset = (page - 1) * page_size
        users = query.offset(offset).limit(page_size).all()
        
        # Get stats for each user
        items = []
        for user in users:
            user_stats = self._get_user_learning_stats(user.id)
            items.append(UserStatsItem(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                current_level=user.current_level or "beginner",
                role=user.role,
                is_active=user.is_active or False,
                email_verified=user.email_verified or False,
                created_at=user.created_at,
                **user_stats
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def _get_user_learning_stats(self, user_id: int) -> dict:
        """Lấy thống kê học tập cho 1 user"""
        # Lessons completed
        lessons_completed = self.db.query(func.count(LessonAttempt.id)).filter(
            LessonAttempt.user_id == user_id,
            LessonAttempt.is_completed == True
        ).scalar() or 0
        
        # Study time and average score
        stats = self.db.query(
            func.sum(LessonAttempt.duration_seconds).label("total_seconds"),
            func.avg(LessonAttempt.overall_score).label("avg_score")
        ).filter(
            LessonAttempt.user_id == user_id,
            LessonAttempt.is_completed == True
        ).first()
        
        total_seconds = stats.total_seconds or 0
        study_time_minutes = int(total_seconds / 60) if total_seconds else 0
        avg_score = float(stats.avg_score) if stats.avg_score else None
        
        # Streak
        streak = self.db.query(UserStreak).filter(
            UserStreak.user_id == user_id
        ).first()
        
        current_streak = streak.current_streak if streak else 0
        longest_streak = streak.longest_streak if streak else 0
        
        # Last activity
        last_attempt = self.db.query(LessonAttempt.completed_at).filter(
            LessonAttempt.user_id == user_id
        ).order_by(desc(LessonAttempt.completed_at)).first()
        
        last_activity = last_attempt.completed_at if last_attempt else None
        
        return {
            "total_lessons_completed": lessons_completed,
            "total_study_time_minutes": study_time_minutes,
            "average_score": round(avg_score, 2) if avg_score else None,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity": last_activity
        }
    
    def get_user_detail_stats(self, user_id: int) -> Optional[UserDetailStats]:
        """Lấy thống kê chi tiết cho 1 user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Basic user stats
        user_stats = self._get_user_learning_stats(user_id)
        user_item = UserStatsItem(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            current_level=user.current_level or "beginner",
            role=user.role,
            is_active=user.is_active or False,
            email_verified=user.email_verified or False,
            created_at=user.created_at,
            **user_stats
        )
        
        # Topic progress
        topics_started = self.db.query(func.count(UserProgress.id)).filter(
            UserProgress.user_id == user_id,
            UserProgress.status != "not_started"
        ).scalar() or 0
        
        topics_completed = self.db.query(func.count(UserProgress.id)).filter(
            UserProgress.user_id == user_id,
            UserProgress.status == "completed"
        ).scalar() or 0
        
        # Vocabulary stats
        vocab_stats = self.db.query(
            func.count(UserVocabulary.id).label("total"),
            func.sum(case((UserVocabulary.mastery_level == "mastered", 1), else_=0)).label("mastered"),
            func.sum(case((UserVocabulary.mastery_level == "familiar", 1), else_=0)).label("familiar"),
            func.sum(case((UserVocabulary.mastery_level == "learning", 1), else_=0)).label("learning")
        ).filter(UserVocabulary.user_id == user_id).first()
        
        # Score breakdown by lesson type
        type_scores = self.db.query(
            Lesson.lesson_type,
            func.avg(LessonAttempt.overall_score).label("avg_score")
        ).join(
            LessonAttempt, Lesson.id == LessonAttempt.lesson_id
        ).filter(
            LessonAttempt.user_id == user_id,
            LessonAttempt.is_completed == True
        ).group_by(Lesson.lesson_type).all()
        
        scores_by_type = {ts.lesson_type: float(ts.avg_score) if ts.avg_score else None for ts in type_scores}
        
        # Recent attempts
        recent_attempts = self.db.query(
            LessonAttempt.id,
            LessonAttempt.lesson_id,
            Lesson.title.label("lesson_title"),
            LessonAttempt.overall_score,
            LessonAttempt.is_passed,
            LessonAttempt.completed_at
        ).join(
            Lesson, LessonAttempt.lesson_id == Lesson.id
        ).filter(
            LessonAttempt.user_id == user_id,
            LessonAttempt.is_completed == True
        ).order_by(desc(LessonAttempt.completed_at)).limit(10).all()
        
        recent_list = [
            {
                "attempt_id": a.id,
                "lesson_id": a.lesson_id,
                "lesson_title": a.lesson_title,
                "score": float(a.overall_score) if a.overall_score else None,
                "is_passed": a.is_passed,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None
            }
            for a in recent_attempts
        ]
        
        return UserDetailStats(
            user=user_item,
            topics_started=topics_started,
            topics_completed=topics_completed,
            total_vocabulary_learned=vocab_stats.total or 0,
            vocabulary_mastered=vocab_stats.mastered or 0,
            vocabulary_familiar=vocab_stats.familiar or 0,
            vocabulary_learning=vocab_stats.learning or 0,
            avg_pronunciation_score=round(scores_by_type.get("pronunciation"), 2) if scores_by_type.get("pronunciation") else None,
            avg_vocabulary_score=round(scores_by_type.get("vocabulary_matching"), 2) if scores_by_type.get("vocabulary_matching") else None,
            avg_conversation_score=round(scores_by_type.get("conversation"), 2) if scores_by_type.get("conversation") else None,
            recent_attempts=recent_list
        )
    
    # ============= ACTIVITY STATISTICS =============
    
    def get_activity_stats(
        self,
        days: int = 30,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """Lấy thống kê hoạt động theo thời gian"""
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=days - 1)
        
        # Query daily stats aggregated across all users
        daily_data = self.db.query(
            DailyStats.practice_date,
            func.count(distinct(DailyStats.user_id)).label("active_users"),
            func.sum(DailyStats.total_sessions).label("total_sessions"),
            func.sum(DailyStats.total_minutes).label("total_minutes"),
            func.sum(DailyStats.lessons_completed).label("lessons_completed"),
            func.avg(DailyStats.average_score).label("avg_score")
        ).filter(
            DailyStats.practice_date >= start_date,
            DailyStats.practice_date <= end_date
        ).group_by(DailyStats.practice_date).order_by(DailyStats.practice_date).all()
        
        # Fill missing dates with zeros
        date_dict = {d.practice_date: d for d in daily_data}
        result = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date in date_dict:
                d = date_dict[current_date]
                result.append(DailyActivityItem(
                    date=current_date,
                    active_users=d.active_users or 0,
                    total_sessions=d.total_sessions or 0,
                    total_minutes=d.total_minutes or 0,
                    lessons_completed=d.lessons_completed or 0,
                    average_score=round(float(d.avg_score), 2) if d.avg_score else None
                ))
            else:
                result.append(DailyActivityItem(
                    date=current_date,
                    active_users=0,
                    total_sessions=0,
                    total_minutes=0,
                    lessons_completed=0,
                    average_score=None
                ))
            current_date += timedelta(days=1)
        
        # Summary
        summary = {
            "total_active_users": sum(d.active_users for d in result),
            "total_sessions": sum(d.total_sessions for d in result),
            "total_minutes": sum(d.total_minutes for d in result),
            "total_lessons_completed": sum(d.lessons_completed for d in result),
            "avg_daily_active_users": round(sum(d.active_users for d in result) / len(result), 2) if result else 0
        }
        
        return {
            "period": f"{start_date} to {end_date}",
            "data": result,
            "summary": summary
        }
    
    # ============= LESSON STATISTICS =============
    
    def get_lesson_stats(
        self,
        page: int = 1,
        page_size: int = 20,
        lesson_type: Optional[str] = None,
        topic_id: Optional[int] = None,
        sort_by: str = "total_attempts",
        sort_order: str = "desc"
    ) -> dict:
        """Lấy thống kê cho từng bài học"""
        query = self.db.query(
            Lesson.id.label("lesson_id"),
            Lesson.title.label("lesson_title"),
            Topic.name.label("topic_name"),
            Lesson.lesson_type,
            func.count(LessonAttempt.id).label("total_attempts"),
            func.count(distinct(LessonAttempt.user_id)).label("unique_users"),
            func.sum(case((LessonAttempt.is_completed == True, 1), else_=0)).label("completed_count"),
            func.sum(case((LessonAttempt.is_passed == True, 1), else_=0)).label("pass_count"),
            func.avg(LessonAttempt.overall_score).label("avg_score"),
            func.avg(LessonAttempt.duration_seconds).label("avg_duration")
        ).outerjoin(
            LessonAttempt, Lesson.id == LessonAttempt.lesson_id
        ).join(
            Topic, Lesson.topic_id == Topic.id
        ).filter(
            Lesson.is_active == True
        ).group_by(Lesson.id, Lesson.title, Topic.name, Lesson.lesson_type)
        
        # Apply filters
        if lesson_type:
            query = query.filter(Lesson.lesson_type == lesson_type)
        if topic_id:
            query = query.filter(Lesson.topic_id == topic_id)
        
        # Get all results for counting
        all_results = query.all()
        total = len(all_results)
        
        # Apply sorting and pagination
        # Note: We sort in Python since it's calculated columns
        sort_key = sort_by if sort_by in ["total_attempts", "unique_users", "completed_count", "pass_count", "avg_score"] else "total_attempts"
        
        sorted_results = sorted(
            all_results,
            key=lambda x: getattr(x, sort_key) or 0,
            reverse=(sort_order == "desc")
        )
        
        # Pagination
        offset = (page - 1) * page_size
        paginated = sorted_results[offset:offset + page_size]
        
        items = []
        for r in paginated:
            total_att = r.total_attempts or 0
            completed = r.completed_count or 0
            passed = r.pass_count or 0
            
            items.append(LessonStatsItem(
                lesson_id=r.lesson_id,
                lesson_title=r.lesson_title,
                topic_name=r.topic_name,
                lesson_type=r.lesson_type or "unknown",
                total_attempts=total_att,
                unique_users=r.unique_users or 0,
                completed_count=completed,
                pass_count=passed,
                average_score=round(float(r.avg_score), 2) if r.avg_score else None,
                completion_rate=round((completed / total_att * 100), 2) if total_att > 0 else None,
                pass_rate=round((passed / total_att * 100), 2) if total_att > 0 else None,
                avg_duration_seconds=int(r.avg_duration) if r.avg_duration else None
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def get_top_lessons(self, metric: str = "attempts", limit: int = 10) -> List[TopLessonItem]:
        """Lấy top lessons theo metric"""
        query = self.db.query(
            Lesson.id.label("lesson_id"),
            Lesson.title.label("lesson_title"),
            Topic.name.label("topic_name"),
            func.count(LessonAttempt.id).label("total_attempts"),
            func.avg(LessonAttempt.overall_score).label("avg_score")
        ).outerjoin(
            LessonAttempt, Lesson.id == LessonAttempt.lesson_id
        ).join(
            Topic, Lesson.topic_id == Topic.id
        ).filter(
            Lesson.is_active == True
        ).group_by(Lesson.id, Lesson.title, Topic.name)
        
        results = query.all()
        
        if metric == "attempts":
            sorted_results = sorted(results, key=lambda x: x.total_attempts or 0, reverse=True)
            return [
                TopLessonItem(
                    lesson_id=r.lesson_id,
                    lesson_title=r.lesson_title,
                    topic_name=r.topic_name,
                    value=float(r.total_attempts or 0),
                    metric="attempts"
                )
                for r in sorted_results[:limit]
            ]
        elif metric == "avg_score":
            # Filter out lessons with no attempts
            filtered = [r for r in results if r.avg_score is not None]
            sorted_results = sorted(filtered, key=lambda x: float(x.avg_score), reverse=True)
            return [
                TopLessonItem(
                    lesson_id=r.lesson_id,
                    lesson_title=r.lesson_title,
                    topic_name=r.topic_name,
                    value=round(float(r.avg_score), 2),
                    metric="avg_score"
                )
                for r in sorted_results[:limit]
            ]
        
        return []
    
    # ============= LEADERBOARD =============
    
    def get_leaderboard(
        self,
        metric: str = "score",
        limit: int = 10,
        period: Optional[str] = None  # "this_week", "this_month", or None for all_time
    ) -> List[LeaderboardItem]:
        """Lấy bảng xếp hạng users"""
        
        # Date filter
        date_filter = None
        if period == "this_week":
            date_filter = date.today() - timedelta(days=7)
        elif period == "this_month":
            date_filter = date.today() - timedelta(days=30)
        
        if metric == "score":
            query = self.db.query(
                User.id,
                User.email,
                User.full_name,
                User.avatar_url,
                User.current_level,
                func.avg(LessonAttempt.overall_score).label("value")
            ).join(
                LessonAttempt, User.id == LessonAttempt.user_id
            ).filter(
                User.role == "user",
                User.is_active == True,
                LessonAttempt.is_completed == True
            )
            
            if date_filter:
                query = query.filter(LessonAttempt.completed_at >= date_filter)
            
            query = query.group_by(
                User.id, User.email, User.full_name, User.avatar_url, User.current_level
            ).order_by(desc("value")).limit(limit)
            
        elif metric == "lessons_completed":
            query = self.db.query(
                User.id,
                User.email,
                User.full_name,
                User.avatar_url,
                User.current_level,
                func.count(LessonAttempt.id).label("value")
            ).join(
                LessonAttempt, User.id == LessonAttempt.user_id
            ).filter(
                User.role == "user",
                User.is_active == True,
                LessonAttempt.is_completed == True
            )
            
            if date_filter:
                query = query.filter(LessonAttempt.completed_at >= date_filter)
            
            query = query.group_by(
                User.id, User.email, User.full_name, User.avatar_url, User.current_level
            ).order_by(desc("value")).limit(limit)
            
        elif metric == "streak":
            query = self.db.query(
                User.id,
                User.email,
                User.full_name,
                User.avatar_url,
                User.current_level,
                UserStreak.current_streak.label("value")
            ).join(
                UserStreak, User.id == UserStreak.user_id
            ).filter(
                User.role == "user",
                User.is_active == True
            ).order_by(desc("value")).limit(limit)
            
        elif metric == "study_time":
            query = self.db.query(
                User.id,
                User.email,
                User.full_name,
                User.avatar_url,
                User.current_level,
                func.sum(LessonAttempt.duration_seconds).label("value")
            ).join(
                LessonAttempt, User.id == LessonAttempt.user_id
            ).filter(
                User.role == "user",
                User.is_active == True,
                LessonAttempt.is_completed == True
            )
            
            if date_filter:
                query = query.filter(LessonAttempt.completed_at >= date_filter)
            
            query = query.group_by(
                User.id, User.email, User.full_name, User.avatar_url, User.current_level
            ).order_by(desc("value")).limit(limit)
        else:
            return []
        
        results = query.all()
        
        items = []
        for rank, r in enumerate(results, 1):
            value = r.value
            if metric == "score" and value:
                value = round(float(value), 2)
            elif metric == "study_time" and value:
                value = int(value / 60)  # Convert to minutes
            
            items.append(LeaderboardItem(
                rank=rank,
                user_id=r.id,
                email=r.email,
                full_name=r.full_name,
                avatar_url=r.avatar_url,
                current_level=r.current_level or "beginner",
                value=float(value) if value else 0,
                metric=metric
            ))
        
        return items
