#!/usr/bin/env python3
"""
Fix entities without entity_id/entity_type properties.

Generates deterministic entity_id (MD5 hash of name+type).
"""
import hashlib
from neo4j import GraphDatabase

# Neo4j connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4j_password_2024"

def generate_entity_id(name: str, entity_type: str) -> str:
    """Generate deterministic entity_id from name and type."""
    return hashlib.md5(f"{name}:{entity_type}".encode('utf-8')).hexdigest()[:16]

def fix_entities():
    """Fix all entities missing entity_id or entity_type."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        # Get all entities without properties
        result = session.run("""
            MATCH (e:Entity)
            WHERE (e.entity_id IS NULL OR e.entity_type IS NULL)
              AND NOT 'Article' IN labels(e)
              AND NOT 'Symbolic' IN labels(e)
              AND e.name IS NOT NULL
              AND e.type IS NOT NULL
            RETURN id(e) AS node_id, e.name AS name, e.type AS type
        """)

        entities = list(result)
        total = len(entities)

        print(f"Found {total} entities to fix...")

        # Fix each entity
        fixed = 0
        for entity in entities:
            node_id = entity["node_id"]
            name = entity["name"]
            entity_type = entity["type"]

            # Generate entity_id
            entity_id = generate_entity_id(name, entity_type)

            # Update entity
            session.run("""
                MATCH (e:Entity)
                WHERE id(e) = $node_id
                SET e.entity_id = $entity_id,
                    e.entity_type = $entity_type
            """, node_id=node_id, entity_id=entity_id, entity_type=entity_type)

            fixed += 1
            if fixed % 50 == 0:
                print(f"Fixed {fixed}/{total} entities...")

        print(f"\n✓ Fixed {fixed} entities successfully!")

    driver.close()

if __name__ == "__main__":
    fix_entities()
