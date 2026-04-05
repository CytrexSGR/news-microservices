#!/usr/bin/env python3
"""
Knowledge Graph Metrics Calculator

Compares test results against ground truth and calculates Precision, Recall, F1.

Usage:
    python scripts/calculate_metrics.py

Input:
    - test-results/ directory (from run_test_suite.py)
    - test-data/ground-truth/ directory

Output:
    - summary_report.json with all calculated metrics
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set
from collections import defaultdict


BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "test-results"
GROUND_TRUTH_DIR = BASE_DIR / "test-data" / "ground-truth"
REPORT_FILE = BASE_DIR / "test-results" / "summary_report.json"


class MetricsCalculator:
    """Calculates precision, recall, and F1 scores for relationship extraction."""

    def __init__(self):
        self.category_metrics = defaultdict(lambda: {
            "articles": [],
            "total_tp": 0,
            "total_fp": 0,
            "total_fn": 0,
            "avg_precision": 0.0,
            "avg_recall": 0.0,
            "avg_f1": 0.0,
            "avg_confidence": 0.0
        })
        self.overall_metrics = {
            "total_tp": 0,
            "total_fp": 0,
            "total_fn": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0
        }
        self.best_articles = []  # For Hall of Fame
        self.worst_articles = []  # For Hall of Shame

    def normalize_triplet(self, triplet: List[str]) -> Tuple[str, str, str]:
        """
        Normalize a triplet for comparison.

        - Lowercase entities
        - Strip whitespace
        - Normalize relationship type
        """
        if len(triplet) != 3:
            return ("", "", "")

        entity1 = triplet[0].lower().strip()
        relationship = triplet[1].lower().strip().replace("_", " ")
        entity2 = triplet[2].lower().strip()

        return (entity1, relationship, entity2)

    def extract_triplets_from_result(self, result: Dict[str, Any]) -> Set[Tuple[str, str, str]]:
        """
        Extract normalized triplets from API result.

        Result format:
        {
            "data": {
                "relationships": [
                    {
                        "entity1": "...",
                        "type": "works_for",
                        "entity2": "...",
                        "confidence": 0.95
                    }
                ]
            }
        }
        """
        triplets = set()

        if not result.get("success"):
            return triplets

        relationships = result.get("data", {}).get("relationships", [])

        for rel in relationships:
            triplet = [
                rel.get("entity1", ""),
                rel.get("type", ""),
                rel.get("entity2", "")
            ]
            normalized = self.normalize_triplet(triplet)
            if normalized != ("", "", ""):
                triplets.add(normalized)

        return triplets

    def extract_triplets_from_ground_truth(self, ground_truth: Dict[str, Any]) -> Set[Tuple[str, str, str]]:
        """
        Extract normalized triplets from ground truth.

        Format:
        {
            "ground_truth_relationships": [
                {
                    "triplet": ["Entity1", "relationship", "Entity2"],
                    "mandatory": true
                }
            ]
        }
        """
        triplets = set()

        for rel in ground_truth.get("ground_truth_relationships", []):
            # Only include mandatory relationships in ground truth set
            if rel.get("mandatory", True):
                triplet = rel.get("triplet", [])
                normalized = self.normalize_triplet(triplet)
                if normalized != ("", "", ""):
                    triplets.add(normalized)

        return triplets

    def calculate_article_metrics(
        self,
        extracted: Set[Tuple[str, str, str]],
        ground_truth: Set[Tuple[str, str, str]]
    ) -> Dict[str, Any]:
        """
        Calculate TP, FP, FN, Precision, Recall, F1 for a single article.

        TP: Triplets in both extracted and ground_truth
        FP: Triplets in extracted but not in ground_truth
        FN: Triplets in ground_truth but not in extracted
        """
        tp_set = extracted & ground_truth
        fp_set = extracted - ground_truth
        fn_set = ground_truth - extracted

        tp = len(tp_set)
        fp = len(fp_set)
        fn = len(fn_set)

        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp_list": list(tp_set),
            "fp_list": list(fp_set),
            "fn_list": list(fn_set)
        }

    def load_result(self, result_path: Path) -> Dict[str, Any]:
        """Load result JSON."""
        with open(result_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_ground_truth(self, article_id: str) -> Dict[str, Any]:
        """Load ground truth JSON."""
        gt_path = GROUND_TRUTH_DIR / f"{article_id}-ground-truth.json"
        if not gt_path.exists():
            return {}
        with open(gt_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_average_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate average confidence from result."""
        if not result.get("success"):
            return 0.0

        relationships = result.get("data", {}).get("relationships", [])
        if not relationships:
            return 0.0

        confidences = [r.get("confidence", 0.0) for r in relationships]
        return sum(confidences) / len(confidences)

    def process_article(self, result_path: Path, category: str) -> Dict[str, Any]:
        """Process a single article result."""
        article_id = result_path.stem.replace("-result", "")

        # Load files
        result = self.load_result(result_path)
        ground_truth = self.load_ground_truth(article_id)

        if not ground_truth:
            print(f"⚠ No ground truth for {article_id}, skipping")
            return None

        # Extract triplets
        extracted = self.extract_triplets_from_result(result)
        expected = self.extract_triplets_from_ground_truth(ground_truth)

        # Calculate metrics
        metrics = self.calculate_article_metrics(extracted, expected)
        metrics["article_id"] = article_id
        metrics["category"] = category
        metrics["avg_confidence"] = self.get_average_confidence(result)
        metrics["extracted_count"] = len(extracted)
        metrics["expected_count"] = len(expected)

        print(f"  {article_id}: P={metrics['precision']:.2f} R={metrics['recall']:.2f} F1={metrics['f1']:.2f}")

        return metrics

    def process_category(self, category: str) -> Dict[str, Any]:
        """Process all articles in a category."""
        category_dir = RESULTS_DIR / category

        if not category_dir.exists():
            print(f"⚠ Category {category} results not found")
            return None

        print(f"\nProcessing {category}:")

        result_files = sorted(category_dir.glob("*-result.json"))
        category_data = self.category_metrics[category]

        for result_path in result_files:
            article_metrics = self.process_article(result_path, category)

            if article_metrics:
                category_data["articles"].append(article_metrics)
                category_data["total_tp"] += article_metrics["tp"]
                category_data["total_fp"] += article_metrics["fp"]
                category_data["total_fn"] += article_metrics["fn"]

        # Calculate category averages
        if category_data["articles"]:
            n = len(category_data["articles"])
            category_data["avg_precision"] = sum(a["precision"] for a in category_data["articles"]) / n
            category_data["avg_recall"] = sum(a["recall"] for a in category_data["articles"]) / n
            category_data["avg_f1"] = sum(a["f1"] for a in category_data["articles"]) / n
            category_data["avg_confidence"] = sum(a["avg_confidence"] for a in category_data["articles"]) / n

            # Calculate overall precision/recall/F1 for category
            tp = category_data["total_tp"]
            fp = category_data["total_fp"]
            fn = category_data["total_fn"]

            category_data["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            category_data["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            category_data["f1"] = 2 * (category_data["precision"] * category_data["recall"]) / \
                                  (category_data["precision"] + category_data["recall"]) \
                                  if (category_data["precision"] + category_data["recall"]) > 0 else 0.0

        return category_data

    def calculate_overall_metrics(self):
        """Calculate overall metrics across all categories."""
        total_tp = sum(cat["total_tp"] for cat in self.category_metrics.values())
        total_fp = sum(cat["total_fp"] for cat in self.category_metrics.values())
        total_fn = sum(cat["total_fn"] for cat in self.category_metrics.values())

        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        self.overall_metrics = {
            "total_tp": total_tp,
            "total_fp": total_fp,
            "total_fn": total_fn,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }

    def identify_best_and_worst(self):
        """Identify top 3 best and worst performing articles."""
        all_articles = []

        for category_data in self.category_metrics.values():
            all_articles.extend(category_data["articles"])

        # Sort by F1 score
        sorted_by_f1 = sorted(all_articles, key=lambda a: a["f1"], reverse=True)

        # Best: Top 3 with F1 > 0
        self.best_articles = [a for a in sorted_by_f1 if a["f1"] > 0][:3]

        # Worst: Bottom 3 (or articles with most FP)
        sorted_by_fp = sorted(all_articles, key=lambda a: a["fp"], reverse=True)
        self.worst_articles = sorted_by_fp[:3]

    def run(self):
        """Run complete metrics calculation."""
        print("="*60)
        print("KNOWLEDGE GRAPH METRICS CALCULATION")
        print("="*60)

        # Process each category
        categories = ["category-a", "category-b", "category-c", "category-d"]

        for category in categories:
            self.process_category(category)

        # Calculate overall metrics
        self.calculate_overall_metrics()

        # Identify best/worst
        self.identify_best_and_worst()

        # Print summary
        self.print_summary()

        # Save report
        self.save_report()

    def print_summary(self):
        """Print summary to console."""
        print("\n" + "="*60)
        print("METRICS SUMMARY")
        print("="*60)

        print("\nOverall Performance:")
        print(f"  Precision: {self.overall_metrics['precision']:.2%}")
        print(f"  Recall:    {self.overall_metrics['recall']:.2%}")
        print(f"  F1 Score:  {self.overall_metrics['f1']:.2%}")
        print(f"  TP: {self.overall_metrics['total_tp']}, "
              f"FP: {self.overall_metrics['total_fp']}, "
              f"FN: {self.overall_metrics['total_fn']}")

        print("\nBy Category:")
        for category, data in sorted(self.category_metrics.items()):
            print(f"\n  {category}:")
            print(f"    Precision: {data['precision']:.2%}")
            print(f"    Recall:    {data['recall']:.2%}")
            print(f"    F1 Score:  {data['f1']:.2%}")
            print(f"    Avg Confidence: {data['avg_confidence']:.2f}")
            print(f"    Articles: {len(data['articles'])}")

        print("\n🏆 Hall of Fame (Top 3):")
        for i, article in enumerate(self.best_articles, 1):
            print(f"  {i}. {article['article_id']} (F1: {article['f1']:.2%})")

        print("\n⚠ Hall of Shame (Most FP):")
        for i, article in enumerate(self.worst_articles, 1):
            print(f"  {i}. {article['article_id']} (FP: {article['fp']}, F1: {article['f1']:.2%})")

    def save_report(self):
        """Save complete report to JSON."""
        report = {
            "overall": self.overall_metrics,
            "by_category": dict(self.category_metrics),
            "hall_of_fame": self.best_articles,
            "hall_of_shame": self.worst_articles,
            "generated_at": Path(__file__).stem
        }

        REPORT_FILE.parent.mkdir(exist_ok=True)
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Report saved to {REPORT_FILE}")


def main():
    """Main entry point."""
    if not RESULTS_DIR.exists():
        print("✗ Results directory not found. Run run_test_suite.py first.")
        return 1

    calculator = MetricsCalculator()
    calculator.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
