"""SQLModel persistence models registered for Alembic metadata."""

from app.models.citizen_comments import CitizenComment, CommentReport
from app.models.service_state import ServiceState
from app.models.vertical_slice import (
    CitizenIssueReport,
    Claim,
    ClaimSource,
    Contractor,
    County,
    FinancialRecord,
    Project,
    ProjectCategory,
    ProjectContract,
    ProjectProgress,
    ProjectSubtype,
    ProjectVerification,
    Source,
    SourceRecord,
    SubCounty,
    Ward,
)

__all__ = [
    "CitizenIssueReport",
    "CitizenComment",
    "CommentReport",
    "Claim",
    "ClaimSource",
    "Contractor",
    "County",
    "FinancialRecord",
    "Project",
    "ProjectCategory",
    "ProjectContract",
    "ProjectProgress",
    "ProjectSubtype",
    "ProjectVerification",
    "ServiceState",
    "Source",
    "SourceRecord",
    "SubCounty",
    "Ward",
]
