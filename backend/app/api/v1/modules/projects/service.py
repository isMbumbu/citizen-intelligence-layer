"""Application functions for public-project exploration and review flags."""

from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.contracts import repository as contracts_repository
from app.api.v1.modules.finance import repository as finance_repository
from app.api.v1.modules.geography import repository as geography_repository
from app.api.v1.modules.projects import repository
from app.api.v1.modules.projects.schemas import (
    ClaimEvidenceResponse,
    ClaimReferenceResponse,
    ContractorResponse,
    FinancialFactResponse,
    FinancialSummaryResponse,
    LocationResponse,
    ProgressResponse,
    ProjectAnomalyResponse,
    ProjectDetailResponse,
    ProjectListItemResponse,
    ProjectPageResponse,
    SourceReferenceResponse,
    TimelineResponse,
    VerificationResponse,
)
from app.api.v1.modules.sources import repository as sources_repository
from app.api.v1.modules.verification import repository as verification_repository
from app.core.logging import logger
from app.models.enums import FinancialKind, ProjectStatus, ProjectType
from app.models.vertical_slice import (
    Claim,
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

_REVIEW_GAP_PERCENTAGE_POINTS = Decimal("25")
_PERCENTAGE_QUANTUM = Decimal("0.01")
_EvidenceMap = dict[UUID, list[tuple[SourceRecord, Source]]]


async def list_projects(
    session: AsyncSession,
    *,
    county: str | None,
    ward: str | None,
    project_type: ProjectType | None,
    project_status: ProjectStatus | None,
    search: str | None,
    page: int,
    page_size: int,
) -> ProjectPageResponse:
    """Return a filtered public-project page with resolved location names."""
    try:
        projects, total = await repository.list_projects(
            session,
            county=county,
            ward=ward,
            project_type=project_type,
            status=project_status,
            search=search,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        items = [await _list_item(session, project) for project in projects]
    except HTTPException:
        raise
    except Exception as error:
        await session.rollback()
        logger.exception("Unable to list projects")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve projects.",
        ) from error
    logger.info("Listed %s project(s) from %s matching record(s)", len(items), total)
    return ProjectPageResponse(items=items, page=page, page_size=page_size, total=total)


async def get_project_detail(
    session: AsyncSession,
    project_id: UUID,
) -> ProjectDetailResponse:
    """Return one project page with sourced facts and no derived accusations."""
    try:
        project = await _project_or_404(session, project_id)
        location = await _location_or_error(session, project)
        financial_records = await finance_repository.list_for_project(
            session, project_id
        )
        contract = await contracts_repository.get_current_for_project(
            session, project_id
        )
        progress = await repository.get_latest_progress(session, project_id)
        verification = await verification_repository.get_latest_for_project(
            session,
            project_id,
        )
        claims = await sources_repository.list_claims_for_project(session, project_id)
        evidence_by_claim = await sources_repository.evidence_for_claims(
            session,
            {claim.id for claim in claims},
        )
        verification_source = await _verification_source(session, verification)
        anomalies = await _derive_project_anomalies(session, project_id)
    except HTTPException:
        raise
    except Exception as error:
        await session.rollback()
        logger.exception("Unable to retrieve project id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve project.",
        ) from error

    logger.info("Retrieved project id=%s", project.id)
    return ProjectDetailResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        location=_location_response(location),
        financial_summary=_financial_summary(financial_records, evidence_by_claim),
        contractor=_contract_response(contract, evidence_by_claim),
        progress=_progress_response(progress, evidence_by_claim),
        timeline=TimelineResponse(
            planned_start_date=project.planned_start_date,
            planned_completion_date=project.planned_completion_date,
            actual_start_date=project.actual_start_date,
            expected_completion_date=project.expected_completion_date,
        ),
        last_verified_at=project.last_verified_at,
        verification=(
            VerificationResponse(
                status=verification.status,
                verification_date=verification.verification_date,
                recorded_at=verification.recorded_at,
                notes=verification.notes,
                source=verification_source,
            )
            if verification is not None
            else None
        ),
        anomalies=anomalies,
        evidence=[
            _claim_evidence_response(claim, evidence_by_claim) for claim in claims
        ],
    )


async def get_project_sources(
    session: AsyncSession,
    project_id: UUID,
) -> list[ClaimEvidenceResponse]:
    """Return every project claim with its supporting source record chain."""
    try:
        await _project_or_404(session, project_id)
        claims = await sources_repository.list_claims_for_project(session, project_id)
        evidence_by_claim = await sources_repository.evidence_for_claims(
            session,
            {claim.id for claim in claims},
        )
    except HTTPException:
        raise
    except Exception as error:
        await session.rollback()
        logger.exception("Unable to retrieve project sources id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve project sources.",
        ) from error
    return [_claim_evidence_response(claim, evidence_by_claim) for claim in claims]


async def get_project_verification(
    session: AsyncSession,
    project_id: UUID,
) -> VerificationResponse | None:
    """Return the explicit human verification record, separate from anomalies."""
    try:
        await _project_or_404(session, project_id)
        verification = await verification_repository.get_latest_for_project(
            session,
            project_id,
        )
        if verification is None:
            return None
        source = await _verification_source(session, verification)
    except HTTPException:
        raise
    except Exception as error:
        await session.rollback()
        logger.exception(
            "Unable to retrieve verification for project id=%s", project_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve project verification.",
        ) from error
    return VerificationResponse(
        status=verification.status,
        verification_date=verification.verification_date,
        recorded_at=verification.recorded_at,
        notes=verification.notes,
        source=source,
    )


async def get_project_anomalies(
    session: AsyncSession,
    project_id: UUID,
) -> list[ProjectAnomalyResponse]:
    """Derive review flags only from sourced progress and financial records."""
    await _project_or_404(session, project_id)
    return await _derive_project_anomalies(session, project_id)


async def _derive_project_anomalies(
    session: AsyncSession,
    project_id: UUID,
) -> list[ProjectAnomalyResponse]:
    """Derive review flags from sourced progress and financial records."""
    try:
        records = await finance_repository.list_for_project(session, project_id)
        progress = await repository.get_latest_progress(session, project_id)
        if progress is None:
            return []
        records_by_kind = {record.kind: record for record in records}
        allocated = records_by_kind.get(FinancialKind.ALLOCATED.value)
        spent = records_by_kind.get(FinancialKind.SPENT.value)
        if allocated is None or spent is None or allocated.amount <= 0:
            return []

        claim_ids = {progress.claim_id, allocated.claim_id, spent.claim_id}
        evidence_by_claim = await sources_repository.evidence_for_claims(
            session,
            claim_ids,
        )
        supporting_claims = [
            _claim_reference(claim_id, evidence_by_claim)
            for claim_id in sorted(claim_ids, key=str)
        ]
        if any(not claim.sources for claim in supporting_claims):
            return []
        spent_share = (spent.amount / allocated.amount * Decimal("100")).quantize(
            _PERCENTAGE_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        if progress.percentage - spent_share < _REVIEW_GAP_PERCENTAGE_POINTS:
            return []
    except HTTPException:
        raise
    except Exception as error:
        await session.rollback()
        logger.exception("Unable to derive review flags for project id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve project review flags.",
        ) from error

    logger.info("Derived progress-spend review flag for project id=%s", project_id)
    return [
        ProjectAnomalyResponse(
            type="PROGRESS_SPEND_GAP",
            status="REVIEW_REQUIRED",
            message=(
                "Reported project progress is substantially higher than the "
                "share of the allocated budget recorded as spent. This may "
                "warrant verification."
            ),
            requires_verification=True,
            reported_progress_percentage=progress.percentage,
            spent_budget_percentage=spent_share,
            supporting_claims=supporting_claims,
        )
    ]


async def _list_item(
    session: AsyncSession,
    project: Project,
) -> ProjectListItemResponse:
    """Build one browse result after resolving its bounded geography hierarchy."""
    location = await _location_or_error(session, project)
    return ProjectListItemResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        location=_location_response(location),
    )


async def _project_or_404(session: AsyncSession, project_id: UUID) -> Project:
    """Load a project or return the stable public not-found response."""
    project = await repository.get(session, project_id)
    if project is None:
        logger.info("Project was not found id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


async def _location_or_error(
    session: AsyncSession,
    project: Project,
) -> tuple[County, SubCounty, Ward]:
    """Resolve required project geography or surface a safe data-integrity error."""
    location = await geography_repository.get_location_for_ward(
        session, project.ward_id
    )
    if location is None:
        logger.error("Project has unresolved geography id=%s", project.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project location is unavailable.",
        )
    return location


def _location_response(
    location: tuple[County, SubCounty, Ward],
) -> LocationResponse:
    """Convert resolved SQLModel geography records into the public contract."""
    county, sub_county, ward = location
    return LocationResponse(
        county_id=county.id,
        county=county.name,
        sub_county_id=sub_county.id,
        sub_county=sub_county.name,
        ward_id=ward.id,
        ward=ward.name,
    )


def _financial_summary(
    records: list[FinancialRecord],
    evidence_by_claim: _EvidenceMap,
) -> FinancialSummaryResponse:
    """Map distinct monetary concepts into the project financial summary."""
    values: dict[str, FinancialFactResponse] = {}
    for record in records:
        values[record.kind.lower()] = FinancialFactResponse(
            kind=record.kind,
            amount=record.amount,
            currency=record.currency,
            financial_period=record.financial_period,
            evidence=_claim_reference(record.claim_id, evidence_by_claim),
        )
    return FinancialSummaryResponse(**values)


def _contract_response(
    contract_data: tuple[ProjectContract, Contractor] | None,
    evidence_by_claim: _EvidenceMap,
) -> ContractorResponse | None:
    """Return the current contractor without flattening it into a project string."""
    if contract_data is None:
        return None
    contract, contractor = contract_data
    return ContractorResponse(
        id=contractor.id,
        legal_name=contractor.legal_name,
        award_reference=contract.award_reference,
        contract_status=contract.contract_status,
        contract_start_date=contract.contract_start_date,
        contract_end_date=contract.contract_end_date,
        evidence=_claim_reference(contract.claim_id, evidence_by_claim),
    )


def _progress_response(
    progress: ProjectProgress | None,
    evidence_by_claim: _EvidenceMap,
) -> ProgressResponse | None:
    """Return the latest reported progress with its material claim reference."""
    if progress is None:
        return None
    return ProgressResponse(
        percentage=progress.percentage,
        reported_at=progress.reported_at,
        evidence=_claim_reference(progress.claim_id, evidence_by_claim),
    )


def _claim_evidence_response(
    claim: Claim,
    evidence_by_claim: _EvidenceMap,
) -> ClaimEvidenceResponse:
    """Convert a claim and its source-record evidence into the API contract."""
    return ClaimEvidenceResponse(
        id=claim.id,
        claim_kind=claim.claim_kind,
        field_name=claim.field_name,
        value_text=claim.value_text,
        numeric_value=claim.numeric_value,
        currency=claim.currency,
        financial_period=claim.financial_period,
        sources=[
            _source_reference(record, source)
            for record, source in evidence_by_claim.get(claim.id, [])
        ],
    )


def _claim_reference(
    claim_id: UUID,
    evidence_by_claim: _EvidenceMap,
) -> ClaimReferenceResponse:
    """Return only the source chain required to support one displayed fact."""
    return ClaimReferenceResponse(
        claim_id=claim_id,
        sources=[
            _source_reference(record, source)
            for record, source in evidence_by_claim.get(claim_id, [])
        ],
    )


async def _verification_source(
    session: AsyncSession,
    verification: ProjectVerification | None,
) -> SourceReferenceResponse | None:
    """Resolve the optional source record attached to a verification state."""
    if verification is None or verification.source_record_id is None:
        return None
    evidence = await sources_repository.evidence_for_source_record(
        session,
        verification.source_record_id,
    )
    if evidence is None:
        return None
    record, source = evidence
    return _source_reference(record, source)


def _source_reference(
    record: SourceRecord,
    source: Source,
) -> SourceReferenceResponse:
    """Convert source persistence data into a safe public provenance reference."""
    return SourceReferenceResponse(
        source_id=source.id,
        source_record_id=record.id,
        publisher=source.publisher,
        title=source.title,
        source_type=source.source_type,
        url=source.url,
        publication_date=source.publication_date,
        retrieved_at=source.retrieved_at,
        record_summary=record.content_summary,
    )
