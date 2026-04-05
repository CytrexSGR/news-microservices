"""
Integration tests for Knowledge-Graph Service.

Tests complete workflows involving multiple services:
- FMP Service → Knowledge-Graph → Neo4j
- End-to-end data pipelines
- Service-to-service communication
- Performance benchmarks

Requirements:
- Docker Compose stack running
- All services healthy (FMP, Knowledge-Graph, Neo4j)
- Network connectivity

Usage:
    pytest tests/integration/ -v -m integration
    pytest tests/integration/ -v -m "integration and not slow"
    pytest tests/integration/ -v -m performance
"""
