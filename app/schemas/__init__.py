"""
Schemas package initialization - Export all Pydantic schemas
"""
# User schemas
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse, RefreshTokenRequest

# Topic schemas
from app.schemas.topic import (
    TopicCreate, TopicUpdate, TopicBasicResponse, 
    TopicListResponse, TopicWithProgressResponse, TopicFilter
)

# Vocabulary schemas
from app.schemas.vocabulary import (
    VocabularyCreate, VocabularyUpdate, VocabularyResponse,
    VocabularyForMatchingGame, VocabularyWithUserProgress,
    VocabularyMatchSubmit, VocabularyMatchingSubmitRequest,
    VocabularyMatchingResultResponse, VocabularyMatchingSummary,
    UserVocabularySaveRequest, UserVocabularyListResponse
)

# Lesson schemas
from app.schemas.lesson import (
    LessonCreate, PronunciationExerciseCreate, ConversationTemplateCreate,
    LessonBasicResponse, LessonWithProgressResponse,
    PronunciationExerciseResponse, ConversationTemplateResponse,
    VocabularyMatchingLessonDetail, PronunciationLessonDetail,
    ConversationLessonDetail, TopicDetailResponse
)

# Pronunciation schemas
from app.schemas.pronunciation import (
    PronunciationSubmitRequest, PronunciationSubmitBase64Request,
    PronunciationScoreDetail, PronunciationFeedback, WordAnalysis,
    PronunciationAttemptResponse, PronunciationLessonSummary
)

# Conversation schemas
from app.schemas.conversation import (
    ConversationMessageCreate, ConversationMessageWithAudio,
    GrammarError, ConversationMessageResponse, AIConversationResponse,
    ConversationStartRequest, ConversationStartResponse,
    ConversationEndRequest, ConversationSummary, ConversationHistoryResponse
)

# Attempt schemas
from app.schemas.attempt import (
    LessonAttemptCreate, LessonAttemptComplete,
    LessonAttemptResponse, LessonAttemptStartResponse,
    LessonAttemptSummary, LessonAttemptHistoryItem,
    LessonAttemptHistoryResponse, UserLessonStats
)

# Progress schemas
from app.schemas.progress import (
    UserLessonProgressResponse, UserLessonProgressUpdate,
    UserTopicProgressResponse, DailyStatsResponse,
    WeeklyStatsResponse, MonthlyStatsResponse,
    UserStreakResponse, UserOverallProgress,
    LeaderboardEntry, LeaderboardResponse, Achievement, UserAchievementsResponse
)

__all__ = [
    # User
    "UserRegister", "UserLogin", "UserResponse", "TokenResponse", "RefreshTokenRequest",
    
    # Topic
    "TopicCreate", "TopicUpdate", "TopicBasicResponse",
    "TopicListResponse", "TopicWithProgressResponse", "TopicFilter",
    
    # Vocabulary
    "VocabularyCreate", "VocabularyUpdate", "VocabularyResponse",
    "VocabularyForMatchingGame", "VocabularyWithUserProgress",
    "VocabularyMatchSubmit", "VocabularyMatchingSubmitRequest",
    "VocabularyMatchingResultResponse", "VocabularyMatchingSummary",
    "UserVocabularySaveRequest", "UserVocabularyListResponse",
    
    # Lesson
    "LessonCreate", "PronunciationExerciseCreate", "ConversationTemplateCreate",
    "LessonBasicResponse", "LessonWithProgressResponse",
    "PronunciationExerciseResponse", "ConversationTemplateResponse",
    "VocabularyMatchingLessonDetail", "PronunciationLessonDetail",
    "ConversationLessonDetail", "TopicDetailResponse",
    
    # Pronunciation
    "PronunciationSubmitRequest", "PronunciationSubmitBase64Request",
    "PronunciationScoreDetail", "PronunciationFeedback", "WordAnalysis",
    "PronunciationAttemptResponse", "PronunciationLessonSummary",
    
    # Conversation
    "ConversationMessageCreate", "ConversationMessageWithAudio",
    "GrammarError", "ConversationMessageResponse", "AIConversationResponse",
    "ConversationStartRequest", "ConversationStartResponse",
    "ConversationEndRequest", "ConversationSummary", "ConversationHistoryResponse",
    
    # Attempt
    "LessonAttemptCreate", "LessonAttemptComplete",
    "LessonAttemptResponse", "LessonAttemptStartResponse",
    "LessonAttemptSummary", "LessonAttemptHistoryItem",
    "LessonAttemptHistoryResponse", "UserLessonStats",
    
    # Progress
    "UserLessonProgressResponse", "UserLessonProgressUpdate",
    "UserTopicProgressResponse", "DailyStatsResponse",
    "WeeklyStatsResponse", "MonthlyStatsResponse",
    "UserStreakResponse", "UserOverallProgress",
    "LeaderboardEntry", "LeaderboardResponse", "Achievement", "UserAchievementsResponse",
]
