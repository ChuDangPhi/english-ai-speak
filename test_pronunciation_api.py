"""
Comprehensive test suite for Pronunciation API endpoints

Tests:
1. POST /api/v1/pronunciation/submit - Submit pronunciation for scoring
2. GET /api/v1/pronunciation/summary/{lesson_attempt_id} - Get pronunciation summary

NOTE: Some tests are skipped when using SQLite as they require MySQL for auto-increment
ID generation. To run all tests, configure a MySQL test database and update the
SQLALCHEMY_TEST_DATABASE_URL variable below.

Running tests:
    # Run all tests (some will be skipped with SQLite)
    pytest test_pronunciation_api.py -v
    
    # Run only passing tests
    pytest test_pronunciation_api.py -v -k "not skip"
    
    # Run with coverage
    pytest test_pronunciation_api.py --cov=app.routers.pronunciation
"""
import pytest
import base64
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.topic import Topic
from app.models.lesson import Lesson, PronunciationExercise, ExerciseType, LessonType
from app.models.attempt import LessonAttempt, PronunciationAttempt
from app.core.security import hash_password, create_access_token

# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_pronunciation.db"
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Helper function for generating test IDs compatible with BigInteger
def generate_test_id() -> int:
    """Generate a unique ID for SQLite compatibility with BigInteger columns"""
    return abs(hash(str(uuid.uuid4()))) % (10 ** 15)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        id=generate_test_id(),
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        full_name="Test User",
        current_level="beginner",
        is_active=True,
        role="student"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers with JWT token"""
    access_token = create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_topic(db_session):
    """Create a test topic"""
    topic = Topic(
        id=generate_test_id(),
        title="Pronunciation Practice",
        description="Test pronunciation topic",
        difficulty_level="beginner",
        display_order=1,
        is_active=True
    )
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)
    return topic


@pytest.fixture
def test_lesson(db_session, test_topic):
    """Create a test lesson"""
    lesson = Lesson(
        id=generate_test_id(),
        topic_id=test_topic.id,
        lesson_type=LessonType.PRONUNCIATION,
        title="Basic Pronunciation",
        description="Test basic pronunciation",
        lesson_order=1,
        difficulty_level="beginner",
        passing_score=70.0,
        is_active=True
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)
    return lesson


@pytest.fixture
def test_exercise(db_session, test_lesson):
    """Create a test pronunciation exercise"""
    exercise = PronunciationExercise(
        id=generate_test_id(),
        lesson_id=test_lesson.id,
        exercise_type=ExerciseType.WORD,
        content="restaurant",
        phonetic="/ˈrestərɒnt/",
        audio_url="/audio/restaurant.mp3",
        target_pronunciation_score=70.0,
        display_order=1
    )
    db_session.add(exercise)
    db_session.commit()
    db_session.refresh(exercise)
    return exercise


@pytest.fixture
def test_lesson_attempt(db_session, test_user, test_lesson):
    """Create a test lesson attempt"""
    attempt = LessonAttempt(
        id=generate_test_id(),
        user_id=test_user.id,
        lesson_id=test_lesson.id,
        attempt_number=1,
        is_completed=False
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)
    return attempt


# Minimal valid WebM audio header for testing (base64 encoded)
# This represents the start of a WebM container with minimal data
SAMPLE_WEBM_AUDIO = b"GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibWKHEQAJ"


@pytest.fixture
def sample_audio_base64():
    """Generate a sample base64 encoded audio for testing"""
    return f"data:audio/webm;base64,{base64.b64encode(SAMPLE_WEBM_AUDIO).decode()}"


# ============================================================
# Tests for POST /api/v1/pronunciation/submit
# ============================================================

class TestPronunciationSubmit:
    """Test cases for pronunciation submission endpoint"""
    
    @pytest.mark.skip(reason="Requires MySQL database for auto-increment ID generation")
    def test_submit_pronunciation_success(
        self, 
        client, 
        auth_headers, 
        test_lesson_attempt, 
        test_exercise,
        sample_audio_base64
    ):
        """Test successful pronunciation submission"""
        response = client.post(
            "/api/v1/pronunciation/submit",
            json={
                "lesson_attempt_id": test_lesson_attempt.id,
                "exercise_id": test_exercise.id,
                "audio_base64": sample_audio_base64,
                "audio_format": "webm"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "exercise_id" in data
        assert data["exercise_id"] == test_exercise.id
        assert "attempt_number" in data
        assert data["attempt_number"] == 1
        assert "expected_content" in data
        assert data["expected_content"] == "restaurant"
        assert "transcription" in data
        assert "scores" in data
        assert "feedback" in data
        assert "is_passed" in data
        assert "target_score" in data
        assert "created_at" in data
        
        # Verify scores structure
        scores = data["scores"]
        assert "pronunciation_score" in scores
        assert "intonation_score" in scores
        assert "stress_score" in scores
        assert "accuracy_score" in scores
        assert 0 <= scores["pronunciation_score"] <= 100
        assert 0 <= scores["intonation_score"] <= 100
        assert 0 <= scores["stress_score"] <= 100
        assert 0 <= scores["accuracy_score"] <= 100
        
        # Verify feedback structure
        feedback = data["feedback"]
        assert "overall" in feedback
        assert "pronunciation_feedback" in feedback
        assert "intonation_feedback" in feedback
        assert "stress_feedback" in feedback
        assert "suggestions" in feedback
        assert isinstance(feedback["suggestions"], list)
    
    def test_submit_pronunciation_invalid_lesson_attempt(
        self,
        client,
        auth_headers,
        test_exercise,
        sample_audio_base64
    ):
        """Test submission with invalid lesson_attempt_id"""
        response = client.post(
            "/api/v1/pronunciation/submit",
            json={
                "lesson_attempt_id": 99999,  # Non-existent
                "exercise_id": test_exercise.id,
                "audio_base64": sample_audio_base64,
                "audio_format": "webm"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Không tìm thấy phiên làm bài" in response.json()["detail"]
    
    def test_submit_pronunciation_invalid_exercise(
        self,
        client,
        auth_headers,
        test_lesson_attempt,
        sample_audio_base64
    ):
        """Test submission with invalid exercise_id"""
        response = client.post(
            "/api/v1/pronunciation/submit",
            json={
                "lesson_attempt_id": test_lesson_attempt.id,
                "exercise_id": 99999,  # Non-existent
                "audio_base64": sample_audio_base64,
                "audio_format": "webm"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Không tìm thấy bài tập phát âm" in response.json()["detail"]
    
    @pytest.mark.skip(reason="Requires MySQL database for auto-increment ID generation")
    def test_submit_pronunciation_missing_audio(
        self,
        client,
        auth_headers,
        test_lesson_attempt,
        test_exercise
    ):
        """Test submission with missing audio data"""
        response = client.post(
            "/api/v1/pronunciation/submit",
            json={
                "lesson_attempt_id": test_lesson_attempt.id,
                "exercise_id": test_exercise.id,
                "audio_base64": "",  # Empty audio
                "audio_format": "webm"
            },
            headers=auth_headers
        )
        
        # Should still work but might have lower scores
        # The API should handle empty audio gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_submit_pronunciation_unauthorized(
        self,
        client,
        test_lesson_attempt,
        test_exercise,
        sample_audio_base64
    ):
        """Test submission without authentication"""
        response = client.post(
            "/api/v1/pronunciation/submit",
            json={
                "lesson_attempt_id": test_lesson_attempt.id,
                "exercise_id": test_exercise.id,
                "audio_base64": sample_audio_base64,
                "audio_format": "webm"
            }
        )
        
        assert response.status_code == 403  # HTTPBearer returns 403
    
    @pytest.mark.skip(reason="Requires MySQL database for auto-increment ID generation")
    def test_submit_pronunciation_multiple_attempts(
        self,
        client,
        auth_headers,
        test_lesson_attempt,
        test_exercise,
        sample_audio_base64
    ):
        """Test multiple submissions for the same exercise"""
        # First attempt
        response1 = client.post(
            "/api/v1/pronunciation/submit",
            json={
                "lesson_attempt_id": test_lesson_attempt.id,
                "exercise_id": test_exercise.id,
                "audio_base64": sample_audio_base64,
                "audio_format": "webm"
            },
            headers=auth_headers
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["attempt_number"] == 1
        
        # Second attempt
        response2 = client.post(
            "/api/v1/pronunciation/submit",
            json={
                "lesson_attempt_id": test_lesson_attempt.id,
                "exercise_id": test_exercise.id,
                "audio_base64": sample_audio_base64,
                "audio_format": "webm"
            },
            headers=auth_headers
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["attempt_number"] == 2
    
    @pytest.mark.skip(reason="Requires MySQL database for auto-increment ID generation")
    def test_submit_pronunciation_different_audio_formats(
        self,
        client,
        auth_headers,
        test_lesson_attempt,
        test_exercise,
        sample_audio_base64
    ):
        """Test submission with different audio formats"""
        formats = ["webm", "wav", "mp3"]
        
        for audio_format in formats:
            response = client.post(
                "/api/v1/pronunciation/submit",
                json={
                    "lesson_attempt_id": test_lesson_attempt.id,
                    "exercise_id": test_exercise.id,
                    "audio_base64": sample_audio_base64,
                    "audio_format": audio_format
                },
                headers=auth_headers
            )
            
            # Should accept all common audio formats
            assert response.status_code in [200, 400, 422]


# ============================================================
# Tests for GET /api/v1/pronunciation/summary/{lesson_attempt_id}
# ============================================================

class TestPronunciationSummary:
    """Test cases for pronunciation summary endpoint"""
    
    def test_get_summary_success(
        self,
        client,
        auth_headers,
        test_lesson_attempt,
        test_exercise,
        db_session
    ):
        """Test successful summary retrieval"""
        # Create some pronunciation attempts first
        attempt1 = PronunciationAttempt(
            id=generate_test_id(),
            lesson_attempt_id=test_lesson_attempt.id,
            exercise_id=test_exercise.id,
            audio_url="/test/audio1.webm",
            transcription="restaurant",
            pronunciation_score=85.0,
            intonation_score=80.0,
            stress_score=90.0,
            accuracy_score=85.0,
            suggestions="Good pronunciation!",
            attempt_number=1
        )
        db_session.add(attempt1)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/pronunciation/summary/{test_lesson_attempt.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "lesson_id" in data
        assert data["lesson_id"] == test_lesson_attempt.lesson_id
        assert "lesson_title" in data
        assert "total_exercises" in data
        assert "completed_exercises" in data
        assert "average_pronunciation" in data
        assert "average_intonation" in data
        assert "average_stress" in data
        assert "overall_score" in data
        assert "exercise_results" in data
        assert "is_passed" in data
        assert "passing_score" in data
        assert "ai_summary_feedback" in data
        
        # Verify exercise results
        assert isinstance(data["exercise_results"], list)
        assert len(data["exercise_results"]) > 0
        
        # Verify scores are calculated correctly
        assert data["average_pronunciation"] == 85.0
        assert data["average_intonation"] == 80.0
        assert data["average_stress"] == 90.0
        assert data["overall_score"] == pytest.approx(85.0, rel=0.1)
    
    def test_get_summary_invalid_lesson_attempt(
        self,
        client,
        auth_headers
    ):
        """Test summary retrieval with invalid lesson_attempt_id"""
        response = client.get(
            "/api/v1/pronunciation/summary/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Không tìm thấy phiên làm bài" in response.json()["detail"]
    
    def test_get_summary_unauthorized(
        self,
        client,
        test_lesson_attempt
    ):
        """Test summary retrieval without authentication"""
        response = client.get(
            f"/api/v1/pronunciation/summary/{test_lesson_attempt.id}"
        )
        
        assert response.status_code == 403
    
    def test_get_summary_no_attempts(
        self,
        client,
        auth_headers,
        test_lesson_attempt
    ):
        """Test summary when no pronunciation attempts exist"""
        response = client.get(
            f"/api/v1/pronunciation/summary/{test_lesson_attempt.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return zero scores when no attempts
        assert data["completed_exercises"] == 0
        assert data["average_pronunciation"] == 0.0
        assert data["average_intonation"] == 0.0
        assert data["average_stress"] == 0.0
        assert data["overall_score"] == 0.0
        assert len(data["exercise_results"]) == 0
    
    def test_get_summary_multiple_exercises(
        self,
        client,
        auth_headers,
        test_lesson_attempt,
        test_lesson,
        test_exercise,  # Add test_exercise fixture
        db_session
    ):
        """Test summary with multiple exercises"""
        # Create additional exercises
        exercise2 = PronunciationExercise(
            id=generate_test_id(),
            lesson_id=test_lesson.id,
            exercise_type=ExerciseType.WORD,
            content="beautiful",
            phonetic="/ˈbjuːtɪf(ə)l/",
            target_pronunciation_score=70.0,
            display_order=2
        )
        db_session.add(exercise2)
        db_session.commit()
        db_session.refresh(exercise2)
        
        # Create attempts for both exercises
        attempt1 = PronunciationAttempt(
            id=generate_test_id(),
            lesson_attempt_id=test_lesson_attempt.id,
            exercise_id=test_exercise.id,  # Use test_exercise fixture
            audio_url="/test/audio1.webm",
            transcription="restaurant",
            pronunciation_score=85.0,
            intonation_score=80.0,
            stress_score=90.0,
            accuracy_score=85.0,
            attempt_number=1
        )
        
        attempt2 = PronunciationAttempt(
            id=generate_test_id(),
            lesson_attempt_id=test_lesson_attempt.id,
            exercise_id=exercise2.id,
            audio_url="/test/audio2.webm",
            transcription="beautiful",
            pronunciation_score=75.0,
            intonation_score=70.0,
            stress_score=80.0,
            accuracy_score=75.0,
            attempt_number=1
        )
        
        db_session.add_all([attempt1, attempt2])
        db_session.commit()
        
        response = client.get(
            f"/api/v1/pronunciation/summary/{test_lesson_attempt.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have 2 exercises completed
        assert data["completed_exercises"] == 2
        
        # Verify average scores (average of 85.0 and 75.0 = 80.0)
        assert data["average_pronunciation"] == 80.0
        assert data["average_intonation"] == 75.0
        assert data["average_stress"] == 85.0
        
        # Should have 2 results
        assert len(data["exercise_results"]) == 2
    
    def test_get_summary_wrong_user(
        self,
        client,
        test_lesson_attempt,
        db_session
    ):
        """Test summary retrieval by different user"""
        # Create another user
        other_user = User(
            id=generate_test_id(),
            email="other@example.com",
            password_hash=hash_password("password123"),
            full_name="Other User",
            current_level="beginner",
            is_active=True,
            role="student"
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        # Create auth headers for other user
        other_token = create_access_token(
            data={"sub": str(other_user.id), "email": other_user.email}
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        # Try to access the first user's lesson attempt
        response = client.get(
            f"/api/v1/pronunciation/summary/{test_lesson_attempt.id}",
            headers=other_headers
        )
        
        # Should return 404 because lesson_attempt doesn't belong to this user
        assert response.status_code == 404


# ============================================================
# Run tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
