#!/usr/bin/env python3
"""
n8n JWT Authentication Helper
==============================

Stable authentication for n8n API using JWT tokens instead of API keys.

Features:
- Login with username/password to get JWT token
- Automatic token refresh (recommended every 12-24h)
- Token caching to avoid repeated logins
- Clean API for workflow operations

Usage:
    from scripts.n8n_jwt_auth import N8nAuth

    # Login and get authenticated session
    auth = N8nAuth(base_url="http://localhost:5678", email="andreas@test.com", password="Aug2012#")
    auth.login()

    # Use for API calls
    workflows = auth.get("api/v1/workflows")
    auth.put("api/v1/workflows/123", json={...})
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any


class N8nAuth:
    """JWT-based authentication for n8n API"""

    TOKEN_CACHE_FILE = Path.home() / ".n8n_jwt_token"
    TOKEN_VALIDITY_HOURS = 12

    def __init__(self, base_url: str = "http://localhost:5678", email: str = "andreas@test.com", password: str = "Aug2012#"):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Try to load cached token
        self._load_cached_token()

    def _load_cached_token(self):
        """Load token from cache file if still valid"""
        if not self.TOKEN_CACHE_FILE.exists():
            return

        try:
            with open(self.TOKEN_CACHE_FILE, 'r') as f:
                data = json.load(f)
                expires_at = datetime.fromisoformat(data['expires_at'])

                # Check if token is still valid (with 1 hour safety margin)
                if datetime.now() < expires_at - timedelta(hours=1):
                    self.token = data['token']
                    self.token_expires_at = expires_at
                    print(f"✅ Loaded cached token (valid until {expires_at.strftime('%H:%M:%S')})")
                else:
                    print(f"⚠️  Cached token expired, will login again")
        except Exception as e:
            print(f"⚠️  Failed to load cached token: {e}")

    def _save_token(self, token: str):
        """Save token to cache file"""
        self.token = token
        self.token_expires_at = datetime.now() + timedelta(hours=self.TOKEN_VALIDITY_HOURS)

        try:
            with open(self.TOKEN_CACHE_FILE, 'w') as f:
                json.dump({
                    'token': token,
                    'expires_at': self.token_expires_at.isoformat()
                }, f, indent=2)
            os.chmod(self.TOKEN_CACHE_FILE, 0o600)  # Secure file permissions
            print(f"💾 Token cached (valid until {self.token_expires_at.strftime('%H:%M:%S')})")
        except Exception as e:
            print(f"⚠️  Failed to cache token: {e}")

    def login(self) -> str:
        """
        Login to n8n and get JWT token

        Returns:
            JWT token string
        """
        # Check if we have a valid cached token
        if self.token and self.token_expires_at:
            if datetime.now() < self.token_expires_at - timedelta(hours=1):
                print(f"✅ Using cached token")
                return self.token

        print(f"🔐 Logging in to n8n as {self.email}...")

        try:
            resp = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": self.email,
                    "password": self.password
                },
                timeout=10
            )

            if resp.status_code != 200:
                raise Exception(f"Login failed: HTTP {resp.status_code} - {resp.text}")

            data = resp.json()
            token = data.get('token')

            if not token:
                raise Exception(f"No token in response: {data}")

            self._save_token(token)
            print(f"✅ Login successful!")
            return token

        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to n8n at {self.base_url}. Is it running?")
        except Exception as e:
            raise Exception(f"Login failed: {e}")

    def ensure_authenticated(self):
        """Ensure we have a valid token, login if necessary"""
        if not self.token or not self.token_expires_at:
            self.login()
        elif datetime.now() >= self.token_expires_at - timedelta(hours=1):
            print("⚠️  Token expiring soon, refreshing...")
            self.login()

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        self.ensure_authenticated()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated GET request"""
        self.ensure_authenticated()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return requests.get(url, headers=self._get_headers(), **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated POST request"""
        self.ensure_authenticated()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return requests.post(url, headers=self._get_headers(), **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated PUT request"""
        self.ensure_authenticated()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return requests.put(url, headers=self._get_headers(), **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated DELETE request"""
        self.ensure_authenticated()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return requests.delete(url, headers=self._get_headers(), **kwargs)


# Convenience function for quick access
def get_n8n_session() -> N8nAuth:
    """Get authenticated n8n session"""
    auth = N8nAuth()
    auth.login()
    return auth


if __name__ == "__main__":
    """Test the authentication"""
    import sys

    print("=== n8n JWT Authentication Test ===\n")

    try:
        # Create auth session
        auth = N8nAuth()
        auth.login()

        # Test 1: List workflows
        print("\n📋 Test 1: List workflows")
        resp = auth.get("api/v1/workflows?limit=3")
        if resp.status_code == 200:
            workflows = resp.json()
            print(f"✅ SUCCESS - Got {len(workflows['data'])} workflows")
            for wf in workflows['data']:
                print(f"   - {wf['name']} (ID: {wf['id']})")
        else:
            print(f"❌ FAILED - HTTP {resp.status_code}")
            print(resp.text)
            sys.exit(1)

        # Test 2: Get specific workflow
        if workflows['data']:
            wf_id = workflows['data'][0]['id']
            print(f"\n🔍 Test 2: Get workflow {wf_id}")
            resp = auth.get(f"api/v1/workflows/{wf_id}")
            if resp.status_code == 200:
                wf = resp.json()
                print(f"✅ SUCCESS - Got workflow: {wf['name']}")
                print(f"   Nodes: {len(wf['nodes'])}")
                print(f"   Active: {wf.get('active', False)}")
            else:
                print(f"❌ FAILED - HTTP {resp.status_code}")
                sys.exit(1)

        print("\n🎉 All tests passed!")
        print(f"\n💡 Token valid until: {auth.token_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💡 Token cached at: {auth.TOKEN_CACHE_FILE}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
