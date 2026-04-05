"""
ISO 3166-1 alpha-2 country code mappings.

Reference: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
"""
from typing import Dict, Optional

# ISO 3166-1 alpha-2 country codes
# Maps country name to 2-letter code
ISO_COUNTRY_CODES: Dict[str, str] = {
    # Current database countries
    "United States": "US",
    "Australia": "AU",
    "Japan": "JP",
    "North Korea": "KP",
    "China": "CN",
    "Russia": "RU",

    # Common variants
    "USA": "US",
    "United States of America": "US",
    "U.S.": "US",
    "U.S.A.": "US",
    "People's Republic of China": "CN",
    "PRC": "CN",
    "Russian Federation": "RU",
    "DPRK": "KP",
    "Democratic People's Republic of Korea": "KP",

    # Additional major countries (for future use)
    "Germany": "DE",
    "United Kingdom": "GB",
    "UK": "GB",
    "Great Britain": "GB",
    "France": "FR",
    "Italy": "IT",
    "Spain": "ES",
    "Canada": "CA",
    "Mexico": "MX",
    "Brazil": "BR",
    "Argentina": "AR",
    "India": "IN",
    "Pakistan": "PK",
    "South Korea": "KR",
    "Republic of Korea": "KR",
    "Taiwan": "TW",
    "Israel": "IL",
    "Iran": "IR",
    "Iraq": "IQ",
    "Syria": "SY",
    "Turkey": "TR",
    "Saudi Arabia": "SA",
    "United Arab Emirates": "AE",
    "UAE": "AE",
    "Egypt": "EG",
    "South Africa": "ZA",
    "Nigeria": "NG",
    "Kenya": "KE",
    "Ukraine": "UA",
    "Poland": "PL",
    "Sweden": "SE",
    "Norway": "NO",
    "Finland": "FI",
    "Denmark": "DK",
    "Netherlands": "NL",
    "Belgium": "BE",
    "Switzerland": "CH",
    "Austria": "AT",
    "Greece": "GR",
    "Portugal": "PT",
    "Czech Republic": "CZ",
    "Hungary": "HU",
    "Romania": "RO",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Serbia": "RS",
    "Bosnia and Herzegovina": "BA",
    "Albania": "AL",
    "North Macedonia": "MK",
    "Slovenia": "SI",
    "Slovakia": "SK",
    "Lithuania": "LT",
    "Latvia": "LV",
    "Estonia": "EE",
    "Belarus": "BY",
    "Moldova": "MD",
    "Georgia": "GE",
    "Armenia": "AM",
    "Azerbaijan": "AZ",
    "Kazakhstan": "KZ",
    "Uzbekistan": "UZ",
    "Turkmenistan": "TM",
    "Kyrgyzstan": "KG",
    "Tajikistan": "TJ",
    "Afghanistan": "AF",
    "Thailand": "TH",
    "Vietnam": "VN",
    "Philippines": "PH",
    "Indonesia": "ID",
    "Malaysia": "MY",
    "Singapore": "SG",
    "Myanmar": "MM",
    "Cambodia": "KH",
    "Laos": "LA",
    "Bangladesh": "BD",
    "Nepal": "NP",
    "Sri Lanka": "LK",
    "New Zealand": "NZ",
}


def get_iso_code(country_name: str) -> Optional[str]:
    """
    Get ISO 3166-1 alpha-2 code for a country name.

    Args:
        country_name: Country name (case-insensitive)

    Returns:
        2-letter ISO code or None if not found

    Examples:
        >>> get_iso_code("United States")
        'US'
        >>> get_iso_code("north korea")
        'KP'
        >>> get_iso_code("Unknown Country")
        None
    """
    if not country_name:
        return None

    # Try exact match (case-insensitive)
    code = ISO_COUNTRY_CODES.get(country_name)
    if code:
        return code

    # Try with normalized whitespace
    normalized = " ".join(country_name.split())
    code = ISO_COUNTRY_CODES.get(normalized)
    if code:
        return code

    # Try case-insensitive lookup
    lower_name = country_name.lower()
    for name, code in ISO_COUNTRY_CODES.items():
        if name.lower() == lower_name:
            return code

    return None


def validate_iso_code(code: str) -> bool:
    """
    Validate if a string is a valid ISO 3166-1 alpha-2 code.

    Args:
        code: 2-letter code to validate

    Returns:
        True if valid ISO code format, False otherwise

    Examples:
        >>> validate_iso_code("US")
        True
        >>> validate_iso_code("XX")
        False
        >>> validate_iso_code("USA")
        False
    """
    if not code or not isinstance(code, str):
        return False

    # Must be exactly 2 uppercase letters
    return len(code) == 2 and code.isupper() and code.isalpha()
