"""
Add Vocabulary for New Topics - Thêm từ vựng cho các topics mới

Chạy script:
    python -m app.seeding.add_vocabulary
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Topic, Vocabulary, Lesson, LessonVocabulary, LessonType


# ============================================================
# VOCABULARY DATA CHO CÁC TOPICS MỚI
# ============================================================
VOCAB_DATA = {
    # ===== DAILY LIFE =====
    "At the Supermarket": [
        {"word": "aisle", "definition": "lối đi giữa các kệ hàng", "phonetic": "/aɪl/", "example_sentence": "The milk is in aisle 3.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "cart", "definition": "xe đẩy hàng", "phonetic": "/kɑːrt/", "example_sentence": "I need a shopping cart.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "basket", "definition": "giỏ xách", "phonetic": "/ˈbæskɪt/", "example_sentence": "I'll just use a basket.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "checkout", "definition": "quầy thanh toán", "phonetic": "/ˈtʃekaʊt/", "example_sentence": "There's a long line at checkout.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "cashier", "definition": "nhân viên thu ngân", "phonetic": "/kæˈʃɪr/", "example_sentence": "The cashier was very friendly.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "groceries", "definition": "thực phẩm, hàng tạp hóa", "phonetic": "/ˈɡroʊsəriz/", "example_sentence": "I need to buy groceries.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "produce", "definition": "rau củ quả tươi", "phonetic": "/ˈproʊduːs/", "example_sentence": "The produce section has fresh vegetables.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "dairy", "definition": "sản phẩm từ sữa", "phonetic": "/ˈderi/", "example_sentence": "Milk and cheese are in the dairy section.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "frozen food", "definition": "thực phẩm đông lạnh", "phonetic": "/ˈfroʊzən fuːd/", "example_sentence": "I bought some frozen food.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "expiry date", "definition": "hạn sử dụng", "phonetic": "/ɪkˈspaɪri deɪt/", "example_sentence": "Check the expiry date before buying.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
    ],
    
    "At the Bank": [
        {"word": "account", "definition": "tài khoản", "phonetic": "/əˈkaʊnt/", "example_sentence": "I'd like to open an account.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "deposit", "definition": "gửi tiền", "phonetic": "/dɪˈpɑːzɪt/", "example_sentence": "I want to deposit $500.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "withdraw", "definition": "rút tiền", "phonetic": "/wɪðˈdrɔː/", "example_sentence": "I need to withdraw some cash.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "transfer", "definition": "chuyển khoản", "phonetic": "/trænsˈfɜːr/", "example_sentence": "Can I transfer money online?", "difficulty_level": "intermediate", "part_of_speech": "verb"},
        {"word": "balance", "definition": "số dư", "phonetic": "/ˈbæləns/", "example_sentence": "What's my account balance?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "loan", "definition": "khoản vay", "phonetic": "/loʊn/", "example_sentence": "I'd like to apply for a loan.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "interest rate", "definition": "lãi suất", "phonetic": "/ˈɪntrəst reɪt/", "example_sentence": "What's the interest rate?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "ATM", "definition": "máy rút tiền tự động", "phonetic": "/ˌeɪtiːˈem/", "example_sentence": "Is there an ATM nearby?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "PIN", "definition": "mã số cá nhân", "phonetic": "/pɪn/", "example_sentence": "Please enter your PIN.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "statement", "definition": "sao kê tài khoản", "phonetic": "/ˈsteɪtmənt/", "example_sentence": "I need a bank statement.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
    ],
    
    "At the Doctor": [
        {"word": "appointment", "definition": "cuộc hẹn khám", "phonetic": "/əˈpɔɪntmənt/", "example_sentence": "I have an appointment at 10 AM.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "symptom", "definition": "triệu chứng", "phonetic": "/ˈsɪmptəm/", "example_sentence": "What are your symptoms?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "fever", "definition": "sốt", "phonetic": "/ˈfiːvər/", "example_sentence": "I have a high fever.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "headache", "definition": "đau đầu", "phonetic": "/ˈhedeɪk/", "example_sentence": "I've had a headache all day.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "prescription", "definition": "đơn thuốc", "phonetic": "/prɪˈskrɪpʃn/", "example_sentence": "Here's your prescription.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "medicine", "definition": "thuốc", "phonetic": "/ˈmedɪsn/", "example_sentence": "Take this medicine twice a day.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "allergic", "definition": "dị ứng", "phonetic": "/əˈlɜːrdʒɪk/", "example_sentence": "I'm allergic to penicillin.", "difficulty_level": "intermediate", "part_of_speech": "adjective"},
        {"word": "injection", "definition": "tiêm", "phonetic": "/ɪnˈdʒekʃn/", "example_sentence": "Do I need an injection?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "checkup", "definition": "khám tổng quát", "phonetic": "/ˈtʃekʌp/", "example_sentence": "I'm here for a regular checkup.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "insurance", "definition": "bảo hiểm", "phonetic": "/ɪnˈʃʊrəns/", "example_sentence": "Do you accept health insurance?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
    ],
    
    "Making Phone Calls": [
        {"word": "dial", "definition": "quay số", "phonetic": "/daɪəl/", "example_sentence": "Dial 9 for an outside line.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "extension", "definition": "số máy lẻ", "phonetic": "/ɪkˈstenʃn/", "example_sentence": "What's your extension number?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "voicemail", "definition": "thư thoại", "phonetic": "/ˈvɔɪsmeɪl/", "example_sentence": "Please leave a voicemail.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "hold", "definition": "giữ máy", "phonetic": "/hoʊld/", "example_sentence": "Please hold for a moment.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "transfer", "definition": "chuyển cuộc gọi", "phonetic": "/trænsˈfɜːr/", "example_sentence": "I'll transfer you to sales.", "difficulty_level": "intermediate", "part_of_speech": "verb"},
        {"word": "hang up", "definition": "cúp máy", "phonetic": "/hæŋ ʌp/", "example_sentence": "Don't hang up yet!", "difficulty_level": "beginner", "part_of_speech": "phrasal verb"},
        {"word": "call back", "definition": "gọi lại", "phonetic": "/kɔːl bæk/", "example_sentence": "Can you call back later?", "difficulty_level": "beginner", "part_of_speech": "phrasal verb"},
        {"word": "busy", "definition": "máy bận", "phonetic": "/ˈbɪzi/", "example_sentence": "The line is busy.", "difficulty_level": "beginner", "part_of_speech": "adjective"},
        {"word": "reception", "definition": "sóng điện thoại", "phonetic": "/rɪˈsepʃn/", "example_sentence": "The reception is poor here.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "missed call", "definition": "cuộc gọi nhỡ", "phonetic": "/mɪst kɔːl/", "example_sentence": "I have 3 missed calls.", "difficulty_level": "beginner", "part_of_speech": "noun"},
    ],
    
    # ===== TRAVEL =====
    "At the Airport": [
        {"word": "boarding pass", "definition": "thẻ lên máy bay", "phonetic": "/ˈbɔːrdɪŋ pæs/", "example_sentence": "Here's my boarding pass.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "passport", "definition": "hộ chiếu", "phonetic": "/ˈpæspɔːrt/", "example_sentence": "May I see your passport?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "luggage", "definition": "hành lý", "phonetic": "/ˈlʌɡɪdʒ/", "example_sentence": "Where's the luggage claim?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "departure", "definition": "khởi hành", "phonetic": "/dɪˈpɑːrtʃər/", "example_sentence": "Check the departure time.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "arrival", "definition": "đến nơi", "phonetic": "/əˈraɪvl/", "example_sentence": "What's the arrival time?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "gate", "definition": "cổng ra máy bay", "phonetic": "/ɡeɪt/", "example_sentence": "Your flight departs from gate 15.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "security", "definition": "an ninh", "phonetic": "/sɪˈkjʊrəti/", "example_sentence": "Please go through security.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "customs", "definition": "hải quan", "phonetic": "/ˈkʌstəmz/", "example_sentence": "Do you have anything to declare at customs?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "delay", "definition": "trì hoãn", "phonetic": "/dɪˈleɪ/", "example_sentence": "The flight has been delayed.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "connecting flight", "definition": "chuyến bay nối chuyến", "phonetic": "/kəˈnektɪŋ flaɪt/", "example_sentence": "I have a connecting flight.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
    ],
    
    "Public Transportation": [
        {"word": "bus stop", "definition": "trạm xe buýt", "phonetic": "/bʌs stɑːp/", "example_sentence": "The bus stop is over there.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "train station", "definition": "ga tàu", "phonetic": "/treɪn ˈsteɪʃn/", "example_sentence": "How do I get to the train station?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "subway", "definition": "tàu điện ngầm", "phonetic": "/ˈsʌbweɪ/", "example_sentence": "Take the subway to downtown.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "fare", "definition": "tiền vé", "phonetic": "/fer/", "example_sentence": "What's the fare to the airport?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "ticket", "definition": "vé", "phonetic": "/ˈtɪkɪt/", "example_sentence": "I need to buy a ticket.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "schedule", "definition": "lịch trình", "phonetic": "/ˈskedʒuːl/", "example_sentence": "What's the bus schedule?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "platform", "definition": "sân ga", "phonetic": "/ˈplætfɔːrm/", "example_sentence": "The train leaves from platform 5.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "transfer", "definition": "đổi tuyến", "phonetic": "/trænsˈfɜːr/", "example_sentence": "You need to transfer at Central Station.", "difficulty_level": "intermediate", "part_of_speech": "verb"},
        {"word": "passenger", "definition": "hành khách", "phonetic": "/ˈpæsəndʒər/", "example_sentence": "All passengers must have tickets.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "rush hour", "definition": "giờ cao điểm", "phonetic": "/rʌʃ ˈaʊər/", "example_sentence": "Avoid traveling during rush hour.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
    ],
    
    "Sightseeing": [
        {"word": "tourist", "definition": "khách du lịch", "phonetic": "/ˈtʊrɪst/", "example_sentence": "This area is popular with tourists.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "attraction", "definition": "điểm tham quan", "phonetic": "/əˈtrækʃn/", "example_sentence": "What are the main attractions?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "museum", "definition": "bảo tàng", "phonetic": "/mjuːˈziːəm/", "example_sentence": "Let's visit the art museum.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "monument", "definition": "đài tưởng niệm", "phonetic": "/ˈmɑːnjumənt/", "example_sentence": "That's a famous monument.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "souvenir", "definition": "quà lưu niệm", "phonetic": "/ˌsuːvəˈnɪr/", "example_sentence": "I bought some souvenirs.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "guided tour", "definition": "tour có hướng dẫn", "phonetic": "/ˈɡaɪdɪd tʊr/", "example_sentence": "Is there a guided tour?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "entrance fee", "definition": "phí vào cổng", "phonetic": "/ˈentrəns fiː/", "example_sentence": "What's the entrance fee?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "camera", "definition": "máy ảnh", "phonetic": "/ˈkæmərə/", "example_sentence": "Photography is not allowed here.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "scenery", "definition": "phong cảnh", "phonetic": "/ˈsiːnəri/", "example_sentence": "The scenery is beautiful.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "viewpoint", "definition": "điểm ngắm cảnh", "phonetic": "/ˈvjuːpɔɪnt/", "example_sentence": "There's a great viewpoint up there.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
    ],
    
    # ===== BUSINESS =====
    "Office Communication": [
        {"word": "meeting", "definition": "cuộc họp", "phonetic": "/ˈmiːtɪŋ/", "example_sentence": "We have a meeting at 2 PM.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "colleague", "definition": "đồng nghiệp", "phonetic": "/ˈkɑːliːɡ/", "example_sentence": "I'll introduce you to my colleagues.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "deadline", "definition": "hạn chót", "phonetic": "/ˈdedlaɪn/", "example_sentence": "When is the deadline?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "report", "definition": "báo cáo", "phonetic": "/rɪˈpɔːrt/", "example_sentence": "I need to finish this report.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "schedule", "definition": "lịch làm việc", "phonetic": "/ˈskedʒuːl/", "example_sentence": "What's your schedule this week?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "assignment", "definition": "nhiệm vụ", "phonetic": "/əˈsaɪnmənt/", "example_sentence": "I have a new assignment.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "feedback", "definition": "phản hồi", "phonetic": "/ˈfiːdbæk/", "example_sentence": "Can I get your feedback?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "presentation", "definition": "bài thuyết trình", "phonetic": "/ˌpreznˈteɪʃn/", "example_sentence": "I'm preparing a presentation.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "approve", "definition": "phê duyệt", "phonetic": "/əˈpruːv/", "example_sentence": "Did the manager approve it?", "difficulty_level": "intermediate", "part_of_speech": "verb"},
        {"word": "project", "definition": "dự án", "phonetic": "/ˈprɑːdʒekt/", "example_sentence": "We're working on a new project.", "difficulty_level": "beginner", "part_of_speech": "noun"},
    ],
    
    "Business Meetings": [
        {"word": "agenda", "definition": "chương trình họp", "phonetic": "/əˈdʒendə/", "example_sentence": "Let's go through the agenda.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "minutes", "definition": "biên bản họp", "phonetic": "/ˈmɪnɪts/", "example_sentence": "Who's taking the minutes?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "proposal", "definition": "đề xuất", "phonetic": "/prəˈpoʊzl/", "example_sentence": "Let me present my proposal.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "negotiate", "definition": "đàm phán", "phonetic": "/nɪˈɡoʊʃieɪt/", "example_sentence": "We need to negotiate the terms.", "difficulty_level": "advanced", "part_of_speech": "verb"},
        {"word": "consensus", "definition": "sự đồng thuận", "phonetic": "/kənˈsensəs/", "example_sentence": "We need to reach a consensus.", "difficulty_level": "advanced", "part_of_speech": "noun"},
        {"word": "objective", "definition": "mục tiêu", "phonetic": "/əbˈdʒektɪv/", "example_sentence": "What's the main objective?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "postpone", "definition": "hoãn lại", "phonetic": "/poʊstˈpoʊn/", "example_sentence": "Let's postpone this to next week.", "difficulty_level": "intermediate", "part_of_speech": "verb"},
        {"word": "adjourn", "definition": "kết thúc cuộc họp", "phonetic": "/əˈdʒɜːrn/", "example_sentence": "Let's adjourn the meeting.", "difficulty_level": "advanced", "part_of_speech": "verb"},
        {"word": "chairperson", "definition": "người chủ trì", "phonetic": "/ˈtʃerpɜːrsn/", "example_sentence": "The chairperson opened the meeting.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "action item", "definition": "công việc cần làm", "phonetic": "/ˈækʃn ˈaɪtəm/", "example_sentence": "Let's list the action items.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
    ],
    
    "Email Writing": [
        {"word": "subject", "definition": "tiêu đề", "phonetic": "/ˈsʌbdʒekt/", "example_sentence": "Write a clear subject line.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "attachment", "definition": "tệp đính kèm", "phonetic": "/əˈtætʃmənt/", "example_sentence": "Please see the attachment.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "forward", "definition": "chuyển tiếp", "phonetic": "/ˈfɔːrwərd/", "example_sentence": "I'll forward the email to you.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "reply", "definition": "trả lời", "phonetic": "/rɪˈplaɪ/", "example_sentence": "Please reply by Friday.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "CC", "definition": "gửi bản sao", "phonetic": "/ˌsiːˈsiː/", "example_sentence": "I'll CC my manager.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "regards", "definition": "trân trọng (kết thư)", "phonetic": "/rɪˈɡɑːrdz/", "example_sentence": "Best regards, John.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "sincerely", "definition": "trân trọng (trang trọng)", "phonetic": "/sɪnˈsɪrli/", "example_sentence": "Yours sincerely, Sarah.", "difficulty_level": "intermediate", "part_of_speech": "adverb"},
        {"word": "urgent", "definition": "khẩn cấp", "phonetic": "/ˈɜːrdʒənt/", "example_sentence": "This is urgent.", "difficulty_level": "beginner", "part_of_speech": "adjective"},
        {"word": "confirm", "definition": "xác nhận", "phonetic": "/kənˈfɜːrm/", "example_sentence": "Please confirm your attendance.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "inquire", "definition": "hỏi thăm", "phonetic": "/ɪnˈkwaɪər/", "example_sentence": "I'm writing to inquire about...", "difficulty_level": "intermediate", "part_of_speech": "verb"},
    ],
    
    # ===== SOCIAL =====
    "Making Friends": [
        {"word": "introduce", "definition": "giới thiệu", "phonetic": "/ˌɪntrəˈduːs/", "example_sentence": "Let me introduce myself.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "hobby", "definition": "sở thích", "phonetic": "/ˈhɑːbi/", "example_sentence": "What are your hobbies?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "hangout", "definition": "đi chơi", "phonetic": "/ˈhæŋaʊt/", "example_sentence": "Want to hang out this weekend?", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "get along", "definition": "hợp nhau", "phonetic": "/ɡet əˈlɔːŋ/", "example_sentence": "We get along really well.", "difficulty_level": "intermediate", "part_of_speech": "phrasal verb"},
        {"word": "keep in touch", "definition": "giữ liên lạc", "phonetic": "/kiːp ɪn tʌtʃ/", "example_sentence": "Let's keep in touch!", "difficulty_level": "beginner", "part_of_speech": "phrase"},
        {"word": "common", "definition": "chung", "phonetic": "/ˈkɑːmən/", "example_sentence": "We have a lot in common.", "difficulty_level": "beginner", "part_of_speech": "adjective"},
        {"word": "invite", "definition": "mời", "phonetic": "/ɪnˈvaɪt/", "example_sentence": "I'd like to invite you to my party.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "catch up", "definition": "gặp lại nói chuyện", "phonetic": "/kætʃ ʌp/", "example_sentence": "Let's catch up over coffee.", "difficulty_level": "intermediate", "part_of_speech": "phrasal verb"},
        {"word": "acquaintance", "definition": "người quen", "phonetic": "/əˈkweɪntəns/", "example_sentence": "He's just an acquaintance.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "socialize", "definition": "giao lưu", "phonetic": "/ˈsoʊʃəlaɪz/", "example_sentence": "I like to socialize with colleagues.", "difficulty_level": "intermediate", "part_of_speech": "verb"},
    ],
    
    "Small Talk": [
        {"word": "weather", "definition": "thời tiết", "phonetic": "/ˈweðər/", "example_sentence": "Nice weather today, isn't it?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "weekend", "definition": "cuối tuần", "phonetic": "/ˌwiːkˈend/", "example_sentence": "Any plans for the weekend?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "vacation", "definition": "kỳ nghỉ", "phonetic": "/veɪˈkeɪʃn/", "example_sentence": "How was your vacation?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "commute", "definition": "đi lại làm việc", "phonetic": "/kəˈmjuːt/", "example_sentence": "How long is your commute?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "neighborhood", "definition": "khu vực sống", "phonetic": "/ˈneɪbərhʊd/", "example_sentence": "How do you like your neighborhood?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "favorite", "definition": "yêu thích", "phonetic": "/ˈfeɪvərɪt/", "example_sentence": "What's your favorite restaurant?", "difficulty_level": "beginner", "part_of_speech": "adjective"},
        {"word": "recent", "definition": "gần đây", "phonetic": "/ˈriːsnt/", "example_sentence": "Seen any good movies recently?", "difficulty_level": "beginner", "part_of_speech": "adjective"},
        {"word": "originally", "definition": "quê gốc", "phonetic": "/əˈrɪdʒənəli/", "example_sentence": "Where are you originally from?", "difficulty_level": "intermediate", "part_of_speech": "adverb"},
        {"word": "busy", "definition": "bận rộn", "phonetic": "/ˈbɪzi/", "example_sentence": "Have you been busy lately?", "difficulty_level": "beginner", "part_of_speech": "adjective"},
        {"word": "exciting", "definition": "thú vị", "phonetic": "/ɪkˈsaɪtɪŋ/", "example_sentence": "Anything exciting happening?", "difficulty_level": "beginner", "part_of_speech": "adjective"},
    ],
    
    "Celebrations & Holidays": [
        {"word": "celebrate", "definition": "kỷ niệm, ăn mừng", "phonetic": "/ˈseləbreɪt/", "example_sentence": "How do you celebrate Christmas?", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "tradition", "definition": "truyền thống", "phonetic": "/trəˈdɪʃn/", "example_sentence": "It's a family tradition.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "gift", "definition": "quà tặng", "phonetic": "/ɡɪft/", "example_sentence": "I got you a gift.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "decoration", "definition": "đồ trang trí", "phonetic": "/ˌdekəˈreɪʃn/", "example_sentence": "I love the decorations!", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "fireworks", "definition": "pháo hoa", "phonetic": "/ˈfaɪərwɜːrks/", "example_sentence": "Let's watch the fireworks!", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "feast", "definition": "bữa tiệc lớn", "phonetic": "/fiːst/", "example_sentence": "We had a wonderful feast.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "gathering", "definition": "buổi tụ họp", "phonetic": "/ˈɡæðərɪŋ/", "example_sentence": "It's a family gathering.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "toast", "definition": "nâng cốc chúc mừng", "phonetic": "/toʊst/", "example_sentence": "Let's make a toast!", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "countdown", "definition": "đếm ngược", "phonetic": "/ˈkaʊntdaʊn/", "example_sentence": "The New Year countdown is starting!", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "resolution", "definition": "quyết tâm đầu năm", "phonetic": "/ˌrezəˈluːʃn/", "example_sentence": "What's your New Year's resolution?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
    ],
    
    "Sports & Hobbies": [
        {"word": "exercise", "definition": "tập thể dục", "phonetic": "/ˈeksərsaɪz/", "example_sentence": "I exercise every morning.", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "gym", "definition": "phòng tập", "phonetic": "/dʒɪm/", "example_sentence": "I go to the gym three times a week.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "match", "definition": "trận đấu", "phonetic": "/mætʃ/", "example_sentence": "Did you watch the match?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "team", "definition": "đội", "phonetic": "/tiːm/", "example_sentence": "Which team do you support?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "score", "definition": "điểm số", "phonetic": "/skɔːr/", "example_sentence": "What's the score?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "championship", "definition": "giải vô địch", "phonetic": "/ˈtʃæmpiənʃɪp/", "example_sentence": "They won the championship.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "practice", "definition": "luyện tập", "phonetic": "/ˈpræktɪs/", "example_sentence": "Practice makes perfect.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "outdoor", "definition": "ngoài trời", "phonetic": "/ˈaʊtdɔːr/", "example_sentence": "I prefer outdoor activities.", "difficulty_level": "beginner", "part_of_speech": "adjective"},
        {"word": "coach", "definition": "huấn luyện viên", "phonetic": "/koʊtʃ/", "example_sentence": "My coach is very strict.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "compete", "definition": "thi đấu", "phonetic": "/kəmˈpiːt/", "example_sentence": "I want to compete in the tournament.", "difficulty_level": "intermediate", "part_of_speech": "verb"},
    ],
    
    "Movies & Entertainment": [
        {"word": "cinema", "definition": "rạp chiếu phim", "phonetic": "/ˈsɪnəmə/", "example_sentence": "Let's go to the cinema.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "genre", "definition": "thể loại", "phonetic": "/ˈʒɑːnrə/", "example_sentence": "What's your favorite genre?", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "plot", "definition": "cốt truyện", "phonetic": "/plɑːt/", "example_sentence": "The plot was confusing.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "character", "definition": "nhân vật", "phonetic": "/ˈkærəktər/", "example_sentence": "Who's your favorite character?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "trailer", "definition": "đoạn giới thiệu phim", "phonetic": "/ˈtreɪlər/", "example_sentence": "Have you seen the trailer?", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "sequel", "definition": "phần tiếp theo", "phonetic": "/ˈsiːkwəl/", "example_sentence": "I can't wait for the sequel.", "difficulty_level": "intermediate", "part_of_speech": "noun"},
        {"word": "streaming", "definition": "xem trực tuyến", "phonetic": "/ˈstriːmɪŋ/", "example_sentence": "I watch most shows on streaming.", "difficulty_level": "beginner", "part_of_speech": "noun"},
        {"word": "binge-watch", "definition": "xem liền nhiều tập", "phonetic": "/bɪndʒ wɑːtʃ/", "example_sentence": "I binge-watched the whole series.", "difficulty_level": "intermediate", "part_of_speech": "verb"},
        {"word": "recommend", "definition": "giới thiệu", "phonetic": "/ˌrekəˈmend/", "example_sentence": "Can you recommend a good movie?", "difficulty_level": "beginner", "part_of_speech": "verb"},
        {"word": "spoiler", "definition": "tiết lộ nội dung phim", "phonetic": "/ˈspɔɪlər/", "example_sentence": "No spoilers, please!", "difficulty_level": "intermediate", "part_of_speech": "noun"},
    ],
}


def add_vocabulary():
    """Thêm vocabulary và lesson cho các topics"""
    print("📝 Adding vocabulary for new topics...")
    
    db = SessionLocal()
    
    try:
        vocab_created = 0
        lesson_created = 0
        
        for topic_title, vocab_list in VOCAB_DATA.items():
            # Tìm topic
            topic = db.query(Topic).filter(Topic.title == topic_title).first()
            
            if not topic:
                print(f"  ⚠️ Topic not found: {topic_title}")
                continue
            
            # Check xem đã có lesson vocabulary chưa
            existing_lesson = db.query(Lesson).filter(
                Lesson.topic_id == topic.id,
                Lesson.lesson_type == LessonType.VOCABULARY_MATCHING
            ).first()
            
            if existing_lesson:
                print(f"  ℹ️ Already has vocabulary lesson: {topic_title}")
                continue
            
            # Tạo Vocabulary Lesson
            lesson = Lesson(
                topic_id=topic.id,
                title=f"{topic_title} - Vocabulary",
                description=f"Learn essential vocabulary for {topic_title}",
                lesson_type=LessonType.VOCABULARY_MATCHING,
                lesson_order=1,
                instructions="Match the words with their Vietnamese meanings",
                difficulty_level="beginner",
                estimated_minutes=15,
                passing_score=70.00,
                is_active=True
            )
            db.add(lesson)
            db.flush()
            lesson_created += 1
            
            # Tạo vocabulary và liên kết với lesson
            for i, word_data in enumerate(vocab_list):
                # Tìm vocab đã tồn tại hoặc tạo mới
                existing_vocab = db.query(Vocabulary).filter(Vocabulary.word == word_data["word"]).first()
                
                if existing_vocab:
                    vocab = existing_vocab
                else:
                    vocab = Vocabulary(**word_data)
                    db.add(vocab)
                    db.flush()
                    vocab_created += 1
                
                # Liên kết vocabulary với lesson
                lesson_vocab = LessonVocabulary(
                    lesson_id=lesson.id,
                    vocabulary_id=vocab.id,
                    display_order=i + 1
                )
                db.add(lesson_vocab)
                vocab_created += 1
            
            print(f"  ✅ Added {len(vocab_list)} words for: {topic_title}")
        
        db.commit()
        
        print(f"\n🎉 Done!")
        print(f"   📚 Lessons created: {lesson_created}")
        print(f"   📝 Vocabulary created: {vocab_created}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    add_vocabulary()
