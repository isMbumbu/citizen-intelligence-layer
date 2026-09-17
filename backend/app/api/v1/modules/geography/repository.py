"""Asynchronous SQLModel queries for the project geography hierarchy."""

from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.vertical_slice import County, SubCounty, Ward


async def get_location_for_ward(
    session: AsyncSession,
    ward_id: UUID,
) -> tuple[County, SubCounty, Ward] | None:
    """Resolve the county, sub-county, and ward for a project ward ID."""
    ward = await session.get(Ward, ward_id)
    if ward is None:
        return None
    sub_county = await session.get(SubCounty, ward.sub_county_id)
    if sub_county is None:
        return None
    county = await session.get(County, sub_county.county_id)
    if county is None:
        return None
    return county, sub_county, ward
