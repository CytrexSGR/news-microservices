"""Enrich countries with German names."""
import asyncio
import sys

import asyncpg

GERMAN_NAMES = {
    # Europe - Western
    "DE": "Deutschland",
    "AT": "Österreich",
    "CH": "Schweiz",
    "FR": "Frankreich",
    "BE": "Belgien",
    "NL": "Niederlande",
    "LU": "Luxemburg",
    "MC": "Monaco",
    "LI": "Liechtenstein",
    # Europe - Northern
    "GB": "Vereinigtes Königreich",
    "IE": "Irland",
    "SE": "Schweden",
    "NO": "Norwegen",
    "DK": "Dänemark",
    "FI": "Finnland",
    "IS": "Island",
    "EE": "Estland",
    "LV": "Lettland",
    "LT": "Litauen",
    # Europe - Southern
    "IT": "Italien",
    "ES": "Spanien",
    "PT": "Portugal",
    "GR": "Griechenland",
    "MT": "Malta",
    "CY": "Zypern",
    "HR": "Kroatien",
    "SI": "Slowenien",
    "BA": "Bosnien und Herzegowina",
    "RS": "Serbien",
    "ME": "Montenegro",
    "MK": "Nordmazedonien",
    "AL": "Albanien",
    "XK": "Kosovo",
    "AD": "Andorra",
    "SM": "San Marino",
    "VA": "Vatikanstadt",
    # Europe - Eastern
    "RU": "Russland",
    "UA": "Ukraine",
    "BY": "Belarus",
    "MD": "Moldau",
    "PL": "Polen",
    "CZ": "Tschechien",
    "SK": "Slowakei",
    "HU": "Ungarn",
    "RO": "Rumänien",
    "BG": "Bulgarien",
    # Asia - Eastern
    "CN": "China",
    "JP": "Japan",
    "KR": "Südkorea",
    "KP": "Nordkorea",
    "MN": "Mongolei",
    "TW": "Taiwan",
    "HK": "Hongkong",
    "MO": "Macau",
    # Asia - Southern
    "IN": "Indien",
    "PK": "Pakistan",
    "BD": "Bangladesch",
    "AF": "Afghanistan",
    "IR": "Iran",
    "NP": "Nepal",
    "LK": "Sri Lanka",
    "BT": "Bhutan",
    "MV": "Malediven",
    # Asia - Western
    "IL": "Israel",
    "SA": "Saudi-Arabien",
    "AE": "Vereinigte Arabische Emirate",
    "TR": "Türkei",
    "IQ": "Irak",
    "SY": "Syrien",
    "JO": "Jordanien",
    "LB": "Libanon",
    "KW": "Kuwait",
    "QA": "Katar",
    "YE": "Jemen",
    "OM": "Oman",
    "BH": "Bahrain",
    "PS": "Palästina",
    "GE": "Georgien",
    "AM": "Armenien",
    "AZ": "Aserbaidschan",
    # Asia - South-Eastern
    "VN": "Vietnam",
    "TH": "Thailand",
    "MY": "Malaysia",
    "ID": "Indonesien",
    "PH": "Philippinen",
    "SG": "Singapur",
    "MM": "Myanmar",
    "KH": "Kambodscha",
    "LA": "Laos",
    "BN": "Brunei",
    "TL": "Osttimor",
    # Asia - Central
    "KZ": "Kasachstan",
    "UZ": "Usbekistan",
    "TM": "Turkmenistan",
    "TJ": "Tadschikistan",
    "KG": "Kirgisistan",
    # Americas - Northern
    "US": "Vereinigte Staaten",
    "CA": "Kanada",
    # Americas - Central
    "MX": "Mexiko",
    "GT": "Guatemala",
    "BZ": "Belize",
    "HN": "Honduras",
    "SV": "El Salvador",
    "NI": "Nicaragua",
    "CR": "Costa Rica",
    "PA": "Panama",
    # Americas - Caribbean
    "CU": "Kuba",
    "DO": "Dominikanische Republik",
    "HT": "Haiti",
    "JM": "Jamaika",
    "PR": "Puerto Rico",
    "TT": "Trinidad und Tobago",
    "BS": "Bahamas",
    "BB": "Barbados",
    # Americas - South
    "BR": "Brasilien",
    "AR": "Argentinien",
    "CL": "Chile",
    "CO": "Kolumbien",
    "PE": "Peru",
    "VE": "Venezuela",
    "EC": "Ecuador",
    "BO": "Bolivien",
    "PY": "Paraguay",
    "UY": "Uruguay",
    "GY": "Guyana",
    "SR": "Suriname",
    "GF": "Französisch-Guayana",
    # Africa - Northern
    "EG": "Ägypten",
    "LY": "Libyen",
    "TN": "Tunesien",
    "DZ": "Algerien",
    "MA": "Marokko",
    "SD": "Sudan",
    "SS": "Südsudan",
    # Africa - Western
    "NG": "Nigeria",
    "GH": "Ghana",
    "CI": "Elfenbeinküste",
    "SN": "Senegal",
    "ML": "Mali",
    "BF": "Burkina Faso",
    "NE": "Niger",
    "MR": "Mauretanien",
    "GN": "Guinea",
    "BJ": "Benin",
    "TG": "Togo",
    "SL": "Sierra Leone",
    "LR": "Liberia",
    "GM": "Gambia",
    "GW": "Guinea-Bissau",
    "CV": "Kap Verde",
    # Africa - Eastern
    "KE": "Kenia",
    "ET": "Äthiopien",
    "TZ": "Tansania",
    "UG": "Uganda",
    "RW": "Ruanda",
    "BI": "Burundi",
    "SO": "Somalia",
    "ER": "Eritrea",
    "DJ": "Dschibuti",
    "MG": "Madagaskar",
    "MU": "Mauritius",
    "SC": "Seychellen",
    "KM": "Komoren",
    "MW": "Malawi",
    "MZ": "Mosambik",
    "ZM": "Sambia",
    "ZW": "Simbabwe",
    # Africa - Central
    "CD": "Demokratische Republik Kongo",
    "CG": "Republik Kongo",
    "CF": "Zentralafrikanische Republik",
    "CM": "Kamerun",
    "GA": "Gabun",
    "GQ": "Äquatorialguinea",
    "TD": "Tschad",
    "AO": "Angola",
    "ST": "São Tomé und Príncipe",
    # Africa - Southern
    "ZA": "Südafrika",
    "NA": "Namibia",
    "BW": "Botswana",
    "SZ": "Eswatini",
    "LS": "Lesotho",
    # Oceania
    "AU": "Australien",
    "NZ": "Neuseeland",
    "PG": "Papua-Neuguinea",
    "FJ": "Fidschi",
    "SB": "Salomonen",
    "VU": "Vanuatu",
    "NC": "Neukaledonien",
    "WS": "Samoa",
    "TO": "Tonga",
    "PF": "Französisch-Polynesien",
}


async def enrich_names(db_url: str):
    """Update countries with German names."""
    print(f"Connecting to database: {db_url}")
    conn = await asyncpg.connect(db_url)

    count = 0
    not_found = 0

    for iso, name_de in GERMAN_NAMES.items():
        result = await conn.execute(
            "UPDATE countries SET name_de = $1 WHERE iso_code = $2",
            name_de, iso
        )
        if "UPDATE 1" in result:
            count += 1
            print(f"  Updated: {iso} -> {name_de}")
        else:
            not_found += 1
            print(f"  - Skipped: {iso} (not found in database)")

    await conn.close()
    print(f"\n{'=' * 50}")
    print(f"Enrichment complete!")
    print(f"  Updated: {count} countries with German names")
    print(f"  Not found: {not_found} countries")


if __name__ == "__main__":
    db_url = sys.argv[1] if len(sys.argv) > 1 else \
        "postgresql://postgres:postgres@localhost:5432/news_intelligence"

    print("=" * 50)
    print("German Names Enrichment")
    print("=" * 50)
    asyncio.run(enrich_names(db_url))
