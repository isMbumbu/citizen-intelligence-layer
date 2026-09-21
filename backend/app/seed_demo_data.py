"""Idempotently seed clearly labelled fictional project-explorer demo data.

Run from ``backend/`` with ``python -m app.seed_demo_data`` after migrations.
The records are illustrative and must never be represented as government data.
"""

import asyncio
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol, TypedDict, cast
from uuid import UUID, uuid5

from sqlmodel import SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import async_session_maker, close_database
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

_DEMO_NAMESPACE = UUID("a48a4e7d-9537-4c9f-aab7-b8e663b37720")
_DEMO_TIMESTAMP = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
_FINANCIAL_PERIOD = "FY 2026/27"


class ProjectSeed(TypedDict):
    """Static project values used to construct deterministic demo records."""

    key: str
    name: str
    description: str
    legacy_project_type: str
    category_code: str
    subtype_code: str | None
    status: ProjectStatus
    ward: str
    planned_start: date
    planned_completion: date
    actual_start: date | None
    expected_completion: date | None
    contractor: str
    award: str
    allocated: Decimal
    committed: Decimal
    contracted: Decimal
    spent: Decimal
    reported: Decimal
    progress: Decimal
    progress_date: date


class _SeedRecordWithId(Protocol):
    """Structural type for seeded SQLModel records with UUID primary keys."""

    id: UUID


def _id(key: str) -> UUID:
    """Create stable identifiers so repeated seed runs never duplicate records."""
    return uuid5(_DEMO_NAMESPACE, key)


async def _add_if_missing(session: AsyncSession, record: SQLModel) -> bool:
    """Stage a fixed-ID record only when it is not already persisted."""
    record_type: type[SQLModel] = type(record)
    if isinstance(record, ClaimSource):
        record_id: UUID | tuple[UUID, UUID] = (
            record.claim_id,
            record.source_record_id,
        )
    else:
        record_id = cast(_SeedRecordWithId, record).id
    if await session.get(record_type, record_id) is not None:
        return False
    session.add(record)
    return True


async def _stage(session: AsyncSession, records: list[SQLModel]) -> int:
    """Stage one dependency layer and flush it before dependent rows are added."""
    created = 0
    for record in records:
        if await _add_if_missing(session, record):
            created += 1
    await session.flush()
    return created


async def _taxonomy_ids(
    session: AsyncSession,
    projects: list[ProjectSeed],
) -> tuple[dict[str, UUID], dict[str, UUID]]:
    """Resolve database-managed taxonomy records required by the demo projects."""
    category_codes = {project["category_code"] for project in projects}
    subtype_codes = {
        subtype_code
        for project in projects
        if (subtype_code := project["subtype_code"]) is not None
    }
    categories_result = await session.exec(
        select(ProjectCategory).where(col(ProjectCategory.code).in_(category_codes))
    )
    subtypes_result = await session.exec(
        select(ProjectSubtype).where(col(ProjectSubtype.code).in_(subtype_codes))
    )
    category_ids = {category.code: category.id for category in categories_result.all()}
    subtype_ids = {subtype.code: subtype.id for subtype in subtypes_result.all()}
    missing_categories = category_codes - category_ids.keys()
    missing_subtypes = subtype_codes - subtype_ids.keys()
    if missing_categories or missing_subtypes:
        raise RuntimeError(
            "Project taxonomy reference data is unavailable: "
            f"categories={sorted(missing_categories)}, "
            f"subtypes={sorted(missing_subtypes)}"
        )
    return category_ids, subtype_ids


async def seed_demo_data(session: AsyncSession) -> int:
    """Create four traceable, fictional Kenyan project examples exactly once."""
    locations: list[tuple[str, str, str, str, str, str, str]] = [
        (
            "kisumu",
            "Kisumu",
            "KE-DEMO-KSM",
            "nyando",
            "Nyando Demo",
            "kobura",
            "Kobura Demo Ward",
        ),
        (
            "nakuru",
            "Nakuru",
            "KE-DEMO-NKR",
            "naivasha",
            "Naivasha Demo",
            "maai-mahiu",
            "Maai Mahiu Demo Ward",
        ),
        (
            "kitui",
            "Kitui",
            "KE-DEMO-KTI",
            "kitui-central",
            "Kitui Central Demo",
            "town",
            "Kitui Town Demo Ward",
        ),
        (
            "nairobi",
            "Nairobi City",
            "KE-DEMO-NRB",
            "westlands",
            "Westlands Demo",
            "kangemi",
            "Kangemi Demo Ward",
        ),
        (
            "makueni",
            "Makueni",
            "KE-DEMO-MKN",
            "kitui-south",
            "Kibwezi Demo",
            "kibwezi",
            "Kibwezi Demo Ward",
        ),
        (
            "garissa",
            "Garissa",
            "KE-DEMO-GRS",
            "garissa-east",
            "Garissa East Demo",
            "balambala",
            "Balambala Demo Ward",
        ),
        (
            "eldoret",
            "Uasin Gishu",
            "KE-DEMO-ELD",
            "eldoret-north",
            "Eldoret North Demo",
            "kapsoya",
            "Kapsoya Demo Ward",
        ),
        (
            "isiolo",
            "Isiolo",
            "KE-DEMO-ISL",
            "isiolo-central",
            "Isiolo Central Demo",
            "merti",
            "Merti Demo Ward",
        ),
        (
            "kajiado",
            "Kajiado",
            "KE-DEMO-KJD",
            "kajiado-south",
            "Kajiado South Demo",
            "oonkot",
            "Oonkot Demo Ward",
        ),
    ]
    created = 0
    county_records: list[SQLModel] = []
    sub_county_records: list[SQLModel] = []
    ward_records: list[SQLModel] = []
    for (
        county_key,
        county_name,
        county_code,
        sub_key,
        sub_name,
        ward_key,
        ward_name,
    ) in locations:
        county_id = _id(f"county:{county_key}")
        sub_county_id = _id(f"sub-county:{sub_key}")
        county_records.append(
            County(
                id=county_id,
                name=county_name,
                code=county_code,
                created_at=_DEMO_TIMESTAMP,
            )
        )
        sub_county_records.append(
            SubCounty(
                id=sub_county_id,
                county_id=county_id,
                name=sub_name,
                created_at=_DEMO_TIMESTAMP,
            )
        )
        ward_records.append(
            Ward(
                id=_id(f"ward:{ward_key}"),
                sub_county_id=sub_county_id,
                name=ward_name,
                created_at=_DEMO_TIMESTAMP,
            )
        )
    created += await _stage(session, county_records)
    created += await _stage(session, sub_county_records)
    created += await _stage(session, ward_records)

    projects: list[ProjectSeed] = [
        {
            "key": "nyando-road",
            "name": "Nyando–Kochieng Access Road Rehabilitation (Demo)",
            "description": (
                "Fictional demonstration rehabilitation of a local access road."
            ),
            "legacy_project_type": "ROAD",
            "category_code": "ROADS_TRANSPORT",
            "subtype_code": "ROAD_REHABILITATION",
            "status": ProjectStatus.IN_PROGRESS,
            "ward": "kobura",
            "planned_start": date(2026, 7, 1),
            "planned_completion": date(2027, 3, 31),
            "actual_start": date(2026, 7, 15),
            "expected_completion": date(2027, 4, 30),
            "contractor": "Lake Basin Works Ltd (fictional demo contractor)",
            "award": "DEMO-KSM-ROAD-001",
            "allocated": Decimal("20000000.00"),
            "committed": Decimal("17000000.00"),
            "contracted": Decimal("18500000.00"),
            "spent": Decimal("8000000.00"),
            "reported": Decimal("9000000.00"),
            "progress": Decimal("80.00"),
            "progress_date": date(2026, 8, 25),
        },
        {
            "key": "muhoroni-clinic",
            "name": "Muhoroni Community Clinic Improvement (Demo)",
            "description": (
                "Fictional demonstration upgrade of a community clinic wing."
            ),
            "legacy_project_type": "HEALTH",
            "category_code": "HEALTH",
            "subtype_code": "HEALTH_FACILITY",
            "status": ProjectStatus.IN_PROGRESS,
            "ward": "kobura",
            "planned_start": date(2026, 6, 1),
            "planned_completion": date(2026, 12, 20),
            "actual_start": date(2026, 6, 10),
            "expected_completion": date(2026, 12, 20),
            "contractor": "Equator Health Build Co. (fictional demo contractor)",
            "award": "DEMO-KSM-HEALTH-002",
            "allocated": Decimal("12000000.00"),
            "committed": Decimal("9000000.00"),
            "contracted": Decimal("10500000.00"),
            "spent": Decimal("6000000.00"),
            "reported": Decimal("6200000.00"),
            "progress": Decimal("55.00"),
            "progress_date": date(2026, 8, 22),
        },
        {
            "key": "naivasha-water",
            "name": "Naivasha Community Water Main Extension (Demo)",
            "description": "Fictional demonstration extension of a local water main.",
            "legacy_project_type": "WATER",
            "category_code": "WATER_SANITATION",
            "subtype_code": "WATER_SUPPLY",
            "status": ProjectStatus.IN_PROGRESS,
            "ward": "maai-mahiu",
            "planned_start": date(2026, 4, 1),
            "planned_completion": date(2026, 11, 30),
            "actual_start": date(2026, 4, 8),
            "expected_completion": date(2026, 11, 30),
            "contractor": "Rift Valley Waterworks Ltd (fictional demo contractor)",
            "award": "DEMO-NKR-WATER-003",
            "allocated": Decimal("16000000.00"),
            "committed": Decimal("14000000.00"),
            "contracted": Decimal("15000000.00"),
            "spent": Decimal("12000000.00"),
            "reported": Decimal("11800000.00"),
            "progress": Decimal("70.00"),
            "progress_date": date(2026, 8, 26),
        },
        {
            "key": "kitui-classrooms",
            "name": "Kitui Day School Classroom Improvement (Demo)",
            "description": (
                "Fictional demonstration construction of two classroom blocks."
            ),
            "legacy_project_type": "EDUCATION",
            "category_code": "EDUCATION",
            "subtype_code": "CLASSROOMS",
            "status": ProjectStatus.PLANNED,
            "ward": "town",
            "planned_start": date(2026, 10, 1),
            "planned_completion": date(2027, 6, 30),
            "actual_start": None,
            "expected_completion": date(2027, 6, 30),
            "contractor": (
                "Eastern Counties Education Build Ltd (fictional demo contractor)"
            ),
            "award": "DEMO-KTI-EDU-004",
            "allocated": Decimal("9000000.00"),
            "committed": Decimal("4000000.00"),
            "contracted": Decimal("7800000.00"),
            "spent": Decimal("2500000.00"),
            "reported": Decimal("2500000.00"),
            "progress": Decimal("25.00"),
            "progress_date": date(2026, 8, 20),
        },
        {
            "key": "kangemi-market",
            "name": "Kangemi Market Access Improvement (Demo)",
            "description": (
                "Fictional demonstration improvement of market access paths and "
                "drainage."
            ),
            "legacy_project_type": "ROAD",
            "category_code": "ROADS_TRANSPORT",
            "subtype_code": "ROAD_REHABILITATION",
            "status": ProjectStatus.PLANNED,
            "ward": "kangemi",
            "planned_start": date(2026, 10, 15),
            "planned_completion": date(2027, 5, 31),
            "actual_start": None,
            "expected_completion": date(2027, 5, 31),
            "contractor": "Nairobi Community Works Ltd (fictional demo contractor)",
            "award": "DEMO-NRB-MARKET-005",
            "allocated": Decimal("11000000.00"),
            "committed": Decimal("5000000.00"),
            "contracted": Decimal("9500000.00"),
            "spent": Decimal("1000000.00"),
            "reported": Decimal("1000000.00"),
            "progress": Decimal("10.00"),
            "progress_date": date(2026, 8, 28),
        },
        {
            "key": "makueni-irrigation",
            "name": "Makueni Smallholder Irrigation Scheme (Demo)",
            "description": (
                "Fictional demonstration expansion of irrigation channels "
                "for smallholder farmers."
            ),
            "legacy_project_type": "IRRIGATION",
            "category_code": "AGRICULTURE",
            "subtype_code": "IRRIGATION",
            "status": ProjectStatus.IN_PROGRESS,
            "ward": "kibwezi",
            "planned_start": date(2026, 3, 1),
            "planned_completion": date(2027, 2, 28),
            "actual_start": date(2026, 3, 15),
            "expected_completion": date(2027, 3, 15),
            "contractor": "Eastern Farms Infrastructure Ltd (fictional demo contractor)",
            "award": "DEMO-MKN-AGRI-006",
            "allocated": Decimal("18000000.00"),
            "committed": Decimal("15000000.00"),
            "contracted": Decimal("16500000.00"),
            "spent": Decimal("9000000.00"),
            "reported": Decimal("9500000.00"),
            "progress": Decimal("60.00"),
            "progress_date": date(2026, 8, 24),
        },
        {
            "key": "garissa-clinic",
            "name": "Garissa County Referral Medical Equipment (Demo)",
            "description": (
                "Fictional demonstration procurement of diagnostic and "
                "monitoring equipment for a county referral facility."
            ),
            "legacy_project_type": "MEDICAL_EQUIPMENT",
            "category_code": "HEALTH",
            "subtype_code": "MEDICAL_EQUIPMENT",
            "status": ProjectStatus.PLANNED,
            "ward": "balambala",
            "planned_start": date(2026, 11, 1),
            "planned_completion": date(2027, 4, 30),
            "actual_start": None,
            "expected_completion": date(2027, 4, 30),
            "contractor": "Northern Health Supply Co. (fictional demo contractor)",
            "award": "DEMO-GRS-HEALTH-007",
            "allocated": Decimal("8500000.00"),
            "committed": Decimal("3000000.00"),
            "contracted": Decimal("6000000.00"),
            "spent": Decimal("500000.00"),
            "reported": Decimal("500000.00"),
            "progress": Decimal("5.00"),
            "progress_date": date(2026, 8, 20),
        },
        {
            "key": "eldoret-lighting",
            "name": "Eldoret Township Street Lighting Upgrade (Demo)",
            "description": (
                "Fictional demonstration installation of energy-efficient "
                "street lighting across the township."
            ),
            "legacy_project_type": "STREET_LIGHTING",
            "category_code": "ENERGY_ELECTRIFICATION",
            "subtype_code": "STREET_LIGHTING",
            "status": ProjectStatus.IN_PROGRESS,
            "ward": "kapsoya",
            "planned_start": date(2026, 5, 1),
            "planned_completion": date(2026, 12, 31),
            "actual_start": date(2026, 5, 20),
            "expected_completion": date(2027, 1, 31),
            "contractor": "Rift Valley Power Works Ltd (fictional demo contractor)",
            "award": "DEMO-ELD-ENERGY-008",
            "allocated": Decimal("14000000.00"),
            "committed": Decimal("12000000.00"),
            "contracted": Decimal("13000000.00"),
            "spent": Decimal("7000000.00"),
            "reported": Decimal("7200000.00"),
            "progress": Decimal("52.00"),
            "progress_date": date(2026, 8, 23),
        },
        {
            "key": "isiolo-trees",
            "name": "Isiolo Rangeland Reforestation Programme (Demo)",
            "description": (
                "Fictional demonstration tree-planting across degraded "
                "rangeland and grazing areas."
            ),
            "legacy_project_type": "REFORESTATION",
            "category_code": "ENVIRONMENT_CLIMATE",
            "subtype_code": "REFORESTATION",
            "status": ProjectStatus.PLANNED,
            "ward": "merti",
            "planned_start": date(2026, 9, 1),
            "planned_completion": date(2027, 8, 31),
            "actual_start": None,
            "expected_completion": date(2027, 8, 31),
            "contractor": "Northern Conservation Build Ltd (fictional demo contractor)",
            "award": "DEMO-ISL-ENV-009",
            "allocated": Decimal("7500000.00"),
            "committed": Decimal("2000000.00"),
            "contracted": Decimal("5500000.00"),
            "spent": Decimal("300000.00"),
            "reported": Decimal("300000.00"),
            "progress": Decimal("4.00"),
            "progress_date": date(2026, 8, 18),
        },
        {
            "key": "kajiado-housing",
            "name": "Kajiado Affordable Housing Phase 1 (Demo)",
            "description": (
                "Fictional demonstration construction of affordable housing "
                "units for low-income families."
            ),
            "legacy_project_type": "AFFORDABLE_HOUSING",
            "category_code": "HOUSING_URBAN_DEVELOPMENT",
            "subtype_code": "AFFORDABLE_HOUSING",
            "status": ProjectStatus.IN_PROGRESS,
            "ward": "oonkot",
            "planned_start": date(2026, 6, 1),
            "planned_completion": date(2027, 5, 31),
            "actual_start": date(2026, 6, 15),
            "expected_completion": date(2027, 6, 15),
            "contractor": "Savanna Housing Developers Ltd (fictional demo contractor)",
            "award": "DEMO-KJD-HOUSING-010",
            "allocated": Decimal("25000000.00"),
            "committed": Decimal("20000000.00"),
            "contracted": Decimal("22000000.00"),
            "spent": Decimal("11000000.00"),
            "reported": Decimal("10500000.00"),
            "progress": Decimal("44.00"),
            "progress_date": date(2026, 8, 27),
        },
    ]

    category_ids, subtype_ids = await _taxonomy_ids(session, projects)
    project_records: list[SQLModel] = []
    contractor_records: list[SQLModel] = []
    source_records: list[SQLModel] = []
    for item in projects:
        project_key = str(item["key"])
        project_records.append(
            Project(
                id=_id(f"project:{project_key}"),
                demo_key=project_key,
                name=str(item["name"]),
                description=str(item["description"]),
                project_type=item["legacy_project_type"],
                category_id=category_ids[item["category_code"]],
                subtype_id=(
                    subtype_ids[item["subtype_code"]]
                    if item["subtype_code"] is not None
                    else None
                ),
                status=item["status"].value,
                ward_id=_id(f"ward:{item['ward']}"),
                planned_start_date=item["planned_start"],
                planned_completion_date=item["planned_completion"],
                actual_start_date=item["actual_start"],
                expected_completion_date=item["expected_completion"],
                last_verified_at=None,
                created_at=_DEMO_TIMESTAMP,
                updated_at=_DEMO_TIMESTAMP,
            )
        )
        contractor_records.append(
            Contractor(
                id=_id(f"contractor:{project_key}"),
                demo_key=project_key,
                legal_name=str(item["contractor"]),
                created_at=_DEMO_TIMESTAMP,
            )
        )
        source_records.append(
            Source(
                id=_id(f"source:{project_key}"),
                demo_key=f"{project_key}-evidence-sheet",
                publisher="Citizen Intelligence Layer demonstration dataset",
                title=f"{item['name']} evidence sheet (fictional demo data)",
                source_type=SourceType.DEMONSTRATION_RECORD.value,
                url=f"https://example.org/citizen-intelligence-demo/{project_key}.json",
                publication_date=date(2026, 9, 1),
                retrieved_at=_DEMO_TIMESTAMP,
                storage_reference=f"demo://project-explorer/{project_key}.json",
                created_at=_DEMO_TIMESTAMP,
            )
        )
    created += await _stage(session, project_records)
    created += await _stage(session, contractor_records)
    created += await _stage(session, source_records)

    source_record_records: list[SQLModel] = []
    claim_records: list[SQLModel] = []
    claim_source_records: list[SQLModel] = []
    financial_records: list[SQLModel] = []
    contract_records: list[SQLModel] = []
    progress_records: list[SQLModel] = []
    verification_records: list[SQLModel] = []
    for item in projects:
        project_key = str(item["key"])
        project_id = _id(f"project:{project_key}")
        source_id = _id(f"source:{project_key}")
        facts: list[tuple[str, ClaimKind, str, Decimal | None, str | None]] = [
            (
                "allocated_amount",
                ClaimKind.FINANCIAL,
                f"KES {item['allocated']:,.2f} allocated for {_FINANCIAL_PERIOD}",
                item["allocated"],
                "KES",
            ),
            (
                "committed_amount",
                ClaimKind.FINANCIAL,
                f"KES {item['committed']:,.2f} committed for {_FINANCIAL_PERIOD}",
                item["committed"],
                "KES",
            ),
            (
                "contracted_amount",
                ClaimKind.FINANCIAL,
                f"KES {item['contracted']:,.2f} contracted for {_FINANCIAL_PERIOD}",
                item["contracted"],
                "KES",
            ),
            (
                "spent_amount",
                ClaimKind.FINANCIAL,
                f"KES {item['spent']:,.2f} recorded as spent for {_FINANCIAL_PERIOD}",
                item["spent"],
                "KES",
            ),
            (
                "reported_amount",
                ClaimKind.FINANCIAL,
                f"KES {item['reported']:,.2f} reported for {_FINANCIAL_PERIOD}",
                item["reported"],
                "KES",
            ),
            (
                "contractor",
                ClaimKind.CONTRACTOR,
                str(item["contractor"]),
                None,
                None,
            ),
            (
                "reported_progress_percentage",
                ClaimKind.PROGRESS,
                (
                    f"{item['progress']:.2f}% reported progress as of "
                    f"{item['progress_date']}"
                ),
                item["progress"],
                None,
            ),
            (
                "verification_status",
                ClaimKind.VERIFICATION,
                "Fictional demonstration data; not independently verified.",
                None,
                None,
            ),
        ]
        for field_name, claim_kind, value_text, numeric_value, currency in facts:
            record_id = _id(f"source-record:{project_key}:{field_name}")
            claim_id = _id(f"claim:{project_key}:{field_name}")
            source_record_records.append(
                SourceRecord(
                    id=record_id,
                    source_id=source_id,
                    record_key=field_name,
                    content_summary=value_text,
                    created_at=_DEMO_TIMESTAMP,
                )
            )
            claim_records.append(
                Claim(
                    id=claim_id,
                    project_id=project_id,
                    claim_kind=claim_kind.value,
                    field_name=field_name,
                    value_text=value_text,
                    numeric_value=numeric_value,
                    currency=currency,
                    financial_period=(
                        _FINANCIAL_PERIOD if claim_kind is ClaimKind.FINANCIAL else None
                    ),
                    created_at=_DEMO_TIMESTAMP,
                )
            )
            claim_source_records.append(
                ClaimSource(
                    claim_id=claim_id,
                    source_record_id=record_id,
                    created_at=_DEMO_TIMESTAMP,
                )
            )

        for kind, amount in (
            (FinancialKind.ALLOCATED, item["allocated"]),
            (FinancialKind.COMMITTED, item["committed"]),
            (FinancialKind.CONTRACTED, item["contracted"]),
            (FinancialKind.SPENT, item["spent"]),
            (FinancialKind.REPORTED, item["reported"]),
        ):
            financial_records.append(
                FinancialRecord(
                    id=_id(f"financial:{project_key}:{kind.value}"),
                    project_id=project_id,
                    kind=kind.value,
                    amount=amount,
                    currency="KES",
                    financial_period=_FINANCIAL_PERIOD,
                    claim_id=_id(f"claim:{project_key}:{kind.value.lower()}_amount"),
                    created_at=_DEMO_TIMESTAMP,
                )
            )
        contract_records.append(
            ProjectContract(
                id=_id(f"contract:{project_key}"),
                project_id=project_id,
                contractor_id=_id(f"contractor:{project_key}"),
                award_reference=str(item["award"]),
                contract_status="ACTIVE",
                contract_start_date=item["actual_start"] or item["planned_start"],
                contract_end_date=item["expected_completion"],
                claim_id=_id(f"claim:{project_key}:contractor"),
                created_at=_DEMO_TIMESTAMP,
            )
        )
        progress_records.append(
            ProjectProgress(
                id=_id(f"progress:{project_key}"),
                project_id=project_id,
                percentage=item["progress"],
                reported_at=item["progress_date"],
                claim_id=_id(f"claim:{project_key}:reported_progress_percentage"),
                created_at=_DEMO_TIMESTAMP,
            )
        )
        verification_records.append(
            ProjectVerification(
                id=_id(f"verification:{project_key}"),
                project_id=project_id,
                status=VerificationStatus.UNVERIFIED.value,
                verification_date=None,
                recorded_at=_DEMO_TIMESTAMP,
                notes=(
                    "This is fictional demonstration data and has not been "
                    "independently verified."
                ),
                source_record_id=_id(
                    f"source-record:{project_key}:verification_status"
                ),
            )
        )
    created += await _stage(session, source_record_records)
    created += await _stage(session, claim_records)
    created += await _stage(session, claim_source_records)
    created += await _stage(session, financial_records)
    created += await _stage(session, contract_records)
    created += await _stage(session, progress_records)
    created += await _stage(session, verification_records)
    await session.commit()
    logger.info("Seeded project explorer demonstration records count=%s", created)
    return created


async def main() -> None:
    """Run the seed use case and close pooled resources cleanly."""
    try:
        async with async_session_maker() as session:
            created = await seed_demo_data(session)
        print(f"Demo seed complete; created {created} records.")
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
