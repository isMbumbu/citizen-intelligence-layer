"""Initial database reference data for the public-project taxonomy.

The database is authoritative after its migration runs. These definitions only
bootstrap the initial, deliberately compact Kenyan public-sector vocabulary.
"""

from dataclasses import dataclass
from uuid import UUID, uuid5

PROJECT_TAXONOMY_NAMESPACE = UUID("4beed722-0a73-4974-aa28-0486f3955b2e")


@dataclass(frozen=True)
class ProjectCategoryDefinition:
    """One top-level project category used to initialize reference data."""

    code: str
    name: str
    description: str


@dataclass(frozen=True)
class ProjectSubtypeDefinition:
    """One category-specific project subtype used to initialize reference data."""

    category_code: str
    code: str
    name: str
    description: str


PROJECT_CATEGORY_DEFINITIONS = (
    ProjectCategoryDefinition(
        "ROADS_TRANSPORT",
        "Roads and transport",
        "Roads, bridges, public transport, and related access infrastructure.",
    ),
    ProjectCategoryDefinition(
        "WATER_SANITATION",
        "Water and sanitation",
        "Water supply, sanitation, sewerage, and hygiene infrastructure.",
    ),
    ProjectCategoryDefinition(
        "HEALTH",
        "Health",
        "Health facilities, equipment, and public health infrastructure.",
    ),
    ProjectCategoryDefinition(
        "EDUCATION",
        "Education",
        "Early learning, classrooms, and education facilities.",
    ),
    ProjectCategoryDefinition(
        "AGRICULTURE",
        "Agriculture",
        "Irrigation, agricultural markets, and farm-support infrastructure.",
    ),
    ProjectCategoryDefinition(
        "HOUSING_URBAN_DEVELOPMENT",
        "Housing and urban development",
        "Housing, urban renewal, and planned settlement infrastructure.",
    ),
    ProjectCategoryDefinition(
        "ENERGY_ELECTRIFICATION",
        "Energy and electrification",
        "Electricity access, lighting, and energy-support infrastructure.",
    ),
    ProjectCategoryDefinition(
        "ICT_DIGITAL_INFRASTRUCTURE",
        "ICT and digital infrastructure",
        "Connectivity, digital-service facilities, and ICT infrastructure.",
    ),
    ProjectCategoryDefinition(
        "ENVIRONMENT_CLIMATE",
        "Environment and climate",
        "Environmental restoration and climate-resilience works.",
    ),
    ProjectCategoryDefinition(
        "MARKETS_TRADE",
        "Markets and trade",
        "Markets and infrastructure that supports local trade.",
    ),
    ProjectCategoryDefinition(
        "PUBLIC_ADMINISTRATION",
        "Public administration",
        "Civic offices and government-service facilities.",
    ),
    ProjectCategoryDefinition(
        "SECURITY_EMERGENCY_SERVICES",
        "Security and emergency services",
        "Security, fire, rescue, and emergency-response facilities.",
    ),
    ProjectCategoryDefinition(
        "SPORTS_CULTURE_RECREATION",
        "Sports, culture and recreation",
        "Sports facilities, cultural spaces, and public recreation works.",
    ),
    ProjectCategoryDefinition(
        "SOCIAL_COMMUNITY_DEVELOPMENT",
        "Social and community development",
        "Community halls and social-support facilities.",
    ),
    ProjectCategoryDefinition(
        "DRAINAGE_FLOOD_MANAGEMENT",
        "Drainage and flood management",
        "Storm-water drainage, flood control, and related protection works.",
    ),
    ProjectCategoryDefinition(
        "WASTE_MANAGEMENT",
        "Waste management",
        "Waste collection, processing, and disposal infrastructure.",
    ),
    ProjectCategoryDefinition(
        "PUBLIC_FACILITIES",
        "Public facilities",
        "Shared public amenities not represented by another category.",
    ),
    ProjectCategoryDefinition(
        "OTHER",
        "Other",
        "A transparent fallback for projects awaiting a more specific category.",
    ),
)

PROJECT_SUBTYPE_DEFINITIONS = (
    ProjectSubtypeDefinition(
        "ROADS_TRANSPORT",
        "ROAD_CONSTRUCTION",
        "Road construction",
        "Construction of a new public road or access route.",
    ),
    ProjectSubtypeDefinition(
        "ROADS_TRANSPORT",
        "ROAD_REHABILITATION",
        "Road rehabilitation",
        "Rehabilitation, resurfacing, or improvement of an existing road.",
    ),
    ProjectSubtypeDefinition(
        "WATER_SANITATION",
        "WATER_SUPPLY",
        "Water supply",
        "Water mains, boreholes, distribution, and supply works.",
    ),
    ProjectSubtypeDefinition(
        "WATER_SANITATION",
        "SANITATION_SEWERAGE",
        "Sanitation and sewerage",
        "Sewerage, sanitation, and hygiene infrastructure.",
    ),
    ProjectSubtypeDefinition(
        "HEALTH",
        "HEALTH_FACILITY",
        "Health facility",
        "Construction or improvement of a clinic, dispensary, or hospital.",
    ),
    ProjectSubtypeDefinition(
        "HEALTH",
        "MEDICAL_EQUIPMENT",
        "Medical equipment",
        "Procurement or installation of equipment for public health facilities.",
    ),
    ProjectSubtypeDefinition(
        "EDUCATION",
        "CLASSROOMS",
        "Classrooms",
        "Classroom construction, rehabilitation, or expansion.",
    ),
    ProjectSubtypeDefinition(
        "EDUCATION",
        "EARLY_CHILDHOOD_FACILITIES",
        "Early childhood facilities",
        "Facilities supporting early childhood development and education.",
    ),
    ProjectSubtypeDefinition(
        "AGRICULTURE",
        "IRRIGATION",
        "Irrigation",
        "Irrigation and agricultural water-management works.",
    ),
    ProjectSubtypeDefinition(
        "AGRICULTURE",
        "AGRICULTURAL_MARKETS",
        "Agricultural markets",
        "Infrastructure supporting produce aggregation and agricultural trade.",
    ),
    ProjectSubtypeDefinition(
        "HOUSING_URBAN_DEVELOPMENT",
        "AFFORDABLE_HOUSING",
        "Affordable housing",
        "Public affordable-housing development.",
    ),
    ProjectSubtypeDefinition(
        "HOUSING_URBAN_DEVELOPMENT",
        "URBAN_RENEWAL",
        "Urban renewal",
        "Public urban-renewal and settlement-improvement works.",
    ),
    ProjectSubtypeDefinition(
        "ENERGY_ELECTRIFICATION",
        "RURAL_ELECTRIFICATION",
        "Rural electrification",
        "Electricity access and distribution expansion.",
    ),
    ProjectSubtypeDefinition(
        "ENERGY_ELECTRIFICATION",
        "STREET_LIGHTING",
        "Street lighting",
        "Public street, market, and community lighting infrastructure.",
    ),
    ProjectSubtypeDefinition(
        "ICT_DIGITAL_INFRASTRUCTURE",
        "BROADBAND_CONNECTIVITY",
        "Broadband connectivity",
        "Public broadband and connectivity infrastructure.",
    ),
    ProjectSubtypeDefinition(
        "ICT_DIGITAL_INFRASTRUCTURE",
        "DIGITAL_SERVICE_CENTRES",
        "Digital service centres",
        "Public digital-service and ICT access facilities.",
    ),
    ProjectSubtypeDefinition(
        "ENVIRONMENT_CLIMATE",
        "REFORESTATION",
        "Reforestation",
        "Tree-growing and public environmental-restoration works.",
    ),
    ProjectSubtypeDefinition(
        "ENVIRONMENT_CLIMATE",
        "CLIMATE_RESILIENCE",
        "Climate resilience",
        "Infrastructure designed to reduce climate-related risks.",
    ),
    ProjectSubtypeDefinition(
        "MARKETS_TRADE",
        "MARKET_CONSTRUCTION",
        "Market construction",
        "Construction or improvement of a public market.",
    ),
    ProjectSubtypeDefinition(
        "MARKETS_TRADE",
        "TRADE_INFRASTRUCTURE",
        "Trade infrastructure",
        "Public infrastructure supporting local commerce and trade.",
    ),
    ProjectSubtypeDefinition(
        "PUBLIC_ADMINISTRATION",
        "CIVIC_OFFICES",
        "Civic offices",
        "Public administrative offices and civic-service facilities.",
    ),
    ProjectSubtypeDefinition(
        "PUBLIC_ADMINISTRATION",
        "GOVERNMENT_SERVICE_CENTRES",
        "Government service centres",
        "One-stop and public government-service facilities.",
    ),
    ProjectSubtypeDefinition(
        "SECURITY_EMERGENCY_SERVICES",
        "SECURITY_FACILITIES",
        "Security facilities",
        "Public security infrastructure and facilities.",
    ),
    ProjectSubtypeDefinition(
        "SECURITY_EMERGENCY_SERVICES",
        "FIRE_EMERGENCY_RESPONSE",
        "Fire and emergency response",
        "Fire, rescue, and emergency-response infrastructure.",
    ),
    ProjectSubtypeDefinition(
        "SPORTS_CULTURE_RECREATION",
        "SPORTS_FACILITIES",
        "Sports facilities",
        "Public sports grounds, courts, and related facilities.",
    ),
    ProjectSubtypeDefinition(
        "SPORTS_CULTURE_RECREATION",
        "CULTURAL_RECREATION_FACILITIES",
        "Cultural and recreation facilities",
        "Cultural spaces, recreation facilities, and public amenities.",
    ),
    ProjectSubtypeDefinition(
        "SOCIAL_COMMUNITY_DEVELOPMENT",
        "COMMUNITY_HALLS",
        "Community halls",
        "Community meeting halls and shared social facilities.",
    ),
    ProjectSubtypeDefinition(
        "SOCIAL_COMMUNITY_DEVELOPMENT",
        "SOCIAL_SUPPORT_FACILITIES",
        "Social-support facilities",
        "Facilities supporting social and community-development programmes.",
    ),
    ProjectSubtypeDefinition(
        "DRAINAGE_FLOOD_MANAGEMENT",
        "STORMWATER_DRAINAGE",
        "Storm-water drainage",
        "Drains, culverts, and storm-water management infrastructure.",
    ),
    ProjectSubtypeDefinition(
        "DRAINAGE_FLOOD_MANAGEMENT",
        "FLOOD_CONTROL",
        "Flood control",
        "Flood-control and public protection works.",
    ),
    ProjectSubtypeDefinition(
        "WASTE_MANAGEMENT",
        "WASTE_COLLECTION",
        "Waste collection",
        "Waste-collection points, vehicles, and supporting infrastructure.",
    ),
    ProjectSubtypeDefinition(
        "WASTE_MANAGEMENT",
        "WASTE_PROCESSING",
        "Waste processing",
        "Waste sorting, treatment, recycling, and disposal infrastructure.",
    ),
    ProjectSubtypeDefinition(
        "PUBLIC_FACILITIES",
        "PUBLIC_TOILETS",
        "Public toilets",
        "Public sanitation amenities and toilet facilities.",
    ),
    ProjectSubtypeDefinition(
        "PUBLIC_FACILITIES",
        "PUBLIC_SPACES",
        "Public spaces",
        "Shared public spaces and community amenities.",
    ),
    ProjectSubtypeDefinition(
        "OTHER",
        "OTHER_PROJECT",
        "Other project",
        "A project that needs later classification into a specific subtype.",
    ),
)


def category_id(code: str) -> UUID:
    """Return the deterministic identifier used for one category bootstrap row."""
    return uuid5(PROJECT_TAXONOMY_NAMESPACE, f"category:{code}")


def subtype_id(code: str) -> UUID:
    """Return the deterministic identifier used for one subtype bootstrap row."""
    return uuid5(PROJECT_TAXONOMY_NAMESPACE, f"subtype:{code}")
