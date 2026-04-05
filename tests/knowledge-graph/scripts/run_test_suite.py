#!/usr/bin/env python3
"""
Knowledge Graph Test Suite Runner

Runs all test articles through the content-analysis-service and stores results.

Usage:
    export CONTENT_ANALYSIS_API_URL="http://localhost:8102/api/v1"
    export AUTH_TOKEN="your-jwt-token"
    python scripts/run_test_suite.py

Output:
    Creates test-results/ directory with same structure as articles/
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


# Configuration from environment
API_URL = os.getenv("CONTENT_ANALYSIS_API_URL", "http://localhost:8102/api/v1")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
BASE_DIR = Path(__file__).parent.parent
ARTICLES_DIR = BASE_DIR / "test-data" / "articles"
RESULTS_DIR = BASE_DIR / "test-results"


class TestRunner:
    """Orchestrates test execution across all categories."""

    def __init__(self):
        self.api_url = API_URL
        self.headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        self.results_dir = RESULTS_DIR
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "categories": {}
        }

    def setup_results_directory(self):
        """Create results directory structure."""
        self.results_dir.mkdir(exist_ok=True)
        for category in ["category-a", "category-b", "category-c", "category-d"]:
            (self.results_dir / category).mkdir(exist_ok=True)
        print(f"✓ Results directory ready: {self.results_dir}")

    def load_article(self, article_path: Path) -> Dict[str, Any]:
        """Load article JSON from file."""
        with open(article_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def call_analysis_service(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call content-analysis-service TEST API.

        POST /api/v1/test/analyze
        {
            "article_id": "uuid",
            "content": "text",
            "title": "title",
            "extract_relationships": true
        }
        """
        payload = {
            "article_id": article["article_id"],
            "content": article["content"],
            "title": article.get("title", ""),
            "extract_relationships": True
        }

        try:
            response = requests.post(
                f"{self.api_url}/test/analyze",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None),
                "timestamp": datetime.utcnow().isoformat()
            }

    def save_result(self, result: Dict[str, Any], category: str, article_id: str):
        """Save API response to results directory."""
        result_file = self.results_dir / category / f"{article_id}-result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def process_article(self, article_path: Path, category: str) -> bool:
        """Process a single article through the pipeline."""
        article_id = article_path.stem

        print(f"\n{'='*60}")
        print(f"Processing: {category}/{article_id}")
        print(f"{'='*60}")

        # Load article
        try:
            article = self.load_article(article_path)
            print(f"✓ Loaded article: {article['title']}")
            print(f"  Content length: {len(article['content'])} chars")
        except Exception as e:
            print(f"✗ Failed to load article: {e}")
            return False

        # Call API
        print(f"→ Calling analysis service...")
        result = self.call_analysis_service(article)

        if result["success"]:
            print(f"✓ Analysis completed (status {result['status_code']})")

            # Extract key metrics from response
            data = result["data"]
            if "relationships" in data:
                rel_count = len(data.get("relationships", []))
                print(f"  Relationships extracted: {rel_count}")

                if rel_count > 0:
                    avg_conf = sum(r.get("confidence", 0) for r in data["relationships"]) / rel_count
                    print(f"  Average confidence: {avg_conf:.2f}")

            if "entities" in data:
                print(f"  Entities extracted: {len(data.get('entities', []))}")
        else:
            print(f"✗ Analysis failed: {result['error']}")

        # Save result
        self.save_result(result, category, article_id)
        print(f"✓ Result saved to {category}/{article_id}-result.json")

        return result["success"]

    def run_category(self, category: str) -> Dict[str, Any]:
        """Run all tests for a specific category."""
        category_dir = ARTICLES_DIR / category

        if not category_dir.exists():
            print(f"⚠ Category {category} not found, skipping")
            return {"total": 0, "success": 0, "failed": 0}

        articles = sorted(category_dir.glob("*.json"))

        print(f"\n{'#'*60}")
        print(f"# Category: {category.upper()}")
        print(f"# Articles: {len(articles)}")
        print(f"{'#'*60}")

        category_stats = {"total": 0, "success": 0, "failed": 0, "articles": []}

        for article_path in articles:
            category_stats["total"] += 1
            success = self.process_article(article_path, category)

            if success:
                category_stats["success"] += 1
            else:
                category_stats["failed"] += 1

            category_stats["articles"].append({
                "article_id": article_path.stem,
                "success": success
            })

            # Rate limiting: 1 second between requests
            time.sleep(1)

        return category_stats

    def run_all(self):
        """Run complete test suite."""
        print("\n" + "="*60)
        print("KNOWLEDGE GRAPH TEST SUITE")
        print("="*60)
        print(f"API URL: {self.api_url}")
        print(f"Articles directory: {ARTICLES_DIR}")
        print(f"Results directory: {self.results_dir}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Setup
        self.setup_results_directory()

        # Run each category
        categories = ["category-a", "category-b", "category-c", "category-d"]

        for category in categories:
            category_stats = self.run_category(category)
            self.stats["categories"][category] = category_stats
            self.stats["total"] += category_stats["total"]
            self.stats["success"] += category_stats["success"]
            self.stats["failed"] += category_stats["failed"]

        # Summary
        self.print_summary()
        self.save_stats()

    def print_summary(self):
        """Print execution summary."""
        print("\n" + "="*60)
        print("TEST SUITE SUMMARY")
        print("="*60)

        print(f"\nOverall:")
        print(f"  Total articles: {self.stats['total']}")
        print(f"  Successful: {self.stats['success']} ({self.stats['success']/self.stats['total']*100:.1f}%)")
        print(f"  Failed: {self.stats['failed']} ({self.stats['failed']/self.stats['total']*100:.1f}%)")

        print(f"\nBy Category:")
        for category, stats in self.stats["categories"].items():
            success_rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"  {category}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

        print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

    def save_stats(self):
        """Save execution statistics."""
        stats_file = self.results_dir / "execution_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
        print(f"\n✓ Execution stats saved to {stats_file}")


def main():
    """Main entry point."""
    # Validate environment
    if not AUTH_TOKEN:
        print("⚠ Note: AUTH_TOKEN not set. Using test endpoint (no auth required).")

    # Run test suite
    runner = TestRunner()
    runner.run_all()

    return 0


if __name__ == "__main__":
    sys.exit(main())
