"""
Test script for Knowledge Graph ingestion.

Tests inserting a triplet and querying it back.
"""

import asyncio
import sys
sys.path.insert(0, '/app')

from app.services.neo4j_service import neo4j_service
from app.services.ingestion_service import ingestion_service
from app.models.graph import Entity, Relationship, Triplet


async def test_ingestion():
    """Test ingesting a simple triplet."""

    print("\n" + "="*70)
    print("KNOWLEDGE GRAPH INGESTION TEST")
    print("="*70)

    # Connect to Neo4j
    print("\n1. Connecting to Neo4j...")
    await neo4j_service.connect()
    print("   ✓ Connected")

    # Create a test triplet: (Elon Musk) -[WORKS_FOR]-> (Tesla)
    print("\n2. Creating test triplet...")
    subject = Entity(
        name="Elon Musk",
        type="PERSON",
        properties={"title": "CEO"}
    )

    relationship = Relationship(
        subject="Elon Musk",
        subject_type="PERSON",
        relationship_type="WORKS_FOR",
        object="Tesla",
        object_type="ORGANIZATION",
        confidence=0.95,
        evidence="Elon Musk is the CEO of Tesla",
        source_url="https://example.com/test",
        article_id="test-001"
    )

    obj = Entity(
        name="Tesla",
        type="ORGANIZATION",
        properties={"industry": "Automotive"}
    )

    triplet = Triplet(
        subject=subject,
        relationship=relationship,
        object=obj
    )

    print(f"   Triplet: ({subject.name}) -[{relationship.relationship_type}]-> ({obj.name})")

    # Ingest triplet
    print("\n3. Ingesting triplet into Neo4j...")
    summary = await ingestion_service.ingest_triplet(triplet)
    print(f"   ✓ Ingested successfully")
    print(f"   - Nodes created: {summary['nodes_created']}")
    print(f"   - Relationships created: {summary['relationships_created']}")
    print(f"   - Properties set: {summary['properties_set']}")

    # Query back to verify
    print("\n4. Verifying ingestion...")
    results = await neo4j_service.execute_query("""
        MATCH (subject:Entity {name: $name})-[r]->(target:Entity)
        RETURN subject.name, type(r), target.name, r.confidence
    """, parameters={"name": "Elon Musk"})

    if results:
        for record in results:
            print(f"   ✓ Found: ({record['subject.name']}) -[{record['type(r)']}]-> ({record['target.name']})")
            print(f"     Confidence: {record['r.confidence']}")
    else:
        print("   ✗ No results found!")

    # Get graph stats
    print("\n5. Graph statistics:")
    node_count = await neo4j_service.execute_query("MATCH (n:Entity) RETURN count(n) AS count")
    rel_count = await neo4j_service.execute_query("MATCH ()-[r]->() RETURN count(r) AS count")
    print(f"   - Total nodes: {node_count[0]['count']}")
    print(f"   - Total relationships: {rel_count[0]['count']}")

    # Disconnect
    print("\n6. Disconnecting...")
    await neo4j_service.disconnect()
    print("   ✓ Disconnected")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_ingestion())
