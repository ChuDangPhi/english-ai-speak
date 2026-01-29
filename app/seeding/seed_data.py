"""
Seed Data Script - Tạo dữ liệu mẫu cho hệ thống

Chạy script này để tạo:
1. Topics (Chủ đề)
2. Lessons (Bài học) - 3 loại cho mỗi topic
3. Vocabulary (Từ vựng)
4. Pronunciation Exercises (Bài tập phát âm)
5. Conversation Templates (Mẫu hội thoại)

Usage:
    cd D:\Personal\WEB_ENGLISH\ai_tutor_BE
    python -m app.seeding.seed_data
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import (
    Topic, Lesson, Vocabulary, LessonVocabulary,
    PronunciationExercise, ConversationTemplate,
    LessonType, ExerciseType
)


def clear_existing_data(db: Session):
    """Xóa dữ liệu cũ (nếu có)"""
    print("🗑️  Clearing existing data...")
    
    # Delete in correct order (foreign key constraints)
    db.query(ConversationTemplate).delete()
    db.query(PronunciationExercise).delete()
    db.query(LessonVocabulary).delete()
    db.query(Vocabulary).delete()
    db.query(Lesson).delete()
    db.query(Topic).delete()
    
    db.commit()
    print("✅ Cleared existing data")


def seed_topics(db: Session) -> dict:
    """Tạo các chủ đề học"""
    print("\n📚 Creating Topics...")
    
    # Sử dụng Unsplash cho thumbnail (miễn phí, chất lượng cao)
    topics_data = [
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
    
    topics = {}
    for data in topics_data:
        topic = Topic(**data, is_active=True)
        db.add(topic)
        db.flush()
        topics[data["title"]] = topic
        print(f"  ✅ Created topic: {data['title']}")
    
    db.commit()
    return topics


def seed_vocabulary(db: Session, topics: dict) -> dict:
    """Tạo từ vựng cho các chủ đề"""
    print("\n📝 Creating Vocabulary...")
    
    vocab_data = {
        "At the Restaurant": [
            {"word": "menu", "definition": "thực đơn", "phonetic": "/ˈmenjuː/", "example_sentence": "Could I see the menu, please?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "waiter", "definition": "người phục vụ (nam)", "phonetic": "/ˈweɪtər/", "example_sentence": "The waiter will take your order.", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "waitress", "definition": "người phục vụ (nữ)", "phonetic": "/ˈweɪtrəs/", "example_sentence": "The waitress recommended the soup.", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "appetizer", "definition": "món khai vị", "phonetic": "/ˈæpɪtaɪzər/", "example_sentence": "Would you like an appetizer?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "main course", "definition": "món chính", "phonetic": "/meɪn kɔːrs/", "example_sentence": "For the main course, I'll have the steak.", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "dessert", "definition": "món tráng miệng", "phonetic": "/dɪˈzɜːrt/", "example_sentence": "What desserts do you have?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "bill", "definition": "hóa đơn", "phonetic": "/bɪl/", "example_sentence": "Could we have the bill, please?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "tip", "definition": "tiền boa", "phonetic": "/tɪp/", "example_sentence": "I left a 15% tip.", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "reservation", "definition": "đặt chỗ trước", "phonetic": "/ˌrezərˈveɪʃn/", "example_sentence": "I have a reservation for 7 o'clock.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "recommend", "definition": "giới thiệu, đề xuất", "phonetic": "/ˌrekəˈmend/", "example_sentence": "What do you recommend?", "difficulty_level": "intermediate", "part_of_speech": "verb"},
        ],
        "Shopping": [
            {"word": "discount", "definition": "giảm giá", "phonetic": "/ˈdɪskaʊnt/", "example_sentence": "Is there any discount?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "receipt", "definition": "hóa đơn, biên lai", "phonetic": "/rɪˈsiːt/", "example_sentence": "Can I have the receipt?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "fitting room", "definition": "phòng thử đồ", "phonetic": "/ˈfɪtɪŋ ruːm/", "example_sentence": "Where is the fitting room?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "size", "definition": "kích cỡ", "phonetic": "/saɪz/", "example_sentence": "Do you have this in a larger size?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "price", "definition": "giá", "phonetic": "/praɪs/", "example_sentence": "What's the price of this?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "cash", "definition": "tiền mặt", "phonetic": "/kæʃ/", "example_sentence": "Do you accept cash?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "credit card", "definition": "thẻ tín dụng", "phonetic": "/ˈkredɪt kɑːrd/", "example_sentence": "Can I pay by credit card?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "exchange", "definition": "đổi (hàng)", "phonetic": "/ɪksˈtʃeɪndʒ/", "example_sentence": "Can I exchange this for another color?", "difficulty_level": "intermediate", "part_of_speech": "verb"},
            {"word": "refund", "definition": "hoàn tiền", "phonetic": "/ˈriːfʌnd/", "example_sentence": "I'd like a refund, please.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "bargain", "definition": "món hời, mặc cả", "phonetic": "/ˈbɑːrɡɪn/", "example_sentence": "This is a real bargain!", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        ],
        "At the Hotel": [
            {"word": "check-in", "definition": "nhận phòng", "phonetic": "/tʃek ɪn/", "example_sentence": "What time is check-in?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "check-out", "definition": "trả phòng", "phonetic": "/tʃek aʊt/", "example_sentence": "I'd like to check out, please.", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "room service", "definition": "dịch vụ phòng", "phonetic": "/ruːm ˈsɜːrvɪs/", "example_sentence": "Does the hotel have room service?", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "vacancy", "definition": "phòng trống", "phonetic": "/ˈveɪkənsi/", "example_sentence": "Do you have any vacancies?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "single room", "definition": "phòng đơn", "phonetic": "/ˈsɪŋɡl ruːm/", "example_sentence": "I'd like a single room.", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "double room", "definition": "phòng đôi", "phonetic": "/ˈdʌbl ruːm/", "example_sentence": "We need a double room.", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "suite", "definition": "phòng suite (cao cấp)", "phonetic": "/swiːt/", "example_sentence": "How much is the suite per night?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "amenities", "definition": "tiện nghi", "phonetic": "/əˈmenɪtiz/", "example_sentence": "What amenities does the room have?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "housekeeping", "definition": "dọn phòng", "phonetic": "/ˈhaʊskiːpɪŋ/", "example_sentence": "Can I have housekeeping service?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "concierge", "definition": "nhân viên hỗ trợ khách", "phonetic": "/ˌkɒnsiˈeəʒ/", "example_sentence": "Ask the concierge for restaurant recommendations.", "difficulty_level": "advanced", "part_of_speech": "noun"},
        ],
        "Asking for Directions": [
            {"word": "turn left", "definition": "rẽ trái", "phonetic": "/tɜːrn left/", "example_sentence": "Turn left at the traffic light.", "difficulty_level": "beginner", "part_of_speech": "phrase"},
            {"word": "turn right", "definition": "rẽ phải", "phonetic": "/tɜːrn raɪt/", "example_sentence": "Turn right after the bank.", "difficulty_level": "beginner", "part_of_speech": "phrase"},
            {"word": "go straight", "definition": "đi thẳng", "phonetic": "/ɡoʊ streɪt/", "example_sentence": "Go straight for two blocks.", "difficulty_level": "beginner", "part_of_speech": "phrase"},
            {"word": "crossroad", "definition": "ngã tư", "phonetic": "/ˈkrɔːsroʊd/", "example_sentence": "Turn right at the crossroad.", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "intersection", "definition": "giao lộ", "phonetic": "/ˌɪntərˈsekʃn/", "example_sentence": "Stop at the intersection.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "block", "definition": "dãy nhà", "phonetic": "/blɑːk/", "example_sentence": "It's two blocks away.", "difficulty_level": "beginner", "part_of_speech": "noun"},
            {"word": "opposite", "definition": "đối diện", "phonetic": "/ˈɑːpəzɪt/", "example_sentence": "It's opposite the supermarket.", "difficulty_level": "beginner", "part_of_speech": "preposition"},
            {"word": "next to", "definition": "bên cạnh", "phonetic": "/nekst tuː/", "example_sentence": "The bank is next to the post office.", "difficulty_level": "beginner", "part_of_speech": "preposition"},
            {"word": "landmark", "definition": "địa điểm nổi bật", "phonetic": "/ˈlændmɑːrk/", "example_sentence": "Look for the landmark tower.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "pedestrian", "definition": "người đi bộ", "phonetic": "/pəˈdestriən/", "example_sentence": "Use the pedestrian crossing.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        ],
        "Job Interview": [
            {"word": "resume", "definition": "sơ yếu lý lịch", "phonetic": "/ˈrezəmeɪ/", "example_sentence": "I've attached my resume.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "qualification", "definition": "bằng cấp, trình độ", "phonetic": "/ˌkwɑːlɪfɪˈkeɪʃn/", "example_sentence": "What qualifications do you have?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "experience", "definition": "kinh nghiệm", "phonetic": "/ɪkˈspɪriəns/", "example_sentence": "I have 5 years of experience.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "salary", "definition": "lương", "phonetic": "/ˈsæləri/", "example_sentence": "What's the expected salary?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "benefits", "definition": "phúc lợi", "phonetic": "/ˈbenɪfɪts/", "example_sentence": "What benefits does the company offer?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "deadline", "definition": "hạn chót", "phonetic": "/ˈdedlaɪn/", "example_sentence": "I always meet my deadlines.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "teamwork", "definition": "làm việc nhóm", "phonetic": "/ˈtiːmwɜːrk/", "example_sentence": "I enjoy teamwork.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "strength", "definition": "điểm mạnh", "phonetic": "/streŋθ/", "example_sentence": "What are your strengths?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "weakness", "definition": "điểm yếu", "phonetic": "/ˈwiːknəs/", "example_sentence": "What are your weaknesses?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
            {"word": "opportunity", "definition": "cơ hội", "phonetic": "/ˌɑːpərˈtuːnəti/", "example_sentence": "This is a great opportunity.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        ]
    }
    
    vocabularies = {}
    for topic_name, words in vocab_data.items():
        topic = topics[topic_name]
        vocabularies[topic_name] = []
        
        for i, word_data in enumerate(words):
            vocab = Vocabulary(**word_data)
            db.add(vocab)
            db.flush()
            vocabularies[topic_name].append(vocab)
        
        print(f"  ✅ Created {len(words)} vocabulary for: {topic_name}")
    
    db.commit()
    return vocabularies


def seed_lessons(db: Session, topics: dict, vocabularies: dict) -> dict:
    """Tạo bài học cho mỗi chủ đề (3 bài: vocabulary, pronunciation, conversation)"""
    print("\n📖 Creating Lessons...")
    
    lessons = {}
    
    for topic_name, topic in topics.items():
        lessons[topic_name] = []
        
        # Lesson 1: Vocabulary Matching
        vocab_lesson = Lesson(
            topic_id=topic.id,
            lesson_type=LessonType.VOCABULARY_MATCHING,
            title=f"Vocabulary: {topic_name}",
            description=f"Learn and practice vocabulary related to {topic_name.lower()}",
            lesson_order=1,
            instructions="Match each English word with its Vietnamese meaning. You have 3 attempts for each word.",
            difficulty_level="beginner",
            estimated_minutes=15,
            passing_score=70
        )
        db.add(vocab_lesson)
        db.flush()
        lessons[topic_name].append(vocab_lesson)
        
        # Link vocabulary to lesson
        topic_vocab = vocabularies.get(topic_name, [])
        for vocab in topic_vocab:
            link = LessonVocabulary(
                lesson_id=vocab_lesson.id,
                vocabulary_id=vocab.id
            )
            db.add(link)
        
        # Lesson 2: Pronunciation
        pron_lesson = Lesson(
            topic_id=topic.id,
            lesson_type=LessonType.PRONUNCIATION,
            title=f"Pronunciation: {topic_name}",
            description=f"Practice pronouncing key words and phrases for {topic_name.lower()}",
            lesson_order=2,
            instructions="Listen to the audio and repeat. Record your voice to check pronunciation.",
            difficulty_level="intermediate",
            estimated_minutes=20,
            passing_score=70
        )
        db.add(pron_lesson)
        db.flush()
        lessons[topic_name].append(pron_lesson)
        
        # Lesson 3: Conversation
        conv_lesson = Lesson(
            topic_id=topic.id,
            lesson_type=LessonType.CONVERSATION,
            title=f"Conversation: {topic_name}",
            description=f"Practice real conversations about {topic_name.lower()} with AI",
            lesson_order=3,
            instructions="Have a conversation with the AI tutor. Try to use the vocabulary you learned.",
            difficulty_level="intermediate",
            estimated_minutes=15,
            passing_score=60
        )
        db.add(conv_lesson)
        db.flush()
        lessons[topic_name].append(conv_lesson)
        
        print(f"  ✅ Created 3 lessons for: {topic_name}")
    
    db.commit()
    return lessons


def seed_pronunciation_exercises(db: Session, lessons: dict, vocabularies: dict):
    """Tạo bài tập phát âm cho các lesson pronunciation"""
    print("\n🎤 Creating Pronunciation Exercises...")
    
    for topic_name, topic_lessons in lessons.items():
        # Find pronunciation lesson (lesson_order = 2)
        pron_lesson = next((l for l in topic_lessons if l.lesson_order == 2), None)
        if not pron_lesson:
            continue
        
        topic_vocab = vocabularies.get(topic_name, [])
        
        # Create exercises for first 5 vocabulary words
        for i, vocab in enumerate(topic_vocab[:5]):
            exercise = PronunciationExercise(
                lesson_id=pron_lesson.id,
                exercise_type=ExerciseType.WORD,
                content=vocab.word,
                phonetic=vocab.phonetic,
                display_order=i + 1,
                target_pronunciation_score=70
            )
            db.add(exercise)
        
        # Add some phrase exercises
        phrases = get_phrases_for_topic(topic_name)
        for i, phrase_data in enumerate(phrases):
            exercise = PronunciationExercise(
                lesson_id=pron_lesson.id,
                exercise_type=ExerciseType.PHRASE,
                content=phrase_data["phrase"],
                phonetic=phrase_data.get("ipa", ""),
                display_order=6 + i,
                target_pronunciation_score=65
            )
            db.add(exercise)
        
        print(f"  ✅ Created pronunciation exercises for: {topic_name}")
    
    db.commit()


def get_phrases_for_topic(topic_name: str) -> list:
    """Get phrases for each topic"""
    phrases = {
        "At the Restaurant": [
            {"phrase": "I'd like to order", "meaning": "Tôi muốn gọi món", "ipa": "/aɪd laɪk tuː ˈɔːrdər/"},
            {"phrase": "Could I have the bill please", "meaning": "Cho tôi hóa đơn được không", "ipa": "/kʊd aɪ hæv ðə bɪl pliːz/"},
            {"phrase": "What do you recommend", "meaning": "Bạn giới thiệu món gì", "ipa": "/wɒt duː juː ˌrekəˈmend/"},
        ],
        "Shopping": [
            {"phrase": "How much is this", "meaning": "Cái này bao nhiêu tiền", "ipa": "/haʊ mʌtʃ ɪz ðɪs/"},
            {"phrase": "Can I try this on", "meaning": "Tôi có thể thử cái này không", "ipa": "/kæn aɪ traɪ ðɪs ɒn/"},
            {"phrase": "Do you have a smaller size", "meaning": "Bạn có size nhỏ hơn không", "ipa": "/duː juː hæv ə ˈsmɔːlər saɪz/"},
        ],
        "At the Hotel": [
            {"phrase": "I have a reservation", "meaning": "Tôi đã đặt phòng", "ipa": "/aɪ hæv ə ˌrezərˈveɪʃn/"},
            {"phrase": "What time is checkout", "meaning": "Mấy giờ trả phòng", "ipa": "/wɒt taɪm ɪz ˈtʃekaʊt/"},
            {"phrase": "Could you call a taxi", "meaning": "Bạn có thể gọi taxi không", "ipa": "/kʊd juː kɔːl ə ˈtæksi/"},
        ],
        "Asking for Directions": [
            {"phrase": "Excuse me, how do I get to", "meaning": "Xin lỗi, làm sao để đến", "ipa": "/ɪkˈskjuːz miː haʊ duː aɪ ɡet tuː/"},
            {"phrase": "Is it far from here", "meaning": "Có xa đây không", "ipa": "/ɪz ɪt fɑːr frɒm hɪər/"},
            {"phrase": "Can you show me on the map", "meaning": "Bạn có thể chỉ trên bản đồ không", "ipa": "/kæn juː ʃoʊ miː ɒn ðə mæp/"},
        ],
        "Job Interview": [
            {"phrase": "Thank you for this opportunity", "meaning": "Cảm ơn vì cơ hội này", "ipa": "/θæŋk juː fɔːr ðɪs ˌɒpərˈtuːnɪti/"},
            {"phrase": "I am looking forward to hearing from you", "meaning": "Tôi mong nhận được phản hồi", "ipa": "/aɪ æm ˈlʊkɪŋ ˈfɔːrwərd tuː ˈhɪərɪŋ frɒm juː/"},
            {"phrase": "What are the next steps", "meaning": "Bước tiếp theo là gì", "ipa": "/wɒt ɑːr ðə nekst steps/"},
        ],
    }
    return phrases.get(topic_name, [])


def seed_conversation_templates(db: Session, lessons: dict):
    """Tạo template hội thoại cho các lesson conversation"""
    print("\n💬 Creating Conversation Templates...")
    
    templates_data = {
        "At the Restaurant": {
            "ai_role": "Waiter at an Italian restaurant",
            "scenario_context": "You are a customer at an Italian restaurant. You want to order food and drinks. The waiter will help you with the menu and take your order.",
            "starter_prompts": ["I'd like to see the menu", "What do you recommend?", "I'm ready to order"],
            "suggested_topics": ["ordering food", "asking about ingredients", "requesting the bill"],
            "min_turns": 5
        },
        "Shopping": {
            "ai_role": "Shop assistant at a clothing store",
            "scenario_context": "You are shopping for clothes. The shop assistant will help you find the right size, color, and style. You can ask about prices and try items on.",
            "starter_prompts": ["I'm looking for a shirt", "Do you have this in blue?", "Can I try this on?"],
            "suggested_topics": ["finding the right size", "asking about prices", "payment methods"],
            "min_turns": 5
        },
        "At the Hotel": {
            "ai_role": "Hotel receptionist",
            "scenario_context": "You are checking into a hotel. The receptionist will help you with your reservation, room selection, and any special requests you may have.",
            "starter_prompts": ["I have a reservation", "What rooms are available?", "Is breakfast included?"],
            "suggested_topics": ["room amenities", "hotel services", "local recommendations"],
            "min_turns": 5
        },
        "Asking for Directions": {
            "ai_role": "Friendly local resident",
            "scenario_context": "You are a tourist and you're lost. A friendly local will help you find your way to famous landmarks, restaurants, or your hotel.",
            "starter_prompts": ["Excuse me, can you help me?", "How do I get to the museum?", "Is there a bus stop nearby?"],
            "suggested_topics": ["finding locations", "transportation options", "walking directions"],
            "min_turns": 4
        },
        "Job Interview": {
            "ai_role": "HR Manager conducting a job interview",
            "scenario_context": "You are being interviewed for a software developer position. The interviewer will ask about your experience, skills, and why you want to work for the company.",
            "starter_prompts": ["Thank you for having me", "I'm excited about this opportunity", "I've prepared some questions"],
            "suggested_topics": ["experience and skills", "career goals", "company culture"],
            "min_turns": 6
        },
    }
    
    for topic_name, topic_lessons in lessons.items():
        # Find conversation lesson (lesson_order = 3)
        conv_lesson = next((l for l in topic_lessons if l.lesson_order == 3), None)
        if not conv_lesson:
            continue
        
        template_data = templates_data.get(topic_name)
        if not template_data:
            continue
        
        # Convert lists to JSON strings
        starter_prompts = json.dumps(template_data["starter_prompts"])
        suggested_topics = json.dumps(template_data["suggested_topics"])
        
        template = ConversationTemplate(
            lesson_id=conv_lesson.id,
            ai_role=template_data["ai_role"],
            scenario_context=template_data["scenario_context"],
            starter_prompts=starter_prompts,
            suggested_topics=suggested_topics,
            min_turns=template_data["min_turns"]
        )
        db.add(template)
        
        print(f"  ✅ Created conversation template for: {topic_name}")
    
    db.commit()


def run_seed():
    """Main function để chạy seeding"""
    print("=" * 60)
    print("🌱 SEEDING DATABASE WITH SAMPLE DATA")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_existing_data(db)
        
        # Seed data
        topics = seed_topics(db)
        vocabularies = seed_vocabulary(db, topics)
        lessons = seed_lessons(db, topics, vocabularies)
        seed_pronunciation_exercises(db, lessons, vocabularies)
        seed_conversation_templates(db, lessons)
        
        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Summary
        print("\n📊 Summary:")
        print(f"  - Topics: {len(topics)}")
        print(f"  - Lessons: {sum(len(l) for l in lessons.values())}")
        print(f"  - Vocabulary: {sum(len(v) for v in vocabularies.values())}")
        print(f"  - Pronunciation Exercises: Created")
        print(f"  - Conversation Templates: Created")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
