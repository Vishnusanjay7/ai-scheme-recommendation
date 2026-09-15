"""Models package initialization."""

from app.models.scheme import (
    RawScheme,
    NormalizedScheme,
    SchemeEligibilityData,
    SchemeDocumentData,
    SchemeSourceData,
    ValidationResult,
    SchemeItemResponse,
    SchemeDetailResponse,
    SchemeListResponse,
)
from app.models.eligibility import (
    CriterionResult,
    EligibilityStatus,
    DISPLAY_STATUS_MAP,
    UserProfileInput,
    CriterionEvaluation,
    EligibilityExplanation,
    EligibilityEvaluationRequest,
    EligibilityEvaluationResponse,
    BulkEligibilityResponse,
)

from app.models.deadline import (
    ActivityStatus,
    DeadlineClassification,
    SchemeActivityInfo,
)
from app.models.recommendation import (
    AIRankedItem,
    AIRankingOutput,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
    VerificationRequiredItem,
)

from app.models.saved_scheme import (
    SavedSchemeResponse,
    SavedSchemeStatusResponse,
    SaveSchemeActionResponse,
)
from app.models.notification import (
    NotificationType,
    NotificationStatus,
    NotificationResponse,
    UnreadNotificationsResponse,
    NotificationActionResponse,
    DeadlineMonitoringResult,
)
from app.models.chat import (
    ChatIntent,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryItem,
    ChatHistoryResponse,
)

__all__ = [
    "RawScheme",
    "NormalizedScheme",
    "SchemeEligibilityData",
    "SchemeDocumentData",
    "SchemeSourceData",
    "ValidationResult",
    "SchemeItemResponse",
    "SchemeDetailResponse",
    "SchemeListResponse",
    "CriterionResult",
    "EligibilityStatus",
    "DISPLAY_STATUS_MAP",
    "UserProfileInput",
    "CriterionEvaluation",
    "EligibilityExplanation",
    "EligibilityEvaluationRequest",
    "EligibilityEvaluationResponse",
    "BulkEligibilityResponse",
    "ActivityStatus",
    "DeadlineClassification",
    "SchemeActivityInfo",
    "AIRankedItem",
    "AIRankingOutput",
    "RecommendationItem",
    "RecommendationRequest",
    "RecommendationResponse",
    "VerificationRequiredItem",
    "SavedSchemeResponse",
    "SavedSchemeStatusResponse",
    "SaveSchemeActionResponse",
    "NotificationType",
    "NotificationStatus",
    "NotificationResponse",
    "UnreadNotificationsResponse",
    "NotificationActionResponse",
    "DeadlineMonitoringResult",
    "ChatIntent",
    "ChatMessageRequest",
    "ChatMessageResponse",
    "ChatHistoryItem",
    "ChatHistoryResponse",
]

