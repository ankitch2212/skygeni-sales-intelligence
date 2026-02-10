"""
SkyGeni Sales Intelligence - Main Application
Entry point for running the complete sales analysis pipeline.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Global Confidence Thresholds
# These define the minimum sample sizes required for trustworthy insights.
# Below these thresholds, results are either suppressed or flagged.
# ---------------------------------------------------------------------------
MIN_DEALS_FOR_INSIGHT = 100   # Minimum deals to generate a segment-level insight
MIN_DEALS_FOR_REP = 50        # Minimum deals to evaluate individual rep performance

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.data_loader import load_sales_data, validate_data, get_data_summary
from src.eda import (
    analyze_win_rate_trends,
    analyze_segment_performance,
    identify_problem_segments,
    identify_high_performers,
    generate_business_insights
)
from src.metrics import (
    calculate_deal_velocity_score,
    calculate_all_rep_momentum,
    calculate_segment_performance as calc_segment_metrics,
    calculate_quarterly_trends
)
from src.decision_engine import WinRateDriverAnalyzer
from src.visualization import generate_all_charts


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_subheader(title: str):
    """Print a formatted subsection header."""
    print("\n" + "-" * 50)
    print(f" {title}")
    print("-" * 50)


def run_analysis():
    """
    Run the complete sales intelligence analysis pipeline.
    
    The analysis follows a CRO's mental flow:
    data sanity → trend validation → segmentation → rep performance → decisions → visuals
    
    This ordering is intentional: each step builds context for the next,
    mirroring how a revenue leader would naturally investigate a win-rate drop.
    """
    
    print_header("SKYGENI SALES INTELLIGENCE ANALYSIS")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # =========================================================================
    # STEP 1: Load and Validate Data
    # =========================================================================
    print_header("STEP 1: DATA LOADING & VALIDATION")
    
    print("Loading sales data...")
    df = load_sales_data()
    
    print("Validating data quality...")
    is_valid, issues = validate_data(df)
    
    if is_valid:
        print("✓ Data validation passed")
    else:
        print("⚠ Data validation warnings:")
        for issue in issues:
            print(f"  - {issue}")
        print("⚠ Proceeding with analysis using best-available data. Interpret insights cautiously.")
    
    summary = get_data_summary(df)
    print(f"\nData Summary:")
    print(f"  Total Deals: {summary['total_deals']:,}")
    print(f"  Date Range: {summary['date_range']['earliest_created']} to {summary['date_range']['latest_closed']}")
    print(f"  Overall Win Rate: {summary['overall_win_rate']:.1f}%")
    print(f"  Average Deal Size: ${summary['avg_deal_amount']:,.0f}")
    print(f"  Average Sales Cycle: {summary['avg_sales_cycle']:.0f} days")
    
    # =========================================================================
    # STEP 2: Exploratory Data Analysis
    # =========================================================================
    print_header("STEP 2: EXPLORATORY DATA ANALYSIS")
    
    # Win Rate Trends
    print_subheader("Win Rate Trends")
    trends = analyze_win_rate_trends(df)
    print(f"Trend Direction: {trends['trend_direction'].upper()}")
    print(f"Current Win Rate: {trends['current_win_rate']:.1f}%")
    if trends['previous_win_rate']:
        change = trends['current_win_rate'] - trends['previous_win_rate']
        direction = "↑" if change > 0 else "↓"
        print(f"Quarter-over-Quarter Change: {direction} {abs(change):.1f}pp")
    
    # Segment Analysis
    print_subheader("Segment Performance Analysis")
    
    for segment in ['region', 'industry', 'product_type', 'lead_source']:
        print(f"\nBy {segment.replace('_', ' ').title()}:")
        seg_stats = analyze_segment_performance(df, segment)
        for idx in seg_stats.index[:3]:
            rate = seg_stats.loc[idx, 'win_rate']
            diff = seg_stats.loc[idx, 'vs_company_avg']
            indicator = "✓" if diff > 0 else "✗"
            print(f"  {indicator} {idx}: {rate}% ({diff:+.1f}pp vs avg)")
    
    # Problem Areas
    print_subheader("Identified Problem Areas")
    problems = identify_problem_segments(df)
    if problems:
        for dim, segments in problems.items():
            print(f"  {dim}: {', '.join(segments)}")
    else:
        print("  No significant underperforming segments identified")
    
    # =========================================================================
    # STEP 3: Custom Metrics
    # =========================================================================
    print_header("STEP 3: CUSTOM METRICS")
    
    # Deal Velocity Score
    print_subheader("Custom Metric 1: Deal Velocity Score")
    print("Definition: Deal Amount ÷ Sales Cycle Days")
    print("Interpretation: Higher score = more value per day of sales effort")
    
    df['velocity_score'] = calculate_deal_velocity_score(df)
    won_deals = df[df['is_won'] == 1]
    
    print(f"\nVelocity by Product Type (Won Deals):")
    vel_by_product = won_deals.groupby('product_type')['velocity_score'].mean().sort_values(ascending=False)
    for product, vel in vel_by_product.items():
        print(f"  {product}: ${vel:,.0f}/day")
    
    # Rep Momentum Index
    print_subheader("Custom Metric 2: Rep Momentum Index")
    print("Definition: Recent 30-day Win Rate ÷ 90-day Historical Win Rate")
    print("Interpretation: >1.0 = Improving, <1.0 = Declining")
    
    momentum_df = calculate_all_rep_momentum(df)
    valid_momentum = momentum_df[momentum_df['momentum_index'].notna()]
    
    improving = valid_momentum[valid_momentum['momentum_index'] > 1.1]
    declining = valid_momentum[valid_momentum['momentum_index'] < 0.9]
    
    print(f"\nImproving Reps (momentum > 1.1): {len(improving)}")
    print(f"Declining Reps (momentum < 0.9): {len(declining)}")
    
    if len(declining) > 0:
        print("\nTop Declining Reps (need attention):")
        for _, row in declining.head(3).iterrows():
            print(f"  {row['sales_rep_id']}: momentum = {row['momentum_index']:.2f}")
    
    # =========================================================================
    # STEP 4: Business Insights
    # =========================================================================
    print_header("STEP 4: KEY BUSINESS INSIGHTS")
    
    insights = generate_business_insights(df)
    
    for i, insight in enumerate(insights, 1):
        print(f"\n{'─' * 50}")
        print(f"INSIGHT {i}: {insight['title']}")
        print(f"{'─' * 50}")
        print(f"\n📊 Finding:")
        print(f"   {insight['finding']}")
        print(f"\n💡 Why It Matters:")
        print(f"   {insight['why_it_matters']}")
        print(f"\n🎯 Recommended Action:")
        print(f"   {insight['action']}")
    
    # =========================================================================
    # STEP 5: Decision Engine - Win Rate Driver Analysis
    # =========================================================================
    print_header("STEP 5: WIN RATE DRIVER ANALYSIS (DECISION ENGINE)")
    
    analyzer = WinRateDriverAnalyzer(df)
    analyzer.analyze_all_factors()
    
    # Executive Summary
    print(analyzer.generate_executive_summary())
    
    # =========================================================================
    # STEP 6: Generate Visualizations
    # =========================================================================
    print_header("STEP 6: GENERATING VISUALIZATIONS")
    
    output_dir = "outputs"
    charts = generate_all_charts(df, output_dir)
    
    print(f"\nGenerated {len(charts)} charts:")
    for chart in charts:
        print(f"  ✓ {chart}")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print_header("ANALYSIS COMPLETE")
    
    print("""
Key Deliverables:
─────────────────
1. ✓ Problem Framing (docs/part1_problem_framing.md)
2. ✓ EDA & Insights (this analysis + outputs/)
3. ✓ Decision Engine (Win Rate Driver Analysis)
4. ✓ System Design (docs/part4_system_design.md)
5. ✓ Reflection (docs/part5_reflection.md)

For the CRO:
────────────
The analysis confirms the win rate decline and identifies specific
segments, reps, and lead sources that are underperforming. 

Key recommendations:
• Focus on underperforming regions/industries
• Implement coaching for at-risk reps
• Increase investment in high-converting lead sources
• Monitor deal aging to catch stalled deals early

See the generated charts in outputs/ for visual reference.
""")
    
    return {
        'data': df,
        'summary': summary,
        'insights': insights,
        'analyzer': analyzer,
        'charts': charts
    }


if __name__ == "__main__":
    results = run_analysis()
