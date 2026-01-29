"""
Update Topics Script - Cập nhật và thêm topics mới (không xóa data cũ)

Chạy script này để:
1. Cập nhật thumbnail_url cho topics hiện có
2. Thêm các topics mới

Usage:
    cd D:\Personal\WEB_ENGLISH\ai_tutor_BE
    python -m app.seeding.update_topics
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Topic


# Danh sách topics với thumbnail URLs
TOPICS_DATA = [
    # ===== DAILY LIFE (Hằng ngày) =====
    {
        "title": "At the Restaurant",
        "description": "Learn vocabulary and conversations for dining out at restaurants",
        "category": "daily_life",
        "difficulty_level": "beginner",
        "display_order": 1,
        "estimated_duration_minutes": 45,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop"
    },
    {
        "title": "Shopping",
        "description": "Essential phrases for shopping at stores and markets",
        "category": "daily_life",
        "difficulty_level": "beginner",
        "display_order": 2,
        "estimated_duration_minutes": 40,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=400&h=300&fit=crop"
    },
    {
        "title": "At the Supermarket",
        "description": "Learn to shop for groceries and daily necessities",
        "category": "daily_life",
        "difficulty_level": "beginner",
        "display_order": 3,
        "estimated_duration_minutes": 35,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=400&h=300&fit=crop"
    },
    {
        "title": "At the Bank",
        "description": "Banking vocabulary and common transactions",
        "category": "daily_life",
        "difficulty_level": "intermediate",
        "display_order": 4,
        "estimated_duration_minutes": 40,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=400&h=300&fit=crop"
    },
    {
        "title": "At the Doctor",
        "description": "Medical vocabulary and describing symptoms",
        "category": "daily_life",
        "difficulty_level": "intermediate",
        "display_order": 5,
        "estimated_duration_minutes": 50,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=400&h=300&fit=crop"
    },
    {
        "title": "Making Phone Calls",
        "description": "Phone etiquette and common expressions",
        "category": "daily_life",
        "difficulty_level": "intermediate",
        "display_order": 6,
        "estimated_duration_minutes": 35,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1523966211575-eb4a01e7dd51?w=400&h=300&fit=crop"
    },
    
    # ===== TRAVEL (Du lịch) =====
    {
        "title": "At the Hotel",
        "description": "Communication skills for hotel check-in, services, and requests",
        "category": "travel",
        "difficulty_level": "intermediate",
        "display_order": 7,
        "estimated_duration_minutes": 50,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&h=300&fit=crop"
    },
    {
        "title": "Asking for Directions",
        "description": "Learn to ask and give directions in English",
        "category": "travel",
        "difficulty_level": "beginner",
        "display_order": 8,
        "estimated_duration_minutes": 35,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1519500099198-fd81846b8f03?w=400&h=300&fit=crop"
    },
    {
        "title": "At the Airport",
        "description": "Navigate airports with confidence - check-in, security, boarding",
        "category": "travel",
        "difficulty_level": "intermediate",
        "display_order": 9,
        "estimated_duration_minutes": 55,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=400&h=300&fit=crop"
    },
    {
        "title": "Public Transportation",
        "description": "Using buses, trains, and taxis in English-speaking countries",
        "category": "travel",
        "difficulty_level": "beginner",
        "display_order": 10,
        "estimated_duration_minutes": 40,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=400&h=300&fit=crop"
    },
    {
        "title": "Sightseeing",
        "description": "Vocabulary for tourist attractions and activities",
        "category": "travel",
        "difficulty_level": "beginner",
        "display_order": 11,
        "estimated_duration_minutes": 45,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=300&fit=crop"
    },
    
    # ===== BUSINESS (Công việc) =====
    {
        "title": "Job Interview",
        "description": "Prepare for job interviews with common questions and answers",
        "category": "business",
        "difficulty_level": "advanced",
        "display_order": 12,
        "estimated_duration_minutes": 60,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1565688534245-05d6b5be184a?w=400&h=300&fit=crop"
    },
    {
        "title": "Office Communication",
        "description": "Professional communication in the workplace",
        "category": "business",
        "difficulty_level": "intermediate",
        "display_order": 13,
        "estimated_duration_minutes": 50,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=400&h=300&fit=crop"
    },
    {
        "title": "Business Meetings",
        "description": "Lead and participate in professional meetings",
        "category": "business",
        "difficulty_level": "advanced",
        "display_order": 14,
        "estimated_duration_minutes": 55,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=400&h=300&fit=crop"
    },
    {
        "title": "Email Writing",
        "description": "Write professional emails in English",
        "category": "business",
        "difficulty_level": "intermediate",
        "display_order": 15,
        "estimated_duration_minutes": 45,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1596526131083-e8c633c948d2?w=400&h=300&fit=crop"
    },
    
    # ===== SOCIAL (Văn hóa/Xã hội) =====
    {
        "title": "Making Friends",
        "description": "Start conversations and make new friends",
        "category": "social",
        "difficulty_level": "beginner",
        "display_order": 16,
        "estimated_duration_minutes": 40,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=400&h=300&fit=crop"
    },
    {
        "title": "Small Talk",
        "description": "Master the art of casual conversation",
        "category": "social",
        "difficulty_level": "intermediate",
        "display_order": 17,
        "estimated_duration_minutes": 35,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1543807535-eceef0bc6599?w=400&h=300&fit=crop"
    },
    {
        "title": "Celebrations & Holidays",
        "description": "Talk about holidays, parties, and celebrations",
        "category": "social",
        "difficulty_level": "intermediate",
        "display_order": 18,
        "estimated_duration_minutes": 45,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1513151233558-d860c5398176?w=400&h=300&fit=crop"
    },
    {
        "title": "Sports & Hobbies",
        "description": "Discuss sports, hobbies, and leisure activities",
        "category": "social",
        "difficulty_level": "beginner",
        "display_order": 19,
        "estimated_duration_minutes": 40,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=400&h=300&fit=crop"
    },
    {
        "title": "Movies & Entertainment",
        "description": "Talk about movies, TV shows, and entertainment",
        "category": "social",
        "difficulty_level": "beginner",
        "display_order": 20,
        "estimated_duration_minutes": 35,
        "total_lessons": 3,
        "thumbnail_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=400&h=300&fit=crop"
    }
]


def update_topics():
    """Cập nhật và thêm topics"""
    print("🔄 Updating Topics...")
    
    db = SessionLocal()
    
    try:
        updated_count = 0
        created_count = 0
        
        for data in TOPICS_DATA:
            # Tìm topic theo title
            existing = db.query(Topic).filter(Topic.title == data["title"]).first()
            
            if existing:
                # Cập nhật topic hiện có
                existing.description = data["description"]
                existing.category = data["category"]
                existing.difficulty_level = data["difficulty_level"]
                existing.display_order = data["display_order"]
                existing.estimated_duration_minutes = data["estimated_duration_minutes"]
                existing.total_lessons = data["total_lessons"]
                existing.thumbnail_url = data["thumbnail_url"]
                updated_count += 1
                print(f"  📝 Updated: {data['title']}")
            else:
                # Tạo topic mới
                topic = Topic(**data, is_active=True)
                db.add(topic)
                created_count += 1
                print(f"  ✅ Created: {data['title']}")
        
        db.commit()
        
        print(f"\n🎉 Done! Updated: {updated_count}, Created: {created_count}")
        print(f"📊 Total topics in database: {db.query(Topic).count()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    update_topics()
