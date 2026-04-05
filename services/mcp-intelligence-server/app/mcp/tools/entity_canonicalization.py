"""Entity Canonicalization MCP Tools."""

from ...models import MCPToolResult
from ...clients import EntityCanonClient
from .registry import register_tool


@register_tool(
    name="canonicalize_entity",
    description="Canonicalize entity to resolve duplicates and name variations using vector similarity. Finds canonical form of entity name.",
    parameters=[
        {
            "name": "entity_name",
            "type": "string",
            "description": "Entity name to canonicalize",
            "required": True,
        },
        {
            "name": "entity_type",
            "type": "string",
            "description": "Entity type (PERSON, ORG, GPE, LOC, etc.)",
            "required": True,
        },
    ],
    service="entity-canonicalization",
    category="entity",
    cost="$0",
    latency="~100ms",
)
async def canonicalize_entity(
    entity_name: str, entity_type: str, client: EntityCanonClient
) -> MCPToolResult:
    """Canonicalize entity name."""
    try:
        result = await client.canonicalize_entity(entity_name, entity_type)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "entity_name": entity_name,
                "entity_type": entity_type,
                "service": "entity-canonicalization",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_entity_clusters",
    description="Get entity clusters for given type. Returns all canonical entities and their variants/duplicates.",
    parameters=[
        {
            "name": "entity_type",
            "type": "string",
            "description": "Entity type to query (PERSON, ORG, GPE, etc.)",
            "required": True,
        }
    ],
    service="entity-canonicalization",
    category="entity",
    cost="$0",
    latency="~150ms",
)
async def get_entity_clusters(entity_type: str, client: EntityCanonClient) -> MCPToolResult:
    """Get entity clusters."""
    try:
        result = await client.get_entity_clusters(entity_type)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"entity_type": entity_type, "service": "entity-canonicalization"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="batch_canonicalize_entities",
    description="Batch canonicalize multiple entities in single request. More efficient than individual calls for large batches. Returns canonical forms with similarity scores for each entity.",
    parameters=[
        {
            "name": "entities",
            "type": "array",
            "description": "List of entities to canonicalize. Each entity should have: entity_name (string), entity_type (string), language (string, optional). Example: [{\"entity_name\": \"USA\", \"entity_type\": \"LOCATION\", \"language\": \"en\"}, {\"entity_name\": \"Barack Obama\", \"entity_type\": \"PERSON\"}]",
            "required": True,
        }
    ],
    service="entity-canonicalization",
    category="entity",
    cost="$0",
    latency="~500ms for 10 entities",
)
async def batch_canonicalize_entities(entities: list, client: EntityCanonClient) -> MCPToolResult:
    """Batch canonicalize entities."""
    try:
        result = await client.batch_canonicalize_entities(entities)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "batch_size": len(entities),
                "service": "entity-canonicalization",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_canonicalization_stats",
    description="Get canonicalization statistics and metrics. Returns total entities processed, canonical entities count, merge operations, entity type distribution, and cache hit rates.",
    parameters=[],
    service="entity-canonicalization",
    category="entity",
    cost="$0",
    latency="~100ms",
)
async def get_canonicalization_stats(client: EntityCanonClient) -> MCPToolResult:
    """Get canonicalization stats."""
    try:
        result = await client.get_canonicalization_stats()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"service": "entity-canonicalization"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_async_job_status",
    description="Get status of async batch canonicalization job. Returns job status (pending, processing, completed, failed) with progress information.",
    parameters=[
        {
            "name": "job_id",
            "type": "string",
            "description": "Job ID from async batch canonicalization request",
            "required": True,
        }
    ],
    service="entity-canonicalization",
    category="entity",
    cost="$0",
    latency="~50ms",
)
async def get_async_job_status(job_id: str, client: EntityCanonClient) -> MCPToolResult:
    """Get async job status."""
    try:
        result = await client.get_async_job_status(job_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"job_id": job_id, "service": "entity-canonicalization"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_async_job_result",
    description="Get result of completed async batch canonicalization job. Returns canonicalization results if job completed successfully. Use get_async_job_status first to check if job is completed.",
    parameters=[
        {
            "name": "job_id",
            "type": "string",
            "description": "Job ID from async batch canonicalization request",
            "required": True,
        }
    ],
    service="entity-canonicalization",
    category="entity",
    cost="$0",
    latency="~100ms",
)
async def get_async_job_result(job_id: str, client: EntityCanonClient) -> MCPToolResult:
    """Get async job result."""
    try:
        result = await client.get_async_job_result(job_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"job_id": job_id, "service": "entity-canonicalization"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_entity_aliases",
    description="Get all aliases/variants for a canonical entity name. Returns list of all entity name variations that resolve to the given canonical form.",
    parameters=[
        {
            "name": "canonical_name",
            "type": "string",
            "description": "Canonical entity name to query aliases for",
            "required": True,
        }
    ],
    service="entity-canonicalization",
    category="entity",
    cost="$0",
    latency="~80ms",
)
async def get_entity_aliases(canonical_name: str, client: EntityCanonClient) -> MCPToolResult:
    """Get entity aliases."""
    try:
        result = await client.get_entity_aliases(canonical_name)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "canonical_name": canonical_name,
                "service": "entity-canonicalization",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))
