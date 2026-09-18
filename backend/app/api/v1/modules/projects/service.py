"""Application functions for public-project exploration and review flags."""

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.contracts import repository as contracts_repository
from app.api.v1.modules.finance import repository as finance_repository
from app.api.v1.modules.geography import repository as geography_repository
from app.api.v1.modules.projects import repository
from app.api.v1.modules.projects.schemas import (
    AnomalyResponse,
    ClaimEvidenceResponse,
    ClaimReferenceResponse,
    ContractorResponse,
    FinancialAnomalyResponse,
    FinancialFactResponse,
    FinancialSummaryResponse,
    LocationResponse,
    ProgressResponse,
    ProjectAnomalyResponse,
    ProjectCategoryLabelResponse,
    ProjectDetailResponse,
    ProjectListItemResponse,
    ProjectPageResponse,
    ProjectSubtypeLabelResponse,
    SourceReferenceResponse,
    TimelineAnomalyResponse,
    TimelineResponse,
    VerificationResponse,
)
from app.api.v1.modules.sources import repository as sources_repository
from app.api.v1.modules.taxonomy import repository as taxonomy_repository
from app.api.v1.modules.verification import repository as verification_repository
from app.core.logging import logger
from app.models.enums import (
    ClaimKind,
    FinancialKind,
    ProjectStatus,
    SourceType,
    VerificationStatus,
)
from app.models.vertical_slice import (
    Claim,
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

_REVIEW_GAP_PERCENTAGE_POINTS = Decimal("25")
_PERCENTAGE_QUANTUM = Decimal("0.01")
_EvidenceMap = dict[UUID, list[tuple[SourceRecord, Source]]]


async def list_projects(
    session: AsyncSession,
    *,
    county: str | None,
    ward: str | None,
    project_type: str | None,
    category_id: UUID | None,
    subtype_id: UUID | None,
    project_status: ProjectStatus | None,
    search: str | None,
    page: int,
    page_size: int,
) -> ProjectPageResponse:
    """Return a filtered public-project page with resolved location names."""
    try:
        category, subtype = await _validate_taxonomy_filters(
            session,
            category_id=category_id,
            subtype_id=subtype_id,
        )
        projects, total = await repository.list_projects(
            session,
            county=county,
            ward=ward,
            project_type=project_type,
            category_id=category_id,
            subtype_id=subtype_id,
            status=project_status,
            search=search,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        items = [
            await _list_item(session, project, category=category, subtype=subtype)
            for project in projects
        ]
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
        category, subtype = await _project_taxonomy_or_error(session, project)
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
        anomalies = await _derive_project_anomalies(
            session,
            project_id,
            project=project,
        )
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
        category=_category_label(category),
        subtype=_subtype_label(subtype),
        status=ProjectStatus(project.status),
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
                status=VerificationStatus(verification.status),
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
        status=VerificationStatus(verification.status),
        verification_date=verification.verification_date,
        recorded_at=verification.recorded_at,
        notes=verification.notes,
        source=source,
    )


async def get_project_anomalies(
    session: AsyncSession,
    project_id: UUID,
) -> list[AnomalyResponse]:
    """Derive review flags only from sourced progress and financial records."""
    project = await _project_or_404(session, project_id)
    return await _derive_project_anomalies(session, project_id, project=project)


async def _derive_project_anomalies(
    session: AsyncSession,
    project_id: UUID,
    *,
    project: Project | None = None,
) -> list[AnomalyResponse]:
    """Derive review flags from sourced progress and financial records."""
    try:
        project = project or await _project_or_404(session, project_id)
        records = await finance_repository.list_for_project(session, project_id)
        progress = await repository.get_latest_progress(session, project_id)
        records_by_kind = {record.kind: record for record in records}
        allocated = records_by_kind.get(FinancialKind.ALLOCATED.value)
        spent = records_by_kind.get(FinancialKind.SPENT.value)
        contracted = records_by_kind.get(FinancialKind.CONTRACTED.value)
        claim_ids = {
            record.claim_id
            for record in (progress, allocated, spent, contracted)
            if record is not None
        }
        evidence_by_claim = await sources_repository.evidence_for_claims(
            session,
            claim_ids,
        )
    except HTTPException:
        raise
    except Exception as error:
        await session.rollback()
        logger.exception("Unable to derive review flags for project id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve project review flags.",
        ) from error

    signals: list[AnomalyResponse] = []
    if progress is not None and allocated is not None and spent is not None:
        progress_claims = _claim_reference(progress.claim_id, evidence_by_claim)
        allocated_claims = _claim_reference(allocated.claim_id, evidence_by_claim)
        spent_claims = _claim_reference(spent.claim_id, evidence_by_claim)
        supporting_claims = sorted(
            [progress_claims, allocated_claims, spent_claims],
            key=lambda claim: str(claim.claim_id),
        )
        if all(claim.sources for claim in supporting_claims) and allocated.amount > 0:
            spent_share = (spent.amount / allocated.amount * Decimal("100")).quantize(
                _PERCENTAGE_QUANTUM,
                rounding=ROUND_HALF_UP,
            )
            if progress.percentage - spent_share >= _REVIEW_GAP_PERCENTAGE_POINTS:
                signals.append(
                    ProjectAnomalyResponse(
                        type="PROGRESS_SPEND_GAP",
                        status="REVIEW_REQUIRED",
                        message=(
                            "Reported project progress is substantially higher "
                            "than the share of the allocated budget recorded "
                            "as spent. This may "
                            "warrant verification."
                        ),
                        requires_verification=True,
                        reported_progress_percentage=progress.percentage,
                        spent_budget_percentage=spent_share,
                        supporting_claims=supporting_claims,
                    )
                )

    if spent is not None:
        signals.extend(
            _financial_anomaly_signals(
                spent,
                allocated,
                contracted,
                evidence_by_claim,
            )
        )
    timeline_signal = _timeline_past_due_signal(project)
    if timeline_signal is not None:
        signals.append(timeline_signal)
    if signals:
        logger.info("Derived project review flags for project id=%s", project_id)
    return signals


def _timeline_past_due_signal(
    project: Project,
) -> TimelineAnomalyResponse | None:
    """Return the approved project-level past-due timeline signal."""
    planned_completion_date = getattr(project, "planned_completion_date", None)
    if project.status != ProjectStatus.IN_PROGRESS.value:
        return None
    if planned_completion_date is None:
        return None
    if project.planned_start_date > planned_completion_date:
        return None
    if (
        project.actual_start_date is not None
        and project.actual_start_date > planned_completion_date
    ):
        return None
    if datetime.now(UTC).date() <= planned_completion_date:
        return None
    return TimelineAnomalyResponse(
        type="TIMELINE_PAST_DUE",
        status="REVIEW_REQUIRED",
        message=(
            "The project is past its planned completion date without a recorded "
            "completion date. This may warrant verification."
        ),
        requires_verification=True,
        planned_completion_date=planned_completion_date,
        supporting_claims=[],
    )


def _financial_anomaly_signals(
    spent: FinancialRecord,
    allocated: FinancialRecord | None,
    contracted: FinancialRecord | None,
    evidence_by_claim: _EvidenceMap,
) -> list[FinancialAnomalyResponse]:
    """Build INT-002 financial signals from compatible sourced records."""
    signals: list[FinancialAnomalyResponse] = []
    for comparison, comparison_kind, signal_type, message in (
        (
            allocated,
            FinancialKind.ALLOCATED.value,
            "SPEND_OVER_ALLOCATION",
            (
                "Recorded spending exceeds the allocated amount. "
                "This may warrant verification."
            ),
        ),
        (
            contracted,
            FinancialKind.CONTRACTED.value,
            "SPEND_OVER_CONTRACT",
            (
                "Recorded spending exceeds the contracted amount. "
                "This may warrant verification."
            ),
        ),
    ):
        if comparison is None:
            continue
        if (
            spent.amount <= 0
            or comparison.amount <= 0
            or spent.currency != comparison.currency
            or spent.financial_period != comparison.financial_period
            or spent.amount <= comparison.amount
        ):
            continue
        claim_ids = sorted(
            [spent.claim_id, comparison.claim_id],
            key=str,
        )
        supporting_claims = [
            _claim_reference(claim_id, evidence_by_claim) for claim_id in claim_ids
        ]
        if any(not claim.sources for claim in supporting_claims):
            continue
        signals.append(
            FinancialAnomalyResponse(
                type=signal_type,
                status="REVIEW_REQUIRED",
                message=message,
                requires_verification=True,
                spent_amount=spent.amount,
                comparison_amount=comparison.amount,
                comparison_kind=comparison_kind,
                currency=spent.currency,
                financial_period=spent.financial_period,
                supporting_claims=supporting_claims,
            )
        )
    return signals


async def _list_item(
    session: AsyncSession,
    project: Project,
    *,
    category: ProjectCategory | None = None,
    subtype: ProjectSubtype | None = None,
) -> ProjectListItemResponse:
    """Build one browse result after resolving its bounded geography hierarchy."""
    location = await _location_or_error(session, project)
    if category is None or category.id != project.category_id:
        category, subtype = await _project_taxonomy_or_error(session, project)
    return ProjectListItemResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        project_type=project.project_type,
        category=_category_label(category),
        subtype=_subtype_label(subtype),
        status=ProjectStatus(project.status),
        location=_location_response(location),
    )


async def _validate_taxonomy_filters(
    session: AsyncSession,
    *,
    category_id: UUID | None,
    subtype_id: UUID | None,
) -> tuple[ProjectCategory | None, ProjectSubtype | None]:
    """Validate active taxonomy filters and their parent-child relationship."""
    category = (
        await taxonomy_repository.get_active_category(session, category_id)
        if category_id is not None
        else None
    )
    if category_id is not None and category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project category not found.",
        )

    subtype = (
        await taxonomy_repository.get_active_subtype(session, subtype_id)
        if subtype_id is not None
        else None
    )
    if subtype_id is not None and subtype is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project subtype not found.",
        )
    if category is not None and subtype is not None:
        if subtype.category_id != category.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Project subtype does not belong to project category.",
            )
    return category, subtype


async def _project_taxonomy_or_error(
    session: AsyncSession,
    project: Project,
) -> tuple[ProjectCategory, ProjectSubtype | None]:
    """Resolve the active taxonomy labels attached to a project."""
    category = await taxonomy_repository.get_active_category(
        session,
        project.category_id,
    )
    subtype = (
        await taxonomy_repository.get_active_subtype(session, project.subtype_id)
        if project.subtype_id is not None
        else None
    )
    if category is None or (project.subtype_id is not None and subtype is None):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project taxonomy is unavailable.",
        )
    if subtype is not None and subtype.category_id != category.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project taxonomy is inconsistent.",
        )
    return category, subtype


def _category_label(category: ProjectCategory) -> ProjectCategoryLabelResponse:
    return ProjectCategoryLabelResponse(
        id=category.id,
        code=category.code,
        name=category.name,
    )


def _subtype_label(
    subtype: ProjectSubtype | None,
) -> ProjectSubtypeLabelResponse | None:
    if subtype is None:
        return None
    return ProjectSubtypeLabelResponse(
        id=subtype.id,
        code=subtype.code,
        name=subtype.name,
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
            kind=FinancialKind(record.kind),
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
        claim_kind=ClaimKind(claim.claim_kind),
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
        source_type=SourceType(source.source_type),
        url=source.url,
        publication_date=source.publication_date,
        retrieved_at=source.retrieved_at,
        record_summary=record.content_summary,
    )
