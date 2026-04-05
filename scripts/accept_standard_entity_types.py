#!/usr/bin/env python3
"""Accept standard NER entity types."""
import requests

API_BASE = "http://localhost:8109/api/v1/ontology/proposals"

# Standard NER entity types that should be accepted
STANDARD_TYPES = [
    "PERSON", "ORGANIZATION", "LOCATION", "EVENT", "PRODUCT",
    "MISC", "DATE", "TIME", "MONEY", "PERCENT", "QUANTITY",
    "GPE", "NORP", "FAC", "ORG", "LOC", "WORK_OF_ART", "LAW",
    "LANGUAGE", "CARDINAL", "ORDINAL"
]

def main():
    # Fetch pending NEW_ENTITY_TYPE proposals
    response = requests.get(
        API_BASE,
        params={"change_type": "NEW_ENTITY_TYPE", "status": "PENDING", "limit": 500}
    )
    response.raise_for_status()
    proposals = response.json()["proposals"]

    print(f"Found {len(proposals)} pending NEW_ENTITY_TYPE proposals")

    accepted = 0
    for proposal in proposals:
        # Extract entity type from title
        # Format: "Frequent entity type pattern: PERSON"
        if ":" in proposal["title"]:
            entity_type = proposal["title"].split(":")[-1].strip()

            if entity_type in STANDARD_TYPES:
                try:
                    # Accept proposal
                    requests.put(
                        f"{API_BASE}/{proposal['id']}",
                        params={
                            "status": "ACCEPTED",
                            "reviewed_by": "system",
                        }
                    )
                    print(f"✓ ACCEPTED: {entity_type} ({proposal['occurrence_count']} occurrences)")
                    accepted += 1
                except Exception as e:
                    print(f"✗ Error accepting {entity_type}: {e}")

    print(f"\nAccepted {accepted}/{len(proposals)} proposals")

if __name__ == "__main__":
    main()
