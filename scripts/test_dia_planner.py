#!/usr/bin/env python3
"""
Test script for DIA Planner (Phase 1.8).

Publishes a test verification.required event to RabbitMQ
and monitors the llm-orchestrator-service response.

Related: ADR-018 (DIA-Planner & Verifier)
"""

import asyncio
import json
import sys
from datetime import datetime
from uuid import uuid4

import aio_pika


# Test Article: Tesla Earnings with incorrect profit figure
TEST_EVENT = {
    "event_id": str(uuid4()),
    "event_type": "verification.required",
    "timestamp": datetime.utcnow().isoformat(),

    # Analysis Context
    "analysis_result_id": str(uuid4()),
    "article_id": str(uuid4()),

    # Original Content (Tesla earnings example with error)
    "article_title": "Tesla Reports Record Q3 2024 Earnings",
    "article_content": """
Tesla Inc. announced record-breaking third-quarter earnings today, with net income
reaching $5 billion - a significant increase from the previous quarter.

The electric vehicle manufacturer reported total revenue of $25.18 billion,
beating analyst expectations of $24.3 billion. CEO Elon Musk credited the strong
performance to improved production efficiency and growing demand for the Model 3
and Model Y vehicles.

"This quarter demonstrates our ability to scale production while maintaining
profitability," Musk said during the earnings call. The company also announced
plans to expand production capacity at its Texas Gigafactory.

Tesla's automotive gross margin improved to 18.7%, up from 16.3% in Q2 2024.
The company delivered 462,890 vehicles in Q3, a new quarterly record.
""".strip(),
    "article_url": "https://example.com/tesla-q3-2024-earnings",
    "article_published_at": "2024-10-15T14:30:00Z",

    # UQ Sensor Output (detects uncertainty)
    "uq_confidence_score": 0.62,  # Below threshold (0.65)
    "uncertainty_factors": [
        "Low confidence in claim accuracy",
        "Numerical claim lacks verification",
        "Financial data requires fact-checking"
    ],

    # Current Analysis (contains the error)
    "analysis_summary": "Tesla reports record $5B profit in Q3 2024, beating expectations.",
    "extracted_entities": [
        {"entity": "Tesla Inc.", "type": "ORGANIZATION"},
        {"entity": "$5 billion", "type": "MONEY"},
        {"entity": "Q3 2024", "type": "DATE"}
    ],
    "category_analysis": {
        "primary_category": "business",
        "subcategories": ["automotive", "earnings"]
    },

    "priority": "high"
}


async def publish_test_event():
    """
    Publish test event to RabbitMQ verification_exchange.
    """

    print("=" * 80)
    print("DIA Planner - Phase 1.8 Integration Test")
    print("=" * 80)
    print()

    try:
        # Connect to RabbitMQ
        print("[1/4] Connecting to RabbitMQ...")
        connection = await aio_pika.connect_robust(
            "amqp://guest:guest@localhost:5672/",
            timeout=10
        )
        print("      ✓ Connected to RabbitMQ")

        # Create channel
        channel = await connection.channel()

        # Get exchange
        print("[2/4] Getting verification_exchange...")
        exchange = await channel.get_exchange("verification_exchange")
        print("      ✓ Exchange found")

        # Publish event
        print("[3/4] Publishing test event...")
        print(f"      Article: {TEST_EVENT['article_title']}")
        print(f"      UQ Score: {TEST_EVENT['uq_confidence_score']}")
        print(f"      Factors: {len(TEST_EVENT['uncertainty_factors'])}")

        routing_key = f"verification.required.{TEST_EVENT['analysis_result_id']}"

        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(TEST_EVENT, indent=2).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )
        print(f"      ✓ Event published with routing_key: {routing_key}")

        # Close connection
        await connection.close()
        print("[4/4] Connection closed")
        print()

        # Instructions
        print("=" * 80)
        print("Test Event Published Successfully!")
        print("=" * 80)
        print()
        print("Next Steps:")
        print("1. Monitor llm-orchestrator-service logs:")
        print("   docker logs -f news-llm-orchestrator")
        print()
        print("2. Look for these log entries:")
        print("   - [Consumer] Processing verification for article_id=...")
        print("   - [DIAPlanner] Stage 1: Analyzing root cause...")
        print("   - [DIAPlanner] Stage 1 Complete: hypothesis_type=..., confidence=...")
        print("   - [DIAPlanner] Stage 2: Generating verification plan...")
        print("   - [DIAPlanner] Stage 2 Complete: priority=..., methods=...")
        print("   - [Consumer] Planning completed successfully")
        print()
        print("3. Expected Results:")
        print("   Stage 1 Output: ProblemHypothesis")
        print("     - Should identify '$5 billion' figure as problematic")
        print("     - hypothesis_type: 'factual_error'")
        print("     - reasoning: Historical Tesla profits are $3-4.5B range")
        print()
        print("   Stage 2 Output: VerificationPlan")
        print("     - priority: 'high'")
        print("     - verification_methods: financial_data_lookup, perplexity_deep_search")
        print("     - external_sources: SEC EDGAR, Tesla Investor Relations")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(publish_test_event())
    sys.exit(0 if success else 1)
