"""Pytest configuration for integration tests.

These tests call the actual running services, so they don't need mocked clients.
"""

import pytest
import pytest_asyncio


# Configure pytest-asyncio mode
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require running services)"
    )


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"
