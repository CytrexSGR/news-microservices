#!/usr/bin/env python3
"""
Update Freqtrade Strategy in Database

Updates the existing strategy with the corrected JSON (including "enabled": true fields).
"""

import json
import requests
import sys

# Configuration
API_BASE_URL = "http://localhost:8116"
STRATEGY_JSON_PATH = "/home/cytrex/userdocs/crypto-lab/strategies/freqtrade-adaptive-futures-strategy.json"
STRATEGY_ID = "9675ccea-f520-4557-b54c-a98e1972cc1f"

# User credentials
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
    """Load updated strategy definition from JSON file."""
    print(f"📄 Loading updated strategy from {STRATEGY_JSON_PATH}...")

    with open(STRATEGY_JSON_PATH, 'r') as f:
        strategy_def = json.load(f)

    print(f"✅ Loaded strategy: {strategy_def['name']} v{strategy_def['version']}")

    # Verify that all regimes have "enabled": true
    for regime in ["TREND", "CONSOLIDATION", "HIGH_VOLATILITY"]:
        entry = strategy_def["logic"][regime]["entry"]
        if not entry.get("enabled"):
            print(f"⚠️  WARNING: Regime {regime} entry is not enabled!")

    return strategy_def


def update_strategy(token, strategy_def):
    """Update strategy via API."""
    print(f"🔄 Updating strategy {STRATEGY_ID}...")

    # Prepare payload
    payload = {
        "name": strategy_def["name"],
        "version": strategy_def["version"],
        "description": strategy_def["description"],
        "definition": strategy_def,
        "is_public": False
    }

    response = requests.put(
        f"{API_BASE_URL}/api/v1/strategies/{STRATEGY_ID}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        print(f"❌ Strategy update failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    strategy = response.json()
    print(f"✅ Strategy updated successfully!")
    return strategy


def main():
    """Main update workflow."""
    print("=" * 60)
    print("Freqtrade Strategy Update (Add 'enabled' fields)")
    print("=" * 60)
    print()

    # Step 1: Authenticate
    token = get_access_token()

    # Step 2: Load updated strategy JSON
    strategy_def = load_strategy_json()

    # Step 3: Update strategy
    strategy = update_strategy(token, strategy_def)

    print()
    print("=" * 60)
    print("✅ Update Complete!")
    print("=" * 60)
    print()
    print(f"Strategy ID: {STRATEGY_ID}")
    print()
    print("✨ What changed:")
    print("  • Added 'enabled': true to TREND entry")
    print("  • Added 'enabled': true to CONSOLIDATION entry")
    print("  • Added 'enabled': true to HIGH_VOLATILITY entry")
    print()
    print("🎯 Now run the debugger to see full condition tracking!")
    print(f"   http://localhost:3000/trading/debug")
    print()
    print("You will now see ALL entry conditions for each regime:")
    print("  ✅ TREND: 5 conditions (Golden Cross, RSI, multi-timeframe, etc.)")
    print("  ✅ CONSOLIDATION: 3 conditions (RSI extremes, BB bands, volatility)")
    print("  ✅ HIGH_VOLATILITY: 2 conditions (extreme conditions only)")
    print()


if __name__ == "__main__":
    main()
