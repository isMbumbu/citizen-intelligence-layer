"""SQLModel persistence models registered for Alembic metadata."""

from app.models.service_state import ServiceState
from app.models.vertical_slice import (
    CitizenIssueReport,
    Claim,
    ClaimSource,
    Contractor,
    County,
    FinancialRecord,
    Project,
    ProjectContract,
    ProjectProgress,
    ProjectVerification,
    Source,
    SourceRecord,
    SubCounty,
    Ward,
)

__all__ = [
    "CitizenIssueReport",
    "Claim",
    "ClaimSource",
    "Contractor",
    "County",
    "FinancialRecord",
    "Project",
    "ProjectContract",
    "ProjectProgress",
    "ProjectVerification",
    "ServiceState",
    "Source",
    "SourceRecord",
    "SubCounty",
    "Ward",
]
