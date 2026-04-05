#!/usr/bin/env python3
"""Analyze entity extraction quality: V2 vs V3."""
import psycopg2
import json
from collections import Counter

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="news_mcp",
    user="news_user",
    password="your_db_password"
)

def analyze_v2_entities():
    """Analyze V2 entity types."""
    cursor = conn.cursor()

    query = """
    SELECT tier1_results
    FROM article_analysis
    WHERE pipeline_version = '2.0'
        AND tier1_results->'entities' IS NOT NULL
        AND success = true
    LIMIT 5000;
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    entity_types = Counter()
    total_entities = 0
    articles_with_entities = 0

    for row in rows:
        tier1_data = row[0]
        if tier1_data and 'entities' in tier1_data:
            entities = tier1_data.get('entities', [])
            if entities:
                articles_with_entities += 1
                for entity in entities:
                    entity_type = entity.get('type', 'UNKNOWN')
                    entity_types[entity_type] += 1
                    total_entities += 1

    cursor.close()

    return {
        'total_articles_sampled': len(rows),
        'articles_with_entities': articles_with_entities,
        'total_entities': total_entities,
        'type_distribution': entity_types
    }

def analyze_v3_entities():
    """Analyze V3 entity types."""
    cursor = conn.cursor()

    query = """
    SELECT tier1_results
    FROM article_analysis
    WHERE pipeline_version = '3.0'
        AND tier1_results->'entities' IS NOT NULL
        AND success = true
    LIMIT 1000;
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    entity_types = Counter()
    total_entities = 0
    articles_with_entities = 0

    for row in rows:
        tier1_data = row[0]
        if tier1_data and 'entities' in tier1_data:
            entities = tier1_data.get('entities', [])
            if entities:
                articles_with_entities += 1
                for entity in entities:
                    entity_type = entity.get('type', 'UNKNOWN')
                    entity_types[entity_type] += 1
                    total_entities += 1

    cursor.close()

    return {
        'total_articles_sampled': len(rows),
        'articles_with_entities': articles_with_entities,
        'total_entities': total_entities,
        'type_distribution': entity_types
    }

def print_results(version, results):
    """Print analysis results."""
    print(f"\n{'='*60}")
    print(f"  {version} Entity Quality Analysis")
    print(f"{'='*60}")
    print(f"Articles Sampled:        {results['total_articles_sampled']:,}")
    print(f"Articles with Entities:  {results['articles_with_entities']:,}")
    print(f"Total Entities:          {results['total_entities']:,}")
    print(f"\nEntity Type Distribution:")
    print(f"{'─'*60}")

    total = sum(results['type_distribution'].values())
    for entity_type, count in results['type_distribution'].most_common(15):
        percentage = 100.0 * count / total
        print(f"  {entity_type:20s} {count:6,} ({percentage:5.2f}%)")

def main():
    print("Analyzing Entity Extraction Quality...")

    # Analyze V2
    v2_results = analyze_v2_entities()
    print_results("Content-Analysis V2", v2_results)

    # Analyze V3
    v3_results = analyze_v3_entities()
    print_results("Content-Analysis V3", v3_results)

    # Comparison
    print(f"\n{'='*60}")
    print(f"  Quality Comparison")
    print(f"{'='*60}")

    v2_unknown = v2_results['type_distribution'].get('UNKNOWN', 0)
    v3_unknown = v3_results['type_distribution'].get('UNKNOWN', 0)

    v2_unknown_pct = 100.0 * v2_unknown / v2_results['total_entities'] if v2_results['total_entities'] > 0 else 0
    v3_unknown_pct = 100.0 * v3_unknown / v3_results['total_entities'] if v3_results['total_entities'] > 0 else 0

    print(f"V2 UNKNOWN entities:     {v2_unknown:,} ({v2_unknown_pct:.2f}%)")
    print(f"V3 UNKNOWN entities:     {v3_unknown:,} ({v3_unknown_pct:.2f}%)")

    if v2_unknown_pct > 0:
        improvement = v2_unknown_pct - v3_unknown_pct
        print(f"\n✓ V3 Improvement:        {improvement:.2f}% fewer UNKNOWN entities")

    print(f"\n{'='*60}\n")

    conn.close()

if __name__ == "__main__":
    main()
