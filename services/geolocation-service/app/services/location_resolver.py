"""Resolve location names to ISO country codes."""
import logging
from typing import Optional
import httpx

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Cities/Regions → Country ISO codes (for locations not in countries table)
CITY_TO_COUNTRY = {
    # Major cities
    "berlin": "DE", "münchen": "DE", "munich": "DE", "frankfurt": "DE", "hamburg": "DE",
    "paris": "FR", "lyon": "FR", "marseille": "FR",
    "london": "GB", "manchester": "GB", "birmingham": "GB", "edinburgh": "GB", "glasgow": "GB",
    "new york": "US", "washington": "US", "los angeles": "US", "chicago": "US", "san francisco": "US",
    "moskau": "RU", "moscow": "RU", "st. petersburg": "RU", "st petersburg": "RU",
    "peking": "CN", "beijing": "CN", "shanghai": "CN", "hong kong": "HK",
    "tokio": "JP", "tokyo": "JP", "osaka": "JP",
    "kiew": "UA", "kyiv": "UA", "kiev": "UA", "odessa": "UA", "kharkiv": "UA",
    "tel aviv": "IL", "jerusalem": "IL", "haifa": "IL",
    "teheran": "IR", "tehran": "IR",
    "brüssel": "BE", "brussels": "BE",
    "amsterdam": "NL", "rotterdam": "NL",
    "madrid": "ES", "barcelona": "ES",
    "rome": "IT", "milan": "IT", "roma": "IT",
    "vienna": "AT", "wien": "AT",
    "zurich": "CH", "zürich": "CH", "geneva": "CH", "genf": "CH",
    "sydney": "AU", "melbourne": "AU", "canberra": "AU",
    "toronto": "CA", "vancouver": "CA", "ottawa": "CA", "montreal": "CA",
    "dubai": "AE", "abu dhabi": "AE",
    "riyadh": "SA", "riad": "SA", "mecca": "SA", "mekka": "SA",
    "istanbul": "TR", "ankara": "TR",
    "cairo": "EG", "kairo": "EG",
    "mumbai": "IN", "delhi": "IN", "new delhi": "IN", "bangalore": "IN",
    "singapore": "SG", "singapur": "SG",
    "seoul": "KR", "busan": "KR",
    "taipei": "TW",
    "bangkok": "TH",
    "jakarta": "ID",
    "kuala lumpur": "MY",
    "hanoi": "VN", "ho chi minh city": "VN", "saigon": "VN",
    # Regions/Territories
    "gaza": "PS", "west bank": "PS", "westjordanland": "PS", "gaza strip": "PS",
    "crimea": "UA", "krim": "UA", "donbas": "UA", "donbass": "UA",
    "taiwan": "TW", "formosa": "TW",
    "tibet": "CN",
    "xinjiang": "CN",
    "kashmir": "IN",
    "kurdistan": "IQ",
    "catalonia": "ES", "katalonien": "ES",
    "scotland": "GB", "schottland": "GB", "wales": "GB",
    "northern ireland": "GB", "nordirland": "GB",
    "england": "GB",
    "bavaria": "DE", "bayern": "DE",
    "normandy": "FR", "normandie": "FR",
    "siberia": "RU", "sibirien": "RU",
    # Common variations/aliases
    "usa": "US", "u.s.": "US", "u.s.a.": "US", "america": "US", "amerika": "US",
    "uk": "GB", "u.k.": "GB", "britain": "GB", "great britain": "GB", "großbritannien": "GB",
    "uae": "AE", "emirates": "AE",
    "russia": "RU", "russland": "RU", "russian federation": "RU",
    "china": "CN", "volksrepublik china": "CN", "prc": "CN",
    "south korea": "KR", "südkorea": "KR", "republic of korea": "KR",
    "north korea": "KP", "nordkorea": "KP", "dprk": "KP",
    "the netherlands": "NL", "holland": "NL", "niederlande": "NL",
    "czech republic": "CZ", "czechia": "CZ", "tschechien": "CZ",
    "ivory coast": "CI", "côte d'ivoire": "CI",
}


async def resolve_location_to_country(
    db: AsyncSession,
    location_name: str,
) -> Optional[str]:
    """
    Resolve a location name to ISO Alpha-2 country code.

    Strategy:
    1. Direct match in countries table (most LOCATION entities are country names)
    2. Lookup in CITY_TO_COUNTRY dict for cities/regions
    3. Fuzzy match in countries table
    """
    if not location_name:
        return None

    name = location_name.strip()
    name_lower = name.lower()

    # 1. Direct match in countries table (case-insensitive)
    result = await db.execute(
        text("SELECT iso_code FROM countries WHERE LOWER(name) = :name"),
        {"name": name_lower}
    )
    row = result.fetchone()
    if row:
        return row[0]

    # 2. Check city/region mapping
    if name_lower in CITY_TO_COUNTRY:
        return CITY_TO_COUNTRY[name_lower]

    # 3. Fuzzy match - try ILIKE with wildcards for partial matches
    result = await db.execute(
        text("SELECT iso_code FROM countries WHERE LOWER(name) LIKE :pattern LIMIT 1"),
        {"pattern": f"%{name_lower}%"}
    )
    row = result.fetchone()
    if row:
        logger.debug(f"Fuzzy matched '{name}' to {row[0]}")
        return row[0]

    logger.debug(f"Could not resolve location '{name}' to country")
    return None
