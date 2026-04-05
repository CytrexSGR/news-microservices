# Geolocation Service - Data Import Scripts

Scripts for importing and enriching country boundary data for the Geo News Map feature.

## Quick Start

```bash
# Run complete import pipeline
./run_import.sh postgresql://postgres:postgres@localhost:5432/news_intelligence
```

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `download_data.sh` | Downloads Natural Earth country boundaries (GeoJSON) |
| `import_countries.py` | Imports countries with boundaries into PostGIS |
| `enrich_german_names.py` | Adds German names (name_de) to countries |
| `init_country_stats.sql` | Initializes article count statistics |
| `run_import.sh` | Runs all steps in sequence |

## Data Source

- **Source:** [datasets/geo-countries](https://github.com/datasets/geo-countries)
- **Format:** GeoJSON (MultiPolygon boundaries)
- **License:** Public Domain (PDDL)
- **Coverage:** ~250 countries and territories

## Region Mapping

Countries are mapped to UN M49 regions and subregions:

- **Europe:** Western, Northern, Southern, Eastern
- **Asia:** Eastern, Southern, Western, South-Eastern, Central
- **Americas:** Northern, Central, Caribbean, South
- **Africa:** Northern, Western, Eastern, Central, Southern
- **Oceania:** Australia/NZ, Melanesia, Micronesia, Polynesia

## German Names

German translations are provided for ~170 countries, prioritizing:
1. All European countries
2. Major world powers and news-relevant countries
3. German-speaking countries (DE, AT, CH, LI)

## Usage Examples

### Individual Scripts

```bash
# Download data only
./download_data.sh

# Import with custom database URL
python import_countries.py "postgresql://user:pass@host:5432/db"

# Enrich German names
python enrich_german_names.py "postgresql://user:pass@host:5432/db"

# Initialize stats (requires psql)
psql -d news_intelligence -f init_country_stats.sql
```

### Docker Usage

```bash
# From within geolocation-service container
docker exec -it geolocation-service bash
cd /app/scripts
./run_import.sh postgresql://postgres:postgres@postgres:5432/news_intelligence
```

## Database Requirements

- PostgreSQL 14+
- PostGIS extension enabled
- `countries` and `country_stats` tables created (see migrations)

## Troubleshooting

### PostGIS not installed
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Invalid ISO codes
Some territories have special codes (-99, -1). These are skipped during import.

### Missing German names
Not all countries have German translations. Check `GERMAN_NAMES` dict in `enrich_german_names.py`.
