"""String enums shared by persistence-adjacent and API contracts."""

from enum import StrEnum


class ProjectType(StrEnum):
    ROAD = "ROAD"
    HEALTH = "HEALTH"
    WATER = "WATER"
    EDUCATION = "EDUCATION"


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
