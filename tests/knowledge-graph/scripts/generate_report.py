#!/usr/bin/env python3
"""
Knowledge Graph HTML Report Generator

Creates a clean HTML report from summary_report.json.

Usage:
    python scripts/generate_report.py

Input:
    test-results/summary_report.json

Output:
    test-results/test_report.html
"""

import sys
import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).parent.parent
REPORT_JSON = BASE_DIR / "test-results" / "summary_report.json"
REPORT_HTML = BASE_DIR / "test-results" / "test_report.html"


class ReportGenerator:
    """Generates HTML report from metrics."""

    def __init__(self):
        self.data = None

    def load_data(self):
        """Load summary_report.json."""
        if not REPORT_JSON.exists():
            print(f"✗ {REPORT_JSON} not found. Run calculate_metrics.py first.")
            return False

        with open(REPORT_JSON, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        return True

    def percentage_color(self, value: float) -> str:
        """Return color class based on percentage value."""
        if value >= 0.90:
            return "excellent"
        elif value >= 0.75:
            return "good"
        elif value >= 0.60:
            return "acceptable"
        else:
            return "poor"

    def format_percentage(self, value: float) -> str:
        """Format float as percentage."""
        return f"{value * 100:.1f}%"

    def generate_html(self) -> str:
        """Generate complete HTML report."""
        overall = self.data["overall"]
        by_category = self.data["by_category"]
        hall_of_fame = self.data.get("hall_of_fame", [])
        hall_of_shame = self.data.get("hall_of_shame", [])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Graph Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 40px;
        }}

        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}

        h2 {{
            color: #34495e;
            margin: 30px 0 15px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #ecf0f1;
        }}

        .metadata {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
            font-size: 0.9em;
        }}

        .overall-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .metric-card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
            color: white;
        }}

        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}

        .metric-card .subvalue {{
            font-size: 0.8em;
            opacity: 0.8;
            margin-top: 5px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        thead {{
            background: #34495e;
            color: white;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}

        tbody tr:hover {{
            background: #f8f9fa;
        }}

        .excellent {{ color: #27ae60; font-weight: bold; }}
        .good {{ color: #2ecc71; font-weight: bold; }}
        .acceptable {{ color: #f39c12; font-weight: bold; }}
        .poor {{ color: #e74c3c; font-weight: bold; }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-a {{ background: #d4edda; color: #155724; }}
        .badge-b {{ background: #fff3cd; color: #856404; }}
        .badge-c {{ background: #f8d7da; color: #721c24; }}
        .badge-d {{ background: #e7e7e7; color: #383d41; }}

        .hall-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 30px 0;
        }}

        .hall-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
        }}

        .hall-card h3 {{
            margin-bottom: 15px;
            color: #2c3e50;
        }}

        .hall-fame h3 {{
            color: #27ae60;
        }}

        .hall-shame h3 {{
            color: #e74c3c;
        }}

        .hall-item {{
            background: white;
            padding: 12px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }}

        .hall-fame .hall-item {{
            border-left-color: #27ae60;
        }}

        .hall-shame .hall-item {{
            border-left-color: #e74c3c;
        }}

        .hall-item .rank {{
            font-weight: bold;
            color: #7f8c8d;
        }}

        .hall-item .article-id {{
            font-weight: 600;
            color: #2c3e50;
        }}

        .hall-item .score {{
            float: right;
            font-weight: bold;
        }}

        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Knowledge Graph Test Report</h1>

        <div class="metadata">
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
            <strong>Test Suite:</strong> Knowledge Graph Relationship Extraction |
            <strong>Categories:</strong> A (Simple), B (Complex), C (Ambiguous), D (Negative Examples)
        </div>

        <h2>Overall Performance</h2>
        <div class="overall-metrics">
            <div class="metric-card">
                <h3>Precision</h3>
                <div class="value">{self.format_percentage(overall['precision'])}</div>
                <div class="subvalue">True Positives / (TP + FP)</div>
            </div>
            <div class="metric-card">
                <h3>Recall</h3>
                <div class="value">{self.format_percentage(overall['recall'])}</div>
                <div class="subvalue">True Positives / (TP + FN)</div>
            </div>
            <div class="metric-card">
                <h3>F1 Score</h3>
                <div class="value">{self.format_percentage(overall['f1'])}</div>
                <div class="subvalue">Harmonic Mean of P & R</div>
            </div>
        </div>

        <div class="metadata">
            <strong>Confusion Matrix:</strong>
            TP: {overall['total_tp']} |
            FP: {overall['total_fp']} |
            FN: {overall['total_fn']}
        </div>

        <h2>Performance by Category</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Articles</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1 Score</th>
                    <th>Avg Confidence</th>
                    <th>TP / FP / FN</th>
                </tr>
            </thead>
            <tbody>
"""

        # Category rows
        for category in ["category-a", "category-b", "category-c", "category-d"]:
            if category not in by_category:
                continue

            cat_data = by_category[category]
            badge_class = category.split("-")[1]

            precision_class = self.percentage_color(cat_data['precision'])
            recall_class = self.percentage_color(cat_data['recall'])
            f1_class = self.percentage_color(cat_data['f1'])

            html += f"""
                <tr>
                    <td><span class="badge badge-{badge_class}">{category.upper()}</span></td>
                    <td>{len(cat_data['articles'])}</td>
                    <td class="{precision_class}">{self.format_percentage(cat_data['precision'])}</td>
                    <td class="{recall_class}">{self.format_percentage(cat_data['recall'])}</td>
                    <td class="{f1_class}">{self.format_percentage(cat_data['f1'])}</td>
                    <td>{cat_data['avg_confidence']:.2f}</td>
                    <td>{cat_data['total_tp']} / {cat_data['total_fp']} / {cat_data['total_fn']}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>

        <h2>Highlights</h2>
        <div class="hall-section">
            <div class="hall-card hall-fame">
                <h3>🏆 Hall of Fame (Top 3 F1 Scores)</h3>
"""

        # Hall of Fame
        for i, article in enumerate(hall_of_fame, 1):
            html += f"""
                <div class="hall-item">
                    <span class="rank">#{i}</span>
                    <span class="article-id">{article['article_id']}</span>
                    <span class="score excellent">F1: {self.format_percentage(article['f1'])}</span>
                    <div style="font-size: 0.85em; margin-top: 5px; color: #7f8c8d;">
                        P: {self.format_percentage(article['precision'])} |
                        R: {self.format_percentage(article['recall'])} |
                        TP: {article['tp']} / FP: {article['fp']} / FN: {article['fn']}
                    </div>
                </div>
"""

        html += """
            </div>

            <div class="hall-card hall-shame">
                <h3>⚠️ Hall of Shame (Most False Positives)</h3>
"""

        # Hall of Shame
        for i, article in enumerate(hall_of_shame, 1):
            html += f"""
                <div class="hall-item">
                    <span class="rank">#{i}</span>
                    <span class="article-id">{article['article_id']}</span>
                    <span class="score poor">FP: {article['fp']}</span>
                    <div style="font-size: 0.85em; margin-top: 5px; color: #7f8c8d;">
                        P: {self.format_percentage(article['precision'])} |
                        R: {self.format_percentage(article['recall'])} |
                        F1: {self.format_percentage(article['f1'])}
                    </div>
                </div>
"""

        html += """
            </div>
        </div>

        <h2>Category Expectations</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Expected Precision</th>
                    <th>Expected Recall</th>
                    <th>Expected FP</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="badge badge-a">CATEGORY A</span></td>
                    <td>Simple, factual news</td>
                    <td>>90%</td>
                    <td>>85%</td>
                    <td><1 per article</td>
                </tr>
                <tr>
                    <td><span class="badge badge-b">CATEGORY B</span></td>
                    <td>Complex, dense analysis</td>
                    <td>>75%</td>
                    <td>>60%</td>
                    <td><3 per article</td>
                </tr>
                <tr>
                    <td><span class="badge badge-c">CATEGORY C</span></td>
                    <td>Ambiguous, opinion-based</td>
                    <td>>60%</td>
                    <td>>50%</td>
                    <td><6 per article</td>
                </tr>
                <tr>
                    <td><span class="badge badge-d">CATEGORY D</span></td>
                    <td>Negative examples</td>
                    <td>N/A (0 expected)</td>
                    <td>N/A (0 expected)</td>
                    <td><2 per article</td>
                </tr>
            </tbody>
        </table>

        <footer>
            <p>Generated by Knowledge Graph Test Suite | {REPORT_HTML.name}</p>
            <p style="margin-top: 10px; font-size: 0.85em;">
                <strong>Metrics Definitions:</strong>
                Precision = TP/(TP+FP) measures accuracy of extracted relationships |
                Recall = TP/(TP+FN) measures completeness of extraction |
                F1 = harmonic mean balances both metrics
            </p>
        </footer>
    </div>
</body>
</html>
"""

        return html

    def save_html(self, html: str):
        """Save HTML to file."""
        with open(REPORT_HTML, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✓ HTML report saved to {REPORT_HTML}")
        print(f"  Open in browser: file://{REPORT_HTML.absolute()}")

    def run(self):
        """Generate HTML report."""
        print("="*60)
        print("HTML REPORT GENERATION")
        print("="*60)

        if not self.load_data():
            return False

        html = self.generate_html()
        self.save_html(html)

        return True


def main():
    """Main entry point."""
    generator = ReportGenerator()
    success = generator.run()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
