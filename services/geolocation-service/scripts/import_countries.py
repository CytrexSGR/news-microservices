"""Import Natural Earth country data into PostgreSQL (JSONB version)."""
import asyncio
import json
import sys
from pathlib import Path

import asyncpg

# Region mapping based on UN M49 standard
REGION_MAP = {
    # Europe - Western
    "DE": ("Europe", "Western Europe"),
    "FR": ("Europe", "Western Europe"),
    "AT": ("Europe", "Western Europe"),
    "CH": ("Europe", "Western Europe"),
    "BE": ("Europe", "Western Europe"),
    "NL": ("Europe", "Western Europe"),
    "LU": ("Europe", "Western Europe"),
    "MC": ("Europe", "Western Europe"),
    "LI": ("Europe", "Western Europe"),
    # Europe - Northern
    "GB": ("Europe", "Northern Europe"),
    "IE": ("Europe", "Northern Europe"),
    "SE": ("Europe", "Northern Europe"),
    "NO": ("Europe", "Northern Europe"),
    "DK": ("Europe", "Northern Europe"),
    "FI": ("Europe", "Northern Europe"),
    "IS": ("Europe", "Northern Europe"),
    "EE": ("Europe", "Northern Europe"),
    "LV": ("Europe", "Northern Europe"),
    "LT": ("Europe", "Northern Europe"),
    # Europe - Southern
    "IT": ("Europe", "Southern Europe"),
    "ES": ("Europe", "Southern Europe"),
    "PT": ("Europe", "Southern Europe"),
    "GR": ("Europe", "Southern Europe"),
    "MT": ("Europe", "Southern Europe"),
    "CY": ("Europe", "Southern Europe"),
    "HR": ("Europe", "Southern Europe"),
    "SI": ("Europe", "Southern Europe"),
    "BA": ("Europe", "Southern Europe"),
    "RS": ("Europe", "Southern Europe"),
    "ME": ("Europe", "Southern Europe"),
    "MK": ("Europe", "Southern Europe"),
    "AL": ("Europe", "Southern Europe"),
    "XK": ("Europe", "Southern Europe"),
    "AD": ("Europe", "Southern Europe"),
    "SM": ("Europe", "Southern Europe"),
    "VA": ("Europe", "Southern Europe"),
    # Europe - Eastern
    "RU": ("Europe", "Eastern Europe"),
    "UA": ("Europe", "Eastern Europe"),
    "BY": ("Europe", "Eastern Europe"),
    "MD": ("Europe", "Eastern Europe"),
    "PL": ("Europe", "Eastern Europe"),
    "CZ": ("Europe", "Eastern Europe"),
    "SK": ("Europe", "Eastern Europe"),
    "HU": ("Europe", "Eastern Europe"),
    "RO": ("Europe", "Eastern Europe"),
    "BG": ("Europe", "Eastern Europe"),
    # Asia - Eastern
    "CN": ("Asia", "Eastern Asia"),
    "JP": ("Asia", "Eastern Asia"),
    "KR": ("Asia", "Eastern Asia"),
    "KP": ("Asia", "Eastern Asia"),
    "MN": ("Asia", "Eastern Asia"),
    "TW": ("Asia", "Eastern Asia"),
    "HK": ("Asia", "Eastern Asia"),
    "MO": ("Asia", "Eastern Asia"),
    # Asia - Southern
    "IN": ("Asia", "Southern Asia"),
    "PK": ("Asia", "Southern Asia"),
    "BD": ("Asia", "Southern Asia"),
    "AF": ("Asia", "Southern Asia"),
    "IR": ("Asia", "Southern Asia"),
    "NP": ("Asia", "Southern Asia"),
    "LK": ("Asia", "Southern Asia"),
    "BT": ("Asia", "Southern Asia"),
    "MV": ("Asia", "Southern Asia"),
    # Asia - Western
    "IL": ("Asia", "Western Asia"),
    "SA": ("Asia", "Western Asia"),
    "AE": ("Asia", "Western Asia"),
    "TR": ("Asia", "Western Asia"),
    "IQ": ("Asia", "Western Asia"),
    "SY": ("Asia", "Western Asia"),
    "JO": ("Asia", "Western Asia"),
    "LB": ("Asia", "Western Asia"),
    "KW": ("Asia", "Western Asia"),
    "QA": ("Asia", "Western Asia"),
    "YE": ("Asia", "Western Asia"),
    "OM": ("Asia", "Western Asia"),
    "BH": ("Asia", "Western Asia"),
    "PS": ("Asia", "Western Asia"),
    "GE": ("Asia", "Western Asia"),
    "AM": ("Asia", "Western Asia"),
    "AZ": ("Asia", "Western Asia"),
    # Asia - South-Eastern
    "VN": ("Asia", "South-Eastern Asia"),
    "TH": ("Asia", "South-Eastern Asia"),
    "MY": ("Asia", "South-Eastern Asia"),
    "ID": ("Asia", "South-Eastern Asia"),
    "PH": ("Asia", "South-Eastern Asia"),
    "SG": ("Asia", "South-Eastern Asia"),
    "MM": ("Asia", "South-Eastern Asia"),
    "KH": ("Asia", "South-Eastern Asia"),
    "LA": ("Asia", "South-Eastern Asia"),
    "BN": ("Asia", "South-Eastern Asia"),
    "TL": ("Asia", "South-Eastern Asia"),
    # Asia - Central
    "KZ": ("Asia", "Central Asia"),
    "UZ": ("Asia", "Central Asia"),
    "TM": ("Asia", "Central Asia"),
    "TJ": ("Asia", "Central Asia"),
    "KG": ("Asia", "Central Asia"),
    # Americas - Northern
    "US": ("Americas", "Northern America"),
    "CA": ("Americas", "Northern America"),
    # Americas - Central
    "MX": ("Americas", "Central America"),
    "GT": ("Americas", "Central America"),
    "BZ": ("Americas", "Central America"),
    "HN": ("Americas", "Central America"),
    "SV": ("Americas", "Central America"),
    "NI": ("Americas", "Central America"),
    "CR": ("Americas", "Central America"),
    "PA": ("Americas", "Central America"),
    # Americas - Caribbean
    "CU": ("Americas", "Caribbean"),
    "DO": ("Americas", "Caribbean"),
    "HT": ("Americas", "Caribbean"),
    "JM": ("Americas", "Caribbean"),
    "PR": ("Americas", "Caribbean"),
    "TT": ("Americas", "Caribbean"),
    "BS": ("Americas", "Caribbean"),
    "BB": ("Americas", "Caribbean"),
    # Americas - South
    "BR": ("Americas", "South America"),
    "AR": ("Americas", "South America"),
    "CL": ("Americas", "South America"),
    "CO": ("Americas", "South America"),
    "PE": ("Americas", "South America"),
    "VE": ("Americas", "South America"),
    "EC": ("Americas", "South America"),
    "BO": ("Americas", "South America"),
    "PY": ("Americas", "South America"),
    "UY": ("Americas", "South America"),
    "GY": ("Americas", "South America"),
    "SR": ("Americas", "South America"),
    "GF": ("Americas", "South America"),
    # Africa - Northern
    "EG": ("Africa", "Northern Africa"),
    "LY": ("Africa", "Northern Africa"),
    "TN": ("Africa", "Northern Africa"),
    "DZ": ("Africa", "Northern Africa"),
    "MA": ("Africa", "Northern Africa"),
    "SD": ("Africa", "Northern Africa"),
    "SS": ("Africa", "Northern Africa"),
    # Africa - Western
    "NG": ("Africa", "Western Africa"),
    "GH": ("Africa", "Western Africa"),
    "CI": ("Africa", "Western Africa"),
    "SN": ("Africa", "Western Africa"),
    "ML": ("Africa", "Western Africa"),
    "BF": ("Africa", "Western Africa"),
    "NE": ("Africa", "Western Africa"),
    "MR": ("Africa", "Western Africa"),
    "GN": ("Africa", "Western Africa"),
    "BJ": ("Africa", "Western Africa"),
    "TG": ("Africa", "Western Africa"),
    "SL": ("Africa", "Western Africa"),
    "LR": ("Africa", "Western Africa"),
    "GM": ("Africa", "Western Africa"),
    "GW": ("Africa", "Western Africa"),
    "CV": ("Africa", "Western Africa"),
    # Africa - Eastern
    "KE": ("Africa", "Eastern Africa"),
    "ET": ("Africa", "Eastern Africa"),
    "TZ": ("Africa", "Eastern Africa"),
    "UG": ("Africa", "Eastern Africa"),
    "RW": ("Africa", "Eastern Africa"),
    "BI": ("Africa", "Eastern Africa"),
    "SO": ("Africa", "Eastern Africa"),
    "ER": ("Africa", "Eastern Africa"),
    "DJ": ("Africa", "Eastern Africa"),
    "MG": ("Africa", "Eastern Africa"),
    "MU": ("Africa", "Eastern Africa"),
    "SC": ("Africa", "Eastern Africa"),
    "KM": ("Africa", "Eastern Africa"),
    "MW": ("Africa", "Eastern Africa"),
    "MZ": ("Africa", "Eastern Africa"),
    "ZM": ("Africa", "Eastern Africa"),
    "ZW": ("Africa", "Eastern Africa"),
    # Africa - Central
    "CD": ("Africa", "Central Africa"),
    "CG": ("Africa", "Central Africa"),
    "CF": ("Africa", "Central Africa"),
    "CM": ("Africa", "Central Africa"),
    "GA": ("Africa", "Central Africa"),
    "GQ": ("Africa", "Central Africa"),
    "TD": ("Africa", "Central Africa"),
    "AO": ("Africa", "Central Africa"),
    "ST": ("Africa", "Central Africa"),
    # Africa - Southern
    "ZA": ("Africa", "Southern Africa"),
    "NA": ("Africa", "Southern Africa"),
    "BW": ("Africa", "Southern Africa"),
    "SZ": ("Africa", "Southern Africa"),
    "LS": ("Africa", "Southern Africa"),
    # Oceania - Australia and New Zealand
    "AU": ("Oceania", "Australia and New Zealand"),
    "NZ": ("Oceania", "Australia and New Zealand"),
    # Oceania - Melanesia
    "PG": ("Oceania", "Melanesia"),
    "FJ": ("Oceania", "Melanesia"),
    "SB": ("Oceania", "Melanesia"),
    "VU": ("Oceania", "Melanesia"),
    "NC": ("Oceania", "Melanesia"),
    # Oceania - Micronesia
    "FM": ("Oceania", "Micronesia"),
    "PW": ("Oceania", "Micronesia"),
    "MH": ("Oceania", "Micronesia"),
    "KI": ("Oceania", "Micronesia"),
    "NR": ("Oceania", "Micronesia"),
    # Oceania - Polynesia
    "WS": ("Oceania", "Polynesia"),
    "TO": ("Oceania", "Polynesia"),
    "TV": ("Oceania", "Polynesia"),
    "PF": ("Oceania", "Polynesia"),
}


def calculate_centroid(geometry: dict) -> tuple[float, float]:
    """Calculate approximate centroid from GeoJSON geometry."""
    coords = []

    def extract_coords(obj):
        if isinstance(obj, list):
            if len(obj) >= 2 and isinstance(obj[0], (int, float)):
                coords.append((obj[0], obj[1]))
            else:
                for item in obj:
                    extract_coords(item)

    extract_coords(geometry.get("coordinates", []))

    if not coords:
        return 0.0, 0.0

    lon = sum(c[0] for c in coords) / len(coords)
    lat = sum(c[1] for c in coords) / len(coords)
    return lon, lat


async def import_countries(geojson_path: str, db_url: str):
    """Import countries from GeoJSON file (JSONB version)."""
    print(f"Connecting to database...")
    conn = await asyncpg.connect(db_url)

    print(f"Loading GeoJSON from: {geojson_path}")
    with open(geojson_path) as f:
        data = json.load(f)

    count = 0
    skipped = 0

    for feature in data["features"]:
        props = feature["properties"]
        # Try different property names for ISO code
        iso_code = (
            props.get("ISO_A2")
            or props.get("iso_a2")
            or props.get("ISO_A2_EH")
            or props.get("ADM0_A3", "")[:2]
            or ""
        )

        if not iso_code or iso_code == "-99" or iso_code == "-1" or len(iso_code) != 2:
            name = props.get("ADMIN", props.get("name", "Unknown"))
            print(f"  Skipping: {name} (invalid ISO code: {iso_code})")
            skipped += 1
            continue

        name = props.get("ADMIN", props.get("name", ""))
        geometry = feature["geometry"]
        boundary_json = json.dumps(geometry)
        region, subregion = REGION_MAP.get(iso_code, (None, None))

        # Calculate centroid
        centroid_lon, centroid_lat = calculate_centroid(geometry)

        try:
            await conn.execute("""
                INSERT INTO countries (iso_code, name, region, subregion, boundary, centroid_lon, centroid_lat)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
                ON CONFLICT (iso_code) DO UPDATE SET
                    name = EXCLUDED.name,
                    region = COALESCE(EXCLUDED.region, countries.region),
                    subregion = COALESCE(EXCLUDED.subregion, countries.subregion),
                    boundary = EXCLUDED.boundary,
                    centroid_lon = EXCLUDED.centroid_lon,
                    centroid_lat = EXCLUDED.centroid_lat
            """, iso_code, name, region, subregion, boundary_json, centroid_lon, centroid_lat)
            count += 1
            print(f"  Imported: {iso_code} - {name} ({region or 'No region'})")
        except Exception as e:
            print(f"  Error importing {iso_code} - {name}: {e}")
            skipped += 1

    await conn.close()
    print(f"\n{'=' * 50}")
    print(f"Import complete!")
    print(f"  Imported: {count} countries")
    print(f"  Skipped: {skipped} entries")


if __name__ == "__main__":
    db_url = sys.argv[1] if len(sys.argv) > 1 else \
        "postgresql://news_user:+t1koDEJO+ruZ3QnYlkVeU2u6Z+zCJtL6wFW+wfN5Yk=@localhost:5432/news_mcp"
    geojson_path = sys.argv[2] if len(sys.argv) > 2 else \
        str(Path(__file__).parent.parent / "data" / "countries.geojson")

    print("=" * 50)
    print("Natural Earth Country Import (JSONB)")
    print("=" * 50)
    asyncio.run(import_countries(geojson_path, db_url))
