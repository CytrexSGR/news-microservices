#!/usr/bin/env python3
"""
Import Freqtrade Adaptive Futures Strategy into Database

Loads the strategy JSON from userdocs and creates it via the API.
"""

import json
import requests
import sys
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8116"
STRATEGY_JSON_PATH = "/home/cytrex/userdocs/crypto-lab/strategies/freqtrade-adaptive-futures-strategy.json"

# User credentials (from CLAUDE.md)
USERNAME = "andreas"
PASSWORD = "Aug2012#"


def get_access_token():
    """Authenticate and get JWT token."""
    print("🔐 Authenticating...")
    response = requests.post(
        f"http://localhost:8100/api/v1/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )

    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.text}")
        sys.exit(1)

    token = response.json()["access_token"]
    print("✅ Authentication successful")
    return token


def load_strategy_json():
    """Load strategy definition from JSON file."""
    print(f"📄 Loading strategy from {STRATEGY_JSON_PATH}...")

    with open(STRATEGY_JSON_PATH, 'r') as f:
        strategy_def = json.load(f)

    print(f"✅ Loaded strategy: {strategy_def['name']} v{strategy_def['version']}")
    return strategy_def


def create_strategy(token, strategy_def):
    """Create strategy via API."""
    print("🚀 Creating strategy via API...")

    # Prepare payload in StrategyCreate format
    payload = {
        "name": strategy_def["name"],
        "version": strategy_def["version"],
        "description": strategy_def["description"],
        "definition": strategy_def,  # The entire JSON becomes the definition
        "is_public": False
    }

    response = requests.post(
        f"{API_BASE_URL}/api/v1/strategies/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 409:
        print("⚠️  Strategy already exists. Fetching existing strategy...")
        # Get existing strategy
        list_response = requests.get(
            f"{API_BASE_URL}/api/v1/strategies/",
            headers={"Authorization": f"Bearer {token}"}
        )

        if list_response.status_code == 200:
            response_data = list_response.json()
            # Handle both list and dict response formats
            strategies = response_data if isinstance(response_data, list) else response_data.get("items", response_data.get("strategies", []))

            for s in strategies:
                if s["name"] == strategy_def["name"] and s["version"] == strategy_def["version"]:
                    print(f"✅ Found existing strategy with ID: {s['id']}")
                    return s["id"]

        print("❌ Could not find existing strategy")
        sys.exit(1)

    elif response.status_code != 201:
        print(f"❌ Strategy creation failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    strategy = response.json()
    strategy_id = strategy["id"]
    print(f"✅ Strategy created with ID: {strategy_id}")
    return strategy_id


def main():
    """Main import workflow."""
    print("=" * 60)
    print("Freqtrade Adaptive Futures Strategy Import")
    print("=" * 60)
    print()

    # Step 1: Authenticate
    token = get_access_token()

    # Step 2: Load strategy JSON
    strategy_def = load_strategy_json()

    # Step 3: Create strategy
    strategy_id = create_strategy(token, strategy_def)

    print()
    print("=" * 60)
    print("✅ Import Complete!")
    print("=" * 60)
    print()
    print(f"Strategy ID: {strategy_id}")
    print()
    print("🎯 Next Steps:")
    print(f"1. Open http://localhost:3000/trading/debug")
    print(f"2. The strategy should be pre-selected (or select it from dropdown)")
    print(f"3. Click 'Run Debug' to see detailed condition tracking")
    print()
    print("You will now see:")
    print("  ✅ All entry conditions for each regime")
    print("  ✅ Which conditions passed/failed")
    print("  ✅ Actual indicator values at each decision point")
    print("  ✅ Complete transparency into strategy behavior")
    print()


if __name__ == "__main__":
    main()
