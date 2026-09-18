"""String enums shared by persistence-adjacent and API contracts."""

from enum import StrEnum


class ProjectStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class FinancialKind(StrEnum):
    ALLOCATED = "ALLOCATED"
    COMMITTED = "COMMITTED"
    CONTRACTED = "CONTRACTED"
    SPENT = "SPENT"
    REPORTED = "REPORTED"


class SourceType(StrEnum):
    DEMONSTRATION_RECORD = "DEMONSTRATION_RECORD"
    OFFICIAL_DOCUMENT = "OFFICIAL_DOCUMENT"
    OFFICIAL_DATASET = "OFFICIAL_DATASET"
    CIVIL_SOCIETY_RECORD = "CIVIL_SOCIETY_RECORD"


class ClaimKind(StrEnum):
    FINANCIAL = "FINANCIAL"
    CONTRACTOR = "CONTRACTOR"
    PROGRESS = "PROGRESS"
    VERIFICATION = "VERIFICATION"


class VerificationStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    VERIFIED = "VERIFIED"
    STALE = "STALE"
    DISPUTED = "DISPUTED"


class ReportCategory(StrEnum):
    QUALITY = "QUALITY"
    DELAY = "DELAY"
    ACCESS = "ACCESS"
    SAFETY = "SAFETY"
    OTHER = "OTHER"


class ReportStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    REFERRED = "REFERRED"
    RESPONDED = "RESPONDED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CommentStatus(StrEnum):
    ACTIVE = "ACTIVE"


class CommentModerationState(StrEnum):
    PENDING = "PENDING"


class CommentVisibility(StrEnum):
    PUBLIC = "PUBLIC"


class CommentReportReason(StrEnum):
    SPAM = "SPAM"
    HARASSMENT = "HARASSMENT"
    PERSONAL_INFORMATION = "PERSONAL_INFORMATION"
    INAPPROPRIATE = "INAPPROPRIATE"
    OTHER = "OTHER"


class CommentReportStatus(StrEnum):
    SUBMITTED = "SUBMITTED"


class EvidenceSourceClass(StrEnum):
    CITIZEN_SUBMITTED = "CITIZEN_SUBMITTED"


class EvidenceModerationState(StrEnum):
    PENDING = "PENDING"
    FLAGGED = "FLAGGED"
    HIDDEN = "HIDDEN"
    REMOVED = "REMOVED"


class EvidenceProcessingState(StrEnum):
    RAW = "RAW"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    EXTRACTED = "EXTRACTED"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
    HIDDEN = "HIDDEN"


class EvidenceVisibility(StrEnum):
    PRIVATE = "PRIVATE"
    PENDING = "PENDING"
    PUBLIC = "PUBLIC"
