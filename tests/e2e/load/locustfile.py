"""
Locust Load Testing Configuration
Simulates concurrent users interacting with the News MCP platform.
"""
from locust import HttpUser, task, between, TaskSet
import random
import json


class UserBehavior(TaskSet):
    """Simulates typical user behavior patterns."""

    def on_start(self):
        """Execute on user start - perform login."""
        self.login()

    def login(self):
        """Login and store authentication token."""
        # Register a unique user
        user_id = random.randint(100000, 999999)
        self.user_data = {
            "email": f"loadtest_{user_id}@example.com",
            "password": "Load123!@#",
            "username": f"loadtest_{user_id}",
            "full_name": f"Load Test User {user_id}"
        }

        # Register
        response = self.client.post(
            "/api/auth/register",
            json=self.user_data,
            name="Register User"
        )

        if response.status_code == 201:
            # Login
            login_data = {
                "username": self.user_data["email"],
                "password": self.user_data["password"]
            }
            response = self.client.post(
                "/api/auth/login",
                data=login_data,
                name="Login"
            )

            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
            else:
                self.token = None
                self.headers = {}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    def view_feeds(self):
        """View list of feeds."""
        if self.headers:
            self.client.get(
                "/api/feeds",
                headers=self.headers,
                name="View Feeds"
            )

    @task(2)
    def create_feed(self):
        """Create a new feed."""
        if self.headers:
            feed_urls = [
                "https://news.ycombinator.com/rss",
                "https://hnrss.org/frontpage",
                "https://www.reddit.com/r/technology/.rss"
            ]

            feed_data = {
                "url": random.choice(feed_urls),
                "name": f"Load Test Feed {random.randint(1, 1000)}",
                "category": random.choice(["technology", "news", "science"]),
                "fetch_interval": random.choice([1800, 3600, 7200])
            }

            self.client.post(
                "/api/feeds",
                json=feed_data,
                headers=self.headers,
                name="Create Feed"
            )

    @task(4)
    def search_articles(self):
        """Search for articles."""
        if self.headers:
            queries = ["AI", "technology", "security", "blockchain", "cloud"]

            self.client.get(
                "/api/search",
                params={"q": random.choice(queries), "limit": 10},
                headers=self.headers,
                name="Search Articles"
            )

    @task(2)
    def view_notifications(self):
        """View notifications."""
        if self.headers:
            self.client.get(
                "/api/notifications",
                headers=self.headers,
                name="View Notifications"
            )

    @task(1)
    def view_analytics(self):
        """View analytics dashboard."""
        if self.headers:
            self.client.get(
                "/api/analytics/dashboard",
                headers=self.headers,
                name="View Analytics"
            )

    @task(1)
    def fetch_articles(self):
        """Fetch articles from a feed."""
        if self.headers:
            # Get feeds first
            response = self.client.get(
                "/api/feeds",
                headers=self.headers,
                name="Get Feeds for Fetch"
            )

            if response.status_code == 200:
                feeds = response.json()
                if feeds and len(feeds) > 0:
                    feed_id = random.choice(feeds)["id"]
                    self.client.post(
                        f"/api/feeds/{feed_id}/fetch",
                        headers=self.headers,
                        name="Fetch Articles"
                    )


class WebsiteUser(HttpUser):
    """Simulates a user of the News MCP platform."""
    tasks = [UserBehavior]
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    host = "http://localhost:8000"  # Base URL


class AdminUser(HttpUser):
    """Simulates an admin user with different behavior patterns."""
    wait_time = between(2, 8)
    host = "http://localhost:8000"

    @task
    def admin_dashboard(self):
        """Access admin endpoints."""
        # This would require admin-specific endpoints
        pass


class APIUser(HttpUser):
    """Simulates API-only usage (no UI)."""
    wait_time = between(0.5, 2)
    host = "http://localhost:8000"

    @task(5)
    def api_health_check(self):
        """Check health endpoints."""
        services = [8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007]
        port = random.choice(services)

        self.client.get(
            f"http://localhost:{port}/health",
            name="Health Check"
        )
