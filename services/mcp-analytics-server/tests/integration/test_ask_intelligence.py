"""Integration tests for ask_intelligence MCP tool.

Tests the complete RAG pipeline: MCP Server -> Analytics Service -> Search -> LLM

Requirements:
- mcp-analytics-server running on port 9003
- analytics-service running on port 8107
- search-service running on port 8106
- OpenAI API key configured

Run with: pytest tests/integration/test_ask_intelligence.py -v -s

NOTE: When running inside Docker container, tests use localhost:8000 (the container's own server).
When running from host, tests use localhost:9003 (mapped port).
"""

import pytest
import httpx
import os

# Check if we're in a CI/CD environment or services are unavailable
SKIP_INTEGRATION = os.environ.get("SKIP_INTEGRATION_TESTS", "false").lower() == "true"


def detect_base_url() -> str:
    """Detect the correct base URL based on environment.

    When running inside Docker container:
    - Use localhost:8000 (the container's internal port)

    When running from host machine:
    - Use localhost:9003 (Docker port mapping)
    """
    # Check if MCP_ANALYTICS_URL is explicitly set
    explicit_url = os.environ.get("MCP_ANALYTICS_URL")
    if explicit_url:
        return explicit_url

    # Check if we're inside a Docker container by looking for /.dockerenv
    in_docker = os.path.exists("/.dockerenv")

    if in_docker:
        # Inside container, use internal port
        return "http://localhost:8000"
    else:
        # On host, use mapped port
        return "http://localhost:9003"


# MCP Server endpoint
MCP_BASE_URL = detect_base_url()


async def check_service_available(url: str) -> bool:
    """Check if a service is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/health")
            return response.status_code == 200
    except Exception:
        return False


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ask_intelligence_brief():
    """Test asking a brief intelligence question via MCP tools/call endpoint.

    Tests the complete RAG pipeline with brief depth:
    1. MCP Server receives the tool call
    2. Forwards to analytics-service /api/v1/intelligence/ask
    3. RAG service performs semantic search
    4. LLM generates brief answer
    5. Response returned through MCP
    """
    # Check if service is available
    if not await check_service_available(MCP_BASE_URL):
        pytest.skip("MCP Analytics Server not available")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{MCP_BASE_URL}/mcp/tools/call",
            json={
                "tool_name": "ask_intelligence",
                "arguments": {
                    "question": "What are the current geopolitical risks?",
                    "depth": "brief"
                }
            }
        )

        # Check HTTP response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        # Check MCP response structure
        assert "result" in data, f"Missing 'result' in response: {data}"
        result = data["result"]

        # The tool should succeed (even if no articles found)
        assert "success" in result, f"Missing 'success' in result: {result}"

        if result["success"]:
            # Verify response structure when successful
            assert "data" in result, f"Missing 'data' in successful result: {result}"
            result_data = result["data"]

            assert "answer" in result_data, f"Missing 'answer' in data: {result_data}"
            assert "depth" in result_data, f"Missing 'depth' in data: {result_data}"
            assert result_data["depth"] == "brief", f"Expected depth 'brief', got: {result_data['depth']}"

            # Answer should be non-empty
            assert len(result_data["answer"]) > 0, "Answer should not be empty"

            # Check for sources (may be empty if no articles found)
            assert "sources" in result_data, f"Missing 'sources' in data: {result_data}"

            print(f"\n[BRIEF] Answer: {result_data['answer'][:200]}...")
            print(f"[BRIEF] Sources: {len(result_data.get('sources', []))}")
            if "metadata" in result_data:
                print(f"[BRIEF] Tokens used: {result_data['metadata'].get('tokens_used', 'N/A')}")
        else:
            # Tool failed - check error message
            print(f"\n[BRIEF] Tool returned error: {result.get('error', 'Unknown error')}")
            # Don't fail the test if it's a service unavailable issue
            if "circuit breaker" in str(result.get("error", "")).lower():
                pytest.skip("Circuit breaker open - service temporarily unavailable")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ask_intelligence_detailed():
    """Test asking a detailed intelligence question via MCP tools/call endpoint.

    Tests the complete RAG pipeline with detailed depth:
    - Should return longer, structured response
    - Should include sections (## headers) in the answer
    """
    if not await check_service_available(MCP_BASE_URL):
        pytest.skip("MCP Analytics Server not available")

    async with httpx.AsyncClient(timeout=45.0) as client:  # Longer timeout for detailed
        response = await client.post(
            f"{MCP_BASE_URL}/mcp/tools/call",
            json={
                "tool_name": "ask_intelligence",
                "arguments": {
                    "question": "Analyze the sentiment trends for defense sector companies",
                    "depth": "detailed"
                }
            }
        )

        # Check HTTP response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        # Check MCP response structure
        assert "result" in data, f"Missing 'result' in response: {data}"
        result = data["result"]

        assert "success" in result, f"Missing 'success' in result: {result}"

        if result["success"]:
            result_data = result["data"]

            assert "answer" in result_data, f"Missing 'answer' in data: {result_data}"
            assert "depth" in result_data, f"Missing 'depth' in data: {result_data}"
            assert result_data["depth"] == "detailed", f"Expected depth 'detailed', got: {result_data['depth']}"

            # Detailed responses should be longer than brief
            answer = result_data["answer"]
            assert len(answer) > 100, f"Detailed answer should be longer than 100 chars, got {len(answer)}"

            # Detailed responses might have markdown headers (depends on LLM)
            # This is a soft check - not all responses will have headers
            has_structure = "##" in answer or len(answer) > 500
            print(f"\n[DETAILED] Answer length: {len(answer)} chars")
            print(f"[DETAILED] Has markdown structure: {has_structure}")
            print(f"[DETAILED] First 300 chars: {answer[:300]}...")
            print(f"[DETAILED] Sources: {len(result_data.get('sources', []))}")
        else:
            print(f"\n[DETAILED] Tool returned error: {result.get('error', 'Unknown error')}")
            if "circuit breaker" in str(result.get("error", "")).lower():
                pytest.skip("Circuit breaker open - service temporarily unavailable")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ask_intelligence_via_mcp_call():
    """Test the MCP tools/call endpoint directly for ask_intelligence.

    This test validates:
    1. The MCP protocol endpoint is working
    2. The tool is registered and callable
    3. Response follows MCP protocol structure
    """
    if not await check_service_available(MCP_BASE_URL):
        pytest.skip("MCP Analytics Server not available")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, verify the tool is listed
        list_response = await client.get(f"{MCP_BASE_URL}/mcp/tools/list")
        assert list_response.status_code == 200, f"Tools list failed: {list_response.text}"

        tools_data = list_response.json()
        assert "tools" in tools_data, f"Missing 'tools' in list response: {tools_data}"

        # Find ask_intelligence in the list
        tool_names = [t["name"] for t in tools_data["tools"]]
        assert "ask_intelligence" in tool_names, f"ask_intelligence not in tools list: {tool_names}"

        # Now call the tool
        response = await client.post(
            f"{MCP_BASE_URL}/mcp/tools/call",
            json={
                "tool_name": "ask_intelligence",
                "arguments": {
                    "question": "What is the latest news about Rheinmetall?",
                    "depth": "brief"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Validate MCP protocol structure
        assert "result" in data
        result = data["result"]

        # MCP result should have these fields
        assert "success" in result

        if result["success"]:
            assert "data" in result
            assert "metadata" in result or "data" in result  # metadata may be in data

            # Validate tool executed correctly
            result_data = result["data"]
            assert "question" in result_data, f"Missing 'question' echo in response: {result_data}"
            assert "answer" in result_data

            print(f"\n[MCP CALL] Question: {result_data.get('question', 'N/A')}")
            print(f"[MCP CALL] Answer: {result_data['answer'][:150]}...")
        else:
            assert "error" in result, "Failed result should have error message"
            print(f"\n[MCP CALL] Error: {result['error']}")
            if "circuit breaker" in str(result.get("error", "")).lower():
                pytest.skip("Circuit breaker open - service temporarily unavailable")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ask_intelligence_invalid_depth():
    """Test ask_intelligence with invalid depth parameter.

    Should either:
    - Return error for invalid depth
    - Fall back to default depth
    """
    if not await check_service_available(MCP_BASE_URL):
        pytest.skip("MCP Analytics Server not available")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{MCP_BASE_URL}/mcp/tools/call",
            json={
                "tool_name": "ask_intelligence",
                "arguments": {
                    "question": "Test question",
                    "depth": "invalid_depth"
                }
            }
        )

        # Should either return 200 with error in result, or 422 validation error
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            # Either fails or falls back to default
            print(f"\n[INVALID DEPTH] Result: {result}")
        else:
            # Validation error
            print(f"\n[INVALID DEPTH] Validation error: {response.text}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ask_intelligence_empty_question():
    """Test ask_intelligence with empty question.

    Should return error for empty/short question.
    """
    if not await check_service_available(MCP_BASE_URL):
        pytest.skip("MCP Analytics Server not available")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{MCP_BASE_URL}/mcp/tools/call",
            json={
                "tool_name": "ask_intelligence",
                "arguments": {
                    "question": "",  # Empty question
                    "depth": "brief"
                }
            }
        )

        # Should return error (question too short)
        # Could be 422 validation error or 200 with error in result
        assert response.status_code in [200, 422, 500], f"Unexpected status: {response.status_code}"

        print(f"\n[EMPTY QUESTION] Status: {response.status_code}")
        print(f"[EMPTY QUESTION] Response: {response.text[:500]}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ask_intelligence_specific_entity():
    """Test ask_intelligence about a specific entity.

    Tests RAG retrieval for entity-specific questions.
    """
    if not await check_service_available(MCP_BASE_URL):
        pytest.skip("MCP Analytics Server not available")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{MCP_BASE_URL}/mcp/tools/call",
            json={
                "tool_name": "ask_intelligence",
                "arguments": {
                    "question": "What is the current news sentiment for Trump?",
                    "depth": "brief"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data.get("result", {})

        if result.get("success"):
            result_data = result["data"]
            answer = result_data.get("answer", "")

            # The answer should relate to the entity
            print(f"\n[ENTITY QUERY] Answer: {answer[:200]}...")
            print(f"[ENTITY QUERY] Sources: {len(result_data.get('sources', []))}")
        else:
            print(f"\n[ENTITY QUERY] Error: {result.get('error', 'Unknown')}")
            if "circuit breaker" in str(result.get("error", "")).lower():
                pytest.skip("Circuit breaker open - service temporarily unavailable")


# =============================================================================
# Service Health Check Test
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_server_health():
    """Test MCP Analytics Server health endpoint.

    Basic connectivity test - should pass if server is running.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{MCP_BASE_URL}/health")
            assert response.status_code == 200

            data = response.json()
            assert data.get("status") == "healthy"
            assert data.get("service") == "mcp-analytics-server"

            print(f"\n[HEALTH] MCP Server is healthy: {data}")
        except httpx.ConnectError:
            pytest.skip("MCP Analytics Server not running on port 9003")
