"""
Findings Ingestion Endpoint

Ingests structured symbolic findings from Intelligence Synthesizer into Neo4j knowledge graph.
Generates Cypher CREATE statements for nodes and relationships based on symbolic finding types.
"""

import logging
import time
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.services.neo4j_service import neo4j_service
from app.models.findings import (
    IngestFindingsRequest,
    IngestFindingsResponse,
    GraphNodeCreated,
    GraphRelationshipCreated,
    KeyFinding,
    FindingCategory,
    EventTypeSymbolic,
    IHLConcernSymbolic,
    RegionalImpactSymbolic,
    FinancialImpactSymbolic,
    PoliticalDevelopmentSymbolic,
    SecurityThreatSymbolic,
    HumanitarianCrisisSymbolic,
    ActorRole
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/v1/graph/findings", response_model=IngestFindingsResponse)
async def ingest_findings(request: IngestFindingsRequest) -> IngestFindingsResponse:
    """
    Ingest symbolic findings into knowledge graph.

    Processes findings from Intelligence Synthesizer and creates:
    - Nodes for entities (countries, events, markets, etc.)
    - Relationships between entities with confidence scores
    - Properties for detailed metadata

    Args:
        request: IngestFindingsRequest with article_id and findings list

    Returns:
        IngestFindingsResponse with created nodes, relationships, and metrics

    Example:
        POST /api/v1/graph/findings
        {
          "article_id": "123e4567-e89b-12d3-a456-426614174000",
          "findings": [
            {
              "finding_id": "F1",
              "category": "event_type",
              "confidence": 0.95,
              "supporting_agents": ["CONFLICT_EVENT_ANALYST"],
              "priority": "critical",
              "symbolic": {
                "event_type": "MISSILE_STRIKE",
                "target": "INFRASTRUCTURE",
                "severity": "CRITICAL",
                "actors": {"RU": "aggressor", "UA": "defender"},
                "location": "UA_KHARKIV",
                "casualties": 15
              }
            }
          ]
        }
    """
    start_time = time.time()
    article_id = request.article_id
    findings = request.findings

    nodes_created: List[GraphNodeCreated] = []
    relationships_created: List[GraphRelationshipCreated] = []
    errors: List[str] = []

    logger.info(f"Ingesting {len(findings)} findings for article {article_id}")

    try:
        for finding in findings:
            try:
                # Route to appropriate handler based on category
                if finding.category == FindingCategory.EVENT_TYPE:
                    await _ingest_event_type(
                        finding, article_id, nodes_created, relationships_created
                    )
                elif finding.category == FindingCategory.IHL_CONCERN:
                    await _ingest_ihl_concern(
                        finding, article_id, nodes_created, relationships_created
                    )
                elif finding.category == FindingCategory.REGIONAL_IMPACT:
                    await _ingest_regional_impact(
                        finding, article_id, nodes_created, relationships_created
                    )
                elif finding.category == FindingCategory.FINANCIAL_IMPACT:
                    await _ingest_financial_impact(
                        finding, article_id, nodes_created, relationships_created
                    )
                elif finding.category == FindingCategory.POLITICAL_DEVELOPMENT:
                    await _ingest_political_development(
                        finding, article_id, nodes_created, relationships_created
                    )
                elif finding.category == FindingCategory.SECURITY_THREAT:
                    await _ingest_security_threat(
                        finding, article_id, nodes_created, relationships_created
                    )
                elif finding.category == FindingCategory.HUMANITARIAN_CRISIS:
                    await _ingest_humanitarian_crisis(
                        finding, article_id, nodes_created, relationships_created
                    )
                else:
                    errors.append(f"Unknown category: {finding.category} for finding {finding.finding_id}")

            except Exception as e:
                error_msg = f"Failed to ingest finding {finding.finding_id}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Ingestion complete for article {article_id}: "
            f"processed={len(findings)}, nodes={len(nodes_created)}, "
            f"relationships={len(relationships_created)}, time={processing_time_ms}ms"
        )

        return IngestFindingsResponse(
            article_id=article_id,
            findings_processed=len(findings),
            nodes_created=nodes_created,
            relationships_created=relationships_created,
            processing_time_ms=processing_time_ms,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Findings ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest findings: {str(e)}"
        )


# ============================================================================
# CATEGORY-SPECIFIC INGESTION HANDLERS
# ============================================================================

async def _ingest_event_type(
    finding: KeyFinding,
    article_id: str,
    nodes_created: List[GraphNodeCreated],
    relationships_created: List[GraphRelationshipCreated]
):
    """Ingest event_type symbolic finding into Neo4j."""
    symbolic: EventTypeSymbolic = finding.symbolic

    # Find aggressor and affected actors
    aggressors = [code for code, role in symbolic.actors.items() if role == ActorRole.AGGRESSOR]
    targets = [code for code, role in symbolic.actors.items() if role in [ActorRole.DEFENDER, ActorRole.AFFECTED]]

    # Create ATTACKS relationships: Aggressor -> Target
    for aggressor in aggressors:
        for target in targets:
            cypher = """
            MERGE (source:LOCATION {name: $aggressor, iso_code: $aggressor})
            MERGE (target:LOCATION {name: $target, iso_code: $target})
            CREATE (source)-[r:ATTACKS {
                event_type: $event_type,
                target_type: $target_type,
                severity: $severity,
                casualties: $casualties,
                location: $location,
                article_id: $article_id,
                confidence: $confidence,
                created_at: datetime()
            }]->(target)
            RETURN id(source) AS source_id, id(target) AS target_id, id(r) AS rel_id
            """

            result = await neo4j_service.execute_query(cypher, parameters={
                "aggressor": aggressor,
                "target": target,
                "event_type": symbolic.event_type.value,
                "target_type": symbolic.target.value,
                "severity": symbolic.severity.value,
                "casualties": symbolic.casualties,
                "location": symbolic.location,
                "article_id": article_id,
                "confidence": finding.confidence
            })

            if result:
                record = result[0]
                nodes_created.append(GraphNodeCreated(
                    node_id=str(record["source_id"]),
                    node_type="LOCATION",
                    name=aggressor
                ))
                nodes_created.append(GraphNodeCreated(
                    node_id=str(record["target_id"]),
                    node_type="LOCATION",
                    name=target
                ))
                relationships_created.append(GraphRelationshipCreated(
                    relationship_id=str(record["rel_id"]),
                    relationship_type="ATTACKS",
                    source_node=aggressor,
                    target_node=target,
                    confidence=finding.confidence
                ))


async def _ingest_ihl_concern(
    finding: KeyFinding,
    article_id: str,
    nodes_created: List[GraphNodeCreated],
    relationships_created: List[GraphRelationshipCreated]
):
    """Ingest ihl_concern symbolic finding into Neo4j."""
    symbolic: IHLConcernSymbolic = finding.symbolic

    # Create VIOLATES_IHL relationships for each responsible actor
    for actor in symbolic.actors:
        violation_name = f"IHL_VIOLATION_{symbolic.ihl_type.value}"

        cypher = """
        MERGE (actor:LOCATION {name: $actor, iso_code: $actor})
        MERGE (violation:IHL_VIOLATION {name: $violation_name, violation_type: $violation_type})
        CREATE (actor)-[r:VIOLATES_IHL {
            violation_type: $violation_type,
            severity: $severity,
            affected_population: $affected_population,
            protected_status: $protected_status,
            article_id: $article_id,
            confidence: $confidence,
            created_at: datetime()
        }]->(violation)
        RETURN id(actor) AS actor_id, id(violation) AS violation_id, id(r) AS rel_id
        """

        result = await neo4j_service.execute_query(cypher, parameters={
            "actor": actor,
            "violation_name": violation_name,
            "violation_type": symbolic.ihl_type.value,
            "severity": symbolic.violation_level.value,
            "affected_population": symbolic.affected_population,
            "protected_status": symbolic.protected_status,
            "article_id": article_id,
            "confidence": finding.confidence
        })

        if result:
            record = result[0]
            nodes_created.append(GraphNodeCreated(
                node_id=str(record["actor_id"]),
                node_type="LOCATION",
                name=actor
            ))
            nodes_created.append(GraphNodeCreated(
                node_id=str(record["violation_id"]),
                node_type="IHL_VIOLATION",
                name=violation_name
            ))
            relationships_created.append(GraphRelationshipCreated(
                relationship_id=str(record["rel_id"]),
                relationship_type="VIOLATES_IHL",
                source_node=actor,
                target_node=violation_name,
                confidence=finding.confidence
            ))


async def _ingest_regional_impact(
    finding: KeyFinding,
    article_id: str,
    nodes_created: List[GraphNodeCreated],
    relationships_created: List[GraphRelationshipCreated]
):
    """Ingest regional_impact symbolic finding into Neo4j."""
    symbolic: RegionalImpactSymbolic = finding.symbolic

    # Create AFFECTS_REGIONALLY relationships between countries
    for i, country in enumerate(symbolic.affected_countries):
        for other_country in symbolic.affected_countries[i+1:]:
            cypher = """
            MERGE (country1:LOCATION {name: $country1, iso_code: $country1})
            MERGE (country2:LOCATION {name: $country2, iso_code: $country2})
            CREATE (country1)-[r:AFFECTS_REGIONALLY {
                impact_type: $impact_type,
                severity: $severity,
                spillover_risk: $spillover_risk,
                stability: $stability,
                article_id: $article_id,
                confidence: $confidence,
                created_at: datetime()
            }]->(country2)
            RETURN id(country1) AS c1_id, id(country2) AS c2_id, id(r) AS rel_id
            """

            result = await neo4j_service.execute_query(cypher, parameters={
                "country1": country,
                "country2": other_country,
                "impact_type": symbolic.impact_type,  # Now a string, not enum
                "severity": symbolic.severity,
                "spillover_risk": symbolic.spillover_risk,
                "stability": symbolic.regional_stability,  # Now a string, not enum
                "article_id": article_id,
                "confidence": finding.confidence
            })

            if result:
                record = result[0]
                nodes_created.append(GraphNodeCreated(
                    node_id=str(record["c1_id"]),
                    node_type="LOCATION",
                    name=country
                ))
                nodes_created.append(GraphNodeCreated(
                    node_id=str(record["c2_id"]),
                    node_type="LOCATION",
                    name=other_country
                ))
                relationships_created.append(GraphRelationshipCreated(
                    relationship_id=str(record["rel_id"]),
                    relationship_type="AFFECTS_REGIONALLY",
                    source_node=country,
                    target_node=other_country,
                    confidence=finding.confidence
                ))


async def _ingest_financial_impact(
    finding: KeyFinding,
    article_id: str,
    nodes_created: List[GraphNodeCreated],
    relationships_created: List[GraphRelationshipCreated]
):
    """Ingest financial_impact symbolic finding into Neo4j."""
    symbolic: FinancialImpactSymbolic = finding.symbolic

    # Create IMPACTS_MARKET relationships
    event_name = "FINANCIAL_EVENT"

    for market_code, change in symbolic.markets.items():
        cypher = """
        MERGE (event:FINANCIAL_EVENT {name: $event_name, volatility: $volatility})
        MERGE (market:MARKET {name: $market_code, code: $market_code})
        CREATE (event)-[r:IMPACTS_MARKET {
            change_percentage: $change_percentage,
            volatility: $volatility,
            duration: $duration,
            article_id: $article_id,
            confidence: $confidence,
            created_at: datetime()
        }]->(market)
        RETURN id(event) AS event_id, id(market) AS market_id, id(r) AS rel_id
        """

        result = await neo4j_service.execute_query(cypher, parameters={
            "event_name": event_name,
            "market_code": market_code,
            "change_percentage": change,
            "volatility": symbolic.volatility.value,
            "duration": symbolic.duration.value,
            "article_id": article_id,
            "confidence": finding.confidence
        })

        if result:
            record = result[0]
            nodes_created.append(GraphNodeCreated(
                node_id=str(record["event_id"]),
                node_type="FINANCIAL_EVENT",
                name=event_name
            ))
            nodes_created.append(GraphNodeCreated(
                node_id=str(record["market_id"]),
                node_type="MARKET",
                name=market_code
            ))
            relationships_created.append(GraphRelationshipCreated(
                relationship_id=str(record["rel_id"]),
                relationship_type="IMPACTS_MARKET",
                source_node=event_name,
                target_node=market_code,
                confidence=finding.confidence
            ))


async def _ingest_political_development(
    finding: KeyFinding,
    article_id: str,
    nodes_created: List[GraphNodeCreated],
    relationships_created: List[GraphRelationshipCreated]
):
    """Ingest political_development symbolic finding into Neo4j."""
    symbolic: PoliticalDevelopmentSymbolic = finding.symbolic

    # Create INFLUENCES_POLICY relationships
    for actor_code, stance in symbolic.actors.items():
        for affected in symbolic.affected_countries:
            if actor_code != affected:  # Don't create self-relationships
                cypher = """
                MERGE (actor:LOCATION {name: $actor, iso_code: $actor})
                MERGE (affected:LOCATION {name: $affected, iso_code: $affected})
                CREATE (actor)-[r:INFLUENCES_POLICY {
                    policy_area: $policy_area,
                    direction: $direction,
                    alignment: $alignment,
                    position: $position,
                    impact_level: $impact_level,
                    article_id: $article_id,
                    confidence: $confidence,
                    created_at: datetime()
                }]->(affected)
                RETURN id(actor) AS actor_id, id(affected) AS affected_id, id(r) AS rel_id
                """

                result = await neo4j_service.execute_query(cypher, parameters={
                    "actor": actor_code,
                    "affected": affected,
                    "policy_area": symbolic.policy_area,  # Now a string, not enum
                    "direction": symbolic.direction,  # Now a string, not enum
                    "alignment": stance.alignment.value,  # Still enum
                    "position": stance.position,  # Now a string, not enum
                    "impact_level": symbolic.impact_level.value,  # Still enum
                    "article_id": article_id,
                    "confidence": finding.confidence
                })

                if result:
                    record = result[0]
                    nodes_created.append(GraphNodeCreated(
                        node_id=str(record["actor_id"]),
                        node_type="LOCATION",
                        name=actor_code
                    ))
                    nodes_created.append(GraphNodeCreated(
                        node_id=str(record["affected_id"]),
                        node_type="LOCATION",
                        name=affected
                    ))
                    relationships_created.append(GraphRelationshipCreated(
                        relationship_id=str(record["rel_id"]),
                        relationship_type="INFLUENCES_POLICY",
                        source_node=actor_code,
                        target_node=affected,
                        confidence=finding.confidence
                    ))


async def _ingest_security_threat(
    finding: KeyFinding,
    article_id: str,
    nodes_created: List[GraphNodeCreated],
    relationships_created: List[GraphRelationshipCreated]
):
    """Ingest security_threat symbolic finding into Neo4j."""
    symbolic: SecurityThreatSymbolic = finding.symbolic

    # Create THREATENS relationships
    for source_code in symbolic.source:
        for target_code in symbolic.target:
            cypher = """
            MERGE (source:LOCATION {name: $source, iso_code: $source})
            MERGE (target:LOCATION {name: $target, iso_code: $target})
            CREATE (source)-[r:THREATENS {
                threat_type: $threat_type,
                severity: $severity,
                imminence: $imminence,
                article_id: $article_id,
                confidence: $confidence,
                created_at: datetime()
            }]->(target)
            RETURN id(source) AS source_id, id(target) AS target_id, id(r) AS rel_id
            """

            result = await neo4j_service.execute_query(cypher, parameters={
                "source": source_code,
                "target": target_code,
                "threat_type": symbolic.threat_type,  # Now a string, not enum
                "severity": symbolic.severity,
                "imminence": symbolic.imminence,  # Now a string, not enum
                "article_id": article_id,
                "confidence": finding.confidence
            })

            if result:
                record = result[0]
                nodes_created.append(GraphNodeCreated(
                    node_id=str(record["source_id"]),
                    node_type="LOCATION",
                    name=source_code
                ))
                nodes_created.append(GraphNodeCreated(
                    node_id=str(record["target_id"]),
                    node_type="LOCATION",
                    name=target_code
                ))
                relationships_created.append(GraphRelationshipCreated(
                    relationship_id=str(record["rel_id"]),
                    relationship_type="THREATENS",
                    source_node=source_code,
                    target_node=target_code,
                    confidence=finding.confidence
                ))


async def _ingest_humanitarian_crisis(
    finding: KeyFinding,
    article_id: str,
    nodes_created: List[GraphNodeCreated],
    relationships_created: List[GraphRelationshipCreated]
):
    """Ingest humanitarian_crisis symbolic finding into Neo4j."""
    symbolic: HumanitarianCrisisSymbolic = finding.symbolic

    crisis_name = f"CRISIS_{symbolic.crisis_type}_{symbolic.location}"  # Now a string, not enum

    cypher = """
    MERGE (crisis:HUMANITARIAN_CRISIS {
        name: $crisis_name,
        crisis_type: $crisis_type,
        severity: $severity
    })
    MERGE (location:LOCATION {name: $location, location_code: $location})
    CREATE (crisis)-[r:OCCURS_AT {
        crisis_type: $crisis_type,
        affected_population: $affected_population,
        severity: $severity,
        urgent_needs: $urgent_needs,
        article_id: $article_id,
        confidence: $confidence,
        created_at: datetime()
    }]->(location)
    RETURN id(crisis) AS crisis_id, id(location) AS location_id, id(r) AS rel_id
    """

    result = await neo4j_service.execute_query(cypher, parameters={
        "crisis_name": crisis_name,
        "crisis_type": symbolic.crisis_type,  # Now a string, not enum
        "severity": symbolic.severity.value,  # Still enum
        "location": symbolic.location,
        "affected_population": symbolic.affected_population,
        "urgent_needs": symbolic.urgent_needs,  # Already a list of strings, no .value needed
        "article_id": article_id,
        "confidence": finding.confidence
    })

    if result:
        record = result[0]
        nodes_created.append(GraphNodeCreated(
            node_id=str(record["crisis_id"]),
            node_type="HUMANITARIAN_CRISIS",
            name=crisis_name
        ))
        nodes_created.append(GraphNodeCreated(
            node_id=str(record["location_id"]),
            node_type="LOCATION",
            name=symbolic.location
        ))
        relationships_created.append(GraphRelationshipCreated(
            relationship_id=str(record["rel_id"]),
            relationship_type="OCCURS_AT",
            source_node=crisis_name,
            target_node=symbolic.location,
            confidence=finding.confidence
        ))
