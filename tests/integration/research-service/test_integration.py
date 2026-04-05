#!/usr/bin/env python3
"""Integration test for Research Service specialized functions."""

import httpx
import json
import asyncio


async def test_functions_endpoint():
    """Test the /functions endpoint without auth (should work)."""
    async with httpx.AsyncClient() as client:
        # Test health
        response = await client.get("http://localhost:8003/health")
        print(f"Health Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        print()

        # Test functions list (without auth for now)
        try:
            response = await client.get("http://localhost:8003/api/v1/templates/functions")
            print(f"\nFunctions List Status: {response.status_code}")
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"Response: {response.text}")
                print("\nNote: Endpoint requires authentication. This is expected.")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_functions_endpoint())
