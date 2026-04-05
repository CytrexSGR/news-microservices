#!/usr/bin/env python3
"""
TRIAGE Quality Analysis Tool

Compares TRIAGE agent quality between gemini-flash-latest and gemini-flash-lite-latest.

Features:
- Detailed statistical comparison
- Visual charts (optional)
- Side-by-side article comparison
- Export results to JSON/CSV

Usage:
    python scripts/analyze_triage_quality.py [--days 7] [--export json] [--charts]

Examples:
    python scripts/analyze_triage_quality.py
    python scripts/analyze_triage_quality.py --days 3 --export json
    python scripts/analyze_triage_quality.py --charts --export csv
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# Optional visualization support
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


class TriageQualityAnalyzer:
    """Analyzes TRIAGE agent quality across different models."""

    def __init__(self, db_config: Dict[str, str]):
        """Initialize analyzer with database configuration."""
        self.db_config = db_config
        self.conn = None

    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("✓ Connected to database")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            sys.exit(1)

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def get_model_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive statistics for each model.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with statistics per model
        """
        query = """
        SELECT
            model_used,
            COUNT(*) as total_articles,

            -- Priority Score Stats
            AVG((result_data->>'PriorityScore')::int) as avg_priority_score,
            STDDEV((result_data->>'PriorityScore')::int) as stddev_priority,
            MIN((result_data->>'PriorityScore')::int) as min_score,
            MAX((result_data->>'PriorityScore')::int) as max_score,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (result_data->>'PriorityScore')::int) as median_score,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY (result_data->>'PriorityScore')::int) as q1_score,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY (result_data->>'PriorityScore')::int) as q3_score,

            -- Component Scores
            AVG((result_data->'scoring_justification'->>'ImpactScore')::int) as avg_impact_score,
            AVG((result_data->'scoring_justification'->>'EntityScore')::int) as avg_entity_score,
            AVG((result_data->'scoring_justification'->>'SourceScore')::int) as avg_source_score,
            AVG((result_data->'scoring_justification'->>'UrgencyMultiplier')::float) as avg_urgency,

            -- Decision Impact
            COUNT(*) FILTER (WHERE (result_data->>'PriorityScore')::int >= 60) as tier2_triggered,
            COUNT(*) FILTER (WHERE (result_data->>'PriorityScore')::int < 60) as tier2_skipped,

            -- Performance
            AVG(cost_usd) as avg_cost,
            SUM(cost_usd) as total_cost,
            AVG(processing_time_ms) as avg_time_ms,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time_ms) as p95_time_ms,

            -- Reliability
            COUNT(*) FILTER (WHERE status = 'failed') as failures

        FROM content_analysis_v2.agent_results
        WHERE agent_name = 'TRIAGE'
          AND created_at > NOW() - INTERVAL '%s days'
          AND result_data->>'PriorityScore' IS NOT NULL
        GROUP BY model_used
        """ % days

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()

        return {row['model_used']: dict(row) for row in results}

    def get_category_distribution(self, days: int = 7) -> Dict[str, List[Dict]]:
        """Get category distribution per model."""
        query = """
        SELECT
            model_used,
            result_data->>'category' as category,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY model_used), 2) as percentage
        FROM content_analysis_v2.agent_results
        WHERE agent_name = 'TRIAGE'
          AND created_at > NOW() - INTERVAL '%s days'
          AND result_data->>'category' IS NOT NULL
        GROUP BY model_used, result_data->>'category'
        ORDER BY model_used, count DESC
        """ % days

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()

        # Group by model
        distribution = {}
        for row in results:
            model = row['model_used']
            if model not in distribution:
                distribution[model] = []
            distribution[model].append({
                'category': row['category'],
                'count': row['count'],
                'percentage': float(row['percentage'])
            })

        return distribution

    def get_score_buckets(self, days: int = 7) -> Dict[str, List[Dict]]:
        """Get score distribution in buckets."""
        query = """
        WITH score_buckets AS (
            SELECT
                model_used,
                CASE
                    WHEN (result_data->>'PriorityScore')::int >= 85 THEN '85-100'
                    WHEN (result_data->>'PriorityScore')::int >= 70 THEN '70-84'
                    WHEN (result_data->>'PriorityScore')::int >= 60 THEN '60-69'
                    WHEN (result_data->>'PriorityScore')::int >= 50 THEN '50-59'
                    WHEN (result_data->>'PriorityScore')::int >= 40 THEN '40-49'
                    ELSE '0-39'
                END as bucket
            FROM content_analysis_v2.agent_results
            WHERE agent_name = 'TRIAGE'
              AND created_at > NOW() - INTERVAL '%s days'
              AND result_data->>'PriorityScore' IS NOT NULL
        )
        SELECT
            model_used,
            bucket,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY model_used), 2) as percentage
        FROM score_buckets
        GROUP BY model_used, bucket
        ORDER BY model_used, bucket DESC
        """ % days

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()

        # Group by model
        buckets = {}
        for row in results:
            model = row['model_used']
            if model not in buckets:
                buckets[model] = []
            buckets[model].append({
                'bucket': row['bucket'],
                'count': row['count'],
                'percentage': float(row['percentage'])
            })

        return buckets

    def compare_models(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two models and calculate differences.

        Args:
            stats: Statistics dictionary from get_model_statistics()

        Returns:
            Comparison metrics and differences
        """
        models = list(stats.keys())
        if len(models) < 2:
            return {"error": "Need at least 2 models for comparison"}

        # Assume we're comparing flash-latest vs flash-lite-latest
        model_a = next((m for m in models if 'flash-latest' in m and 'lite' not in m), models[0])
        model_b = next((m for m in models if 'flash-lite-latest' in m), models[1])

        a_stats = stats[model_a]
        b_stats = stats[model_b]

        comparison = {
            'model_a': model_a,
            'model_b': model_b,
            'differences': {
                'priority_score_diff': abs(a_stats['avg_priority_score'] - b_stats['avg_priority_score']),
                'impact_score_diff': abs(a_stats['avg_impact_score'] - b_stats['avg_impact_score']),
                'entity_score_diff': abs(a_stats['avg_entity_score'] - b_stats['avg_entity_score']),
                'source_score_diff': abs(a_stats['avg_source_score'] - b_stats['avg_source_score']),
                'tier2_trigger_rate_diff': abs(
                    (a_stats['tier2_triggered'] / a_stats['total_articles'] * 100) -
                    (b_stats['tier2_triggered'] / b_stats['total_articles'] * 100)
                ),
            },
            'performance': {
                'cost_reduction_pct': (1 - b_stats['avg_cost'] / a_stats['avg_cost']) * 100,
                'speed_improvement_pct': (1 - b_stats['avg_time_ms'] / a_stats['avg_time_ms']) * 100,
                'cost_savings_total': a_stats['total_cost'] - b_stats['total_cost'],
            },
            'quality_assessment': {}
        }

        # Quality assessment
        comparison['quality_assessment'] = {
            'score_similarity': 'GOOD' if comparison['differences']['priority_score_diff'] < 5 else 'CONCERNING',
            'tier2_trigger_consistency': 'GOOD' if comparison['differences']['tier2_trigger_rate_diff'] < 10 else 'CONCERNING',
            'component_scores_consistent': 'GOOD' if max(
                comparison['differences']['impact_score_diff'],
                comparison['differences']['entity_score_diff'],
                comparison['differences']['source_score_diff']
            ) < 5 else 'CONCERNING',
        }

        return comparison

    def print_report(self, stats: Dict[str, Any], comparison: Dict[str, Any],
                    categories: Dict[str, List], buckets: Dict[str, List]):
        """Print comprehensive comparison report."""
        print("\n" + "="*80)
        print("TRIAGE MODEL QUALITY COMPARISON REPORT")
        print("="*80 + "\n")

        # Model Statistics
        print("1. MODEL STATISTICS")
        print("-" * 80)
        for model, data in stats.items():
            print(f"\n{model}:")
            print(f"  Articles Analyzed:     {data['total_articles']}")
            print(f"  Avg Priority Score:    {data['avg_priority_score']:.2f} ± {data['stddev_priority']:.2f}")
            print(f"  Score Range:           {data['min_score']}-{data['max_score']} (median: {data['median_score']:.0f})")
            print(f"  Tier 2 Triggered:      {data['tier2_triggered']} ({data['tier2_triggered']/data['total_articles']*100:.1f}%)")
            print(f"  Tier 2 Skipped:        {data['tier2_skipped']} ({data['tier2_skipped']/data['total_articles']*100:.1f}%)")
            print(f"\n  Component Scores:")
            print(f"    Impact Score:        {data['avg_impact_score']:.2f}")
            print(f"    Entity Score:        {data['avg_entity_score']:.2f}")
            print(f"    Source Score:        {data['avg_source_score']:.2f}")
            print(f"    Urgency Multiplier:  {data['avg_urgency']:.2f}")
            print(f"\n  Performance:")
            print(f"    Avg Cost:            ${data['avg_cost']:.8f}")
            print(f"    Total Cost:          ${data['total_cost']:.6f}")
            print(f"    Avg Time:            {data['avg_time_ms']:.0f}ms")
            print(f"    P95 Time:            {data['p95_time_ms']:.0f}ms")
            print(f"    Failures:            {data['failures']}")

        # Comparison
        if 'error' not in comparison:
            print("\n\n2. MODEL COMPARISON")
            print("-" * 80)
            print(f"\nComparing: {comparison['model_a']} vs {comparison['model_b']}")

            print("\n  Score Differences:")
            print(f"    Priority Score:      {comparison['differences']['priority_score_diff']:.2f} points")
            print(f"    Impact Score:        {comparison['differences']['impact_score_diff']:.2f} points")
            print(f"    Entity Score:        {comparison['differences']['entity_score_diff']:.2f} points")
            print(f"    Source Score:        {comparison['differences']['source_score_diff']:.2f} points")
            print(f"    Tier 2 Trigger Rate: {comparison['differences']['tier2_trigger_rate_diff']:.2f}%")

            print("\n  Performance Improvements:")
            print(f"    Cost Reduction:      {comparison['performance']['cost_reduction_pct']:.1f}%")
            print(f"    Speed Improvement:   {comparison['performance']['speed_improvement_pct']:.1f}%")
            print(f"    Total Savings:       ${comparison['performance']['cost_savings_total']:.6f}")

            print("\n  Quality Assessment:")
            for metric, status in comparison['quality_assessment'].items():
                indicator = "✓" if status == "GOOD" else "⚠"
                print(f"    {indicator} {metric.replace('_', ' ').title()}: {status}")

        # Category Distribution
        print("\n\n3. CATEGORY DISTRIBUTION")
        print("-" * 80)
        for model, cats in categories.items():
            print(f"\n{model}:")
            for cat in cats:
                print(f"  {cat['category']:30s} {cat['count']:4d} ({cat['percentage']:5.1f}%)")

        # Score Buckets
        print("\n\n4. SCORE DISTRIBUTION BUCKETS")
        print("-" * 80)
        for model, bucket_list in buckets.items():
            print(f"\n{model}:")
            for b in bucket_list:
                print(f"  {b['bucket']:10s} {b['count']:4d} ({b['percentage']:5.1f}%)")

        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)

        if 'error' not in comparison:
            qa = comparison['quality_assessment']
            all_good = all(v == 'GOOD' for v in qa.values())

            if all_good:
                print("\n✅ QUALITY MAINTAINED")
                print("   The lite model produces comparable results to the standard model.")
                print("   Cost savings of {:.1f}% make this an excellent optimization.".format(
                    comparison['performance']['cost_reduction_pct']
                ))
            else:
                print("\n⚠️  QUALITY CONCERNS DETECTED")
                print("   Review the concerning metrics above.")
                print("   Consider:")
                print("   - Running a manual review of high-priority articles")
                print("   - Checking if important news are being skipped")
                print("   - Monitoring for 2-3 more days before final decision")

        print("\n")

    def export_results(self, data: Dict, format: str, filename: str):
        """Export results to file."""
        if format == 'json':
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"✓ Exported to {filename}")
        elif format == 'csv' and VISUALIZATION_AVAILABLE:
            # Convert to pandas and export
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"✓ Exported to {filename}")
        else:
            print(f"✗ Export format '{format}' not supported or pandas not installed")

    def create_visualizations(self, stats: Dict, buckets: Dict, categories: Dict):
        """Create comparison visualizations."""
        if not VISUALIZATION_AVAILABLE:
            print("✗ Visualization libraries not installed (pandas, matplotlib, seaborn)")
            return

        sns.set_style("whitegrid")
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('TRIAGE Model Quality Comparison', fontsize=16, fontweight='bold')

        # 1. Priority Score Distribution
        models = list(stats.keys())
        scores = [stats[m]['avg_priority_score'] for m in models]
        stds = [stats[m]['stddev_priority'] for m in models]

        axes[0, 0].bar(models, scores, yerr=stds, capsize=5)
        axes[0, 0].set_title('Average Priority Score')
        axes[0, 0].set_ylabel('Score')

        # 2. Tier 2 Trigger Rate
        trigger_rates = [stats[m]['tier2_triggered'] / stats[m]['total_articles'] * 100 for m in models]
        axes[0, 1].bar(models, trigger_rates)
        axes[0, 1].set_title('Tier 2 Trigger Rate')
        axes[0, 1].set_ylabel('Percentage (%)')

        # 3. Component Scores
        components = ['avg_impact_score', 'avg_entity_score', 'avg_source_score']
        x = range(len(components))
        width = 0.35

        for i, model in enumerate(models):
            values = [stats[model][comp] for comp in components]
            axes[1, 0].bar([xi + width*i for xi in x], values, width, label=model)

        axes[1, 0].set_title('Component Score Comparison')
        axes[1, 0].set_xticks([xi + width/2 for xi in x])
        axes[1, 0].set_xticklabels(['Impact', 'Entity', 'Source'])
        axes[1, 0].legend()

        # 4. Cost vs Time
        costs = [stats[m]['avg_cost'] * 1000 for m in models]  # Convert to millicents
        times = [stats[m]['avg_time_ms'] for m in models]

        axes[1, 1].scatter(times, costs, s=100)
        for i, model in enumerate(models):
            axes[1, 1].annotate(model.split('-')[-1], (times[i], costs[i]))
        axes[1, 1].set_title('Cost vs Processing Time')
        axes[1, 1].set_xlabel('Time (ms)')
        axes[1, 1].set_ylabel('Cost (millicents)')

        plt.tight_layout()
        plt.savefig('/tmp/triage_quality_comparison.png', dpi=150)
        print(f"✓ Charts saved to /tmp/triage_quality_comparison.png")

        # Open the image if possible
        try:
            plt.show()
        except:
            pass


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze TRIAGE agent quality across models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/analyze_triage_quality.py
  python scripts/analyze_triage_quality.py --days 3
  python scripts/analyze_triage_quality.py --export json --charts
  python scripts/analyze_triage_quality.py --days 7 --export csv
        """
    )

    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to analyze (default: 7)')
    parser.add_argument('--export', choices=['json', 'csv'],
                       help='Export results to file')
    parser.add_argument('--charts', action='store_true',
                       help='Generate visualization charts')

    args = parser.parse_args()

    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'news_mcp',
        'user': 'news_user',
        'password': 'newspass123'
    }

    # Run analysis
    analyzer = TriageQualityAnalyzer(db_config)

    try:
        analyzer.connect()

        print(f"Analyzing TRIAGE quality for last {args.days} days...")
        print("Loading data...\n")

        # Get data
        stats = analyzer.get_model_statistics(args.days)
        categories = analyzer.get_category_distribution(args.days)
        buckets = analyzer.get_score_buckets(args.days)
        comparison = analyzer.compare_models(stats)

        # Print report
        analyzer.print_report(stats, comparison, categories, buckets)

        # Export if requested
        if args.export:
            export_data = {
                'statistics': stats,
                'comparison': comparison,
                'categories': categories,
                'buckets': buckets,
                'timestamp': datetime.now().isoformat(),
                'analysis_period_days': args.days
            }
            filename = f'/tmp/triage_quality_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{args.export}'
            analyzer.export_results(export_data, args.export, filename)

        # Create charts if requested
        if args.charts:
            analyzer.create_visualizations(stats, buckets, categories)

    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        analyzer.disconnect()


if __name__ == '__main__':
    main()
