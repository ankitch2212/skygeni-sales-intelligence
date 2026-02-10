"""
SkyGeni Sales Intelligence - EDA Module
Performs exploratory data analysis and generates insights.

We intentionally prefer fewer, stronger insights over exhaustive coverage.
Insights below minimum sample thresholds are suppressed rather than shown,
because noisy insights erode executive trust faster than silence.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any

# Minimum deals required before generating a segment-level insight.
# Matches the global threshold in main.py.
MIN_DEALS_FOR_INSIGHT = 100


def analyze_win_rate_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze win rate trends over time.
    
    Args:
        df: DataFrame with sales data
        
    Returns:
        Dictionary with trend analysis results
    """
    quarterly = df.groupby('closed_quarter').agg({
        'deal_id': 'count',
        'is_won': ['sum', 'mean'],
        'deal_amount': 'sum'
    })
    quarterly.columns = ['total_deals', 'won_deals', 'win_rate', 'total_revenue']
    quarterly['win_rate'] = quarterly['win_rate'] * 100
    
    # Calculate period-over-period changes
    quarterly['win_rate_change'] = quarterly['win_rate'].diff()
    quarterly['deal_count_change'] = quarterly['total_deals'].diff()
    
    # Identify trend direction
    recent_quarters = quarterly.tail(4)
    win_rate_trend = 'declining' if recent_quarters['win_rate'].diff().mean() < 0 else 'improving'
    
    return {
        'quarterly_data': quarterly.to_dict(),
        'current_win_rate': quarterly['win_rate'].iloc[-1],
        'previous_win_rate': quarterly['win_rate'].iloc[-2] if len(quarterly) > 1 else None,
        'trend_direction': win_rate_trend,
        'max_win_rate': quarterly['win_rate'].max(),
        'min_win_rate': quarterly['win_rate'].min(),
    }


def analyze_segment_performance(df: pd.DataFrame, segment: str) -> pd.DataFrame:
    """
    Analyze performance by a given segment.
    
    Args:
        df: DataFrame with sales data
        segment: Column name to segment by
        
    Returns:
        DataFrame with segment analysis
    """
    stats = df.groupby(segment).agg({
        'deal_id': 'count',
        'is_won': ['sum', 'mean'],
        'deal_amount': ['mean', 'sum'],
        'sales_cycle_days': 'mean'
    })
    stats.columns = ['total_deals', 'won_deals', 'win_rate', 
                     'avg_deal_size', 'total_revenue', 'avg_cycle_days']
    stats['win_rate'] = (stats['win_rate'] * 100).round(1)
    stats['avg_deal_size'] = stats['avg_deal_size'].round(0)
    stats['avg_cycle_days'] = stats['avg_cycle_days'].round(1)
    
    # Calculate company average for comparison
    company_avg = df['is_won'].mean() * 100
    stats['vs_company_avg'] = (stats['win_rate'] - company_avg).round(1)
    
    return stats.sort_values('win_rate', ascending=False)


def identify_problem_segments(df: pd.DataFrame, 
                              min_deals: int = 100) -> Dict[str, List[str]]:
    """
    Identify segments with below-average performance.
    
    Args:
        df: DataFrame with sales data
        min_deals: Minimum deals threshold for significance
        
    Returns:
        Dictionary of underperforming segments by dimension
    """
    company_avg = df['is_won'].mean() * 100
    problem_segments = {}
    
    for segment in ['region', 'industry', 'product_type', 'lead_source']:
        stats = analyze_segment_performance(df, segment)
        # Filter for significant sample size and below average
        problems = stats[(stats['total_deals'] >= min_deals) & 
                         (stats['win_rate'] < company_avg - 5)]
        if len(problems) > 0:
            problem_segments[segment] = problems.index.tolist()
    
    return problem_segments


def identify_high_performers(df: pd.DataFrame,
                             min_deals: int = 100) -> Dict[str, List[str]]:
    """
    Identify segments with above-average performance.
    
    Args:
        df: DataFrame with sales data
        min_deals: Minimum deals threshold for significance
        
    Returns:
        Dictionary of high-performing segments by dimension
    """
    company_avg = df['is_won'].mean() * 100
    high_performers = {}
    
    for segment in ['region', 'industry', 'product_type', 'lead_source']:
        stats = analyze_segment_performance(df, segment)
        # Filter for significant sample size and above average
        performers = stats[(stats['total_deals'] >= min_deals) & 
                           (stats['win_rate'] > company_avg + 5)]
        if len(performers) > 0:
            high_performers[segment] = performers.index.tolist()
    
    return high_performers


def analyze_rep_performance(df: pd.DataFrame, 
                            min_deals: int = 50) -> pd.DataFrame:
    """
    Analyze individual sales rep performance.
    
    Args:
        df: DataFrame with sales data
        min_deals: Minimum deals for inclusion
        
    Returns:
        DataFrame with rep performance metrics
    """
    rep_stats = df.groupby('sales_rep_id').agg({
        'deal_id': 'count',
        'is_won': ['sum', 'mean'],
        'deal_amount': ['mean', 'sum'],
        'sales_cycle_days': 'mean'
    })
    rep_stats.columns = ['total_deals', 'won_deals', 'win_rate',
                         'avg_deal_size', 'total_won_revenue', 'avg_cycle_days']
    rep_stats['win_rate'] = (rep_stats['win_rate'] * 100).round(1)
    
    # Filter by minimum deals
    rep_stats = rep_stats[rep_stats['total_deals'] >= min_deals]
    
    # Rank reps
    rep_stats['win_rate_rank'] = rep_stats['win_rate'].rank(ascending=False).astype(int)
    rep_stats['revenue_rank'] = rep_stats['total_won_revenue'].rank(ascending=False).astype(int)
    
    return rep_stats.sort_values('win_rate', ascending=False)


def analyze_deal_stage_conversion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze conversion rates at each deal stage.
    
    Args:
        df: DataFrame with sales data
        
    Returns:
        DataFrame with stage conversion analysis
    """
    stage_stats = df.groupby('deal_stage').agg({
        'deal_id': 'count',
        'is_won': ['sum', 'mean'],
        'deal_amount': 'mean',
        'sales_cycle_days': 'mean'
    })
    stage_stats.columns = ['total_deals', 'won_deals', 'win_rate',
                           'avg_deal_size', 'avg_cycle_days']
    stage_stats['win_rate'] = (stage_stats['win_rate'] * 100).round(1)
    
    return stage_stats.sort_values('win_rate', ascending=False)


def generate_business_insights(df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Generate top business insights from the data.
    
    Args:
        df: DataFrame with sales data
        
    Returns:
        List of insight dictionaries with finding, why_it_matters, and action
    """
    insights = []
    company_avg = df['is_won'].mean() * 100
    
    # Insight 1: Quarterly trend
    trends = analyze_win_rate_trends(df)
    if trends['trend_direction'] == 'declining':
        current = trends['current_win_rate']
        previous = trends['previous_win_rate']
        if previous:
            drop = previous - current
            insights.append({
                'title': 'Win Rate Decline Confirmed',
                'finding': f"Win rate has dropped from {previous:.1f}% to {current:.1f}% "
                           f"(a {drop:.1f} percentage point decline)",
                'why_it_matters': "This validates the CRO's concern. Each percentage point drop "
                                  "at current pipeline volume represents significant lost revenue.",
                'action': "Conduct immediate pipeline review focusing on deals in late stages "
                          "to identify and address common loss reasons."
            })
    
    # Insight 2: Regional performance variance
    region_stats = analyze_segment_performance(df, 'region')
    best_region = region_stats.index[0]
    best_rate = region_stats.loc[best_region, 'win_rate']
    worst_region = region_stats.index[-1]
    worst_rate = region_stats.loc[worst_region, 'win_rate']
    
    if best_rate - worst_rate > 10:
        insights.append({
            'title': 'Regional Performance Gap Identified',
            'finding': f"{best_region} leads with {best_rate}% win rate while "
                       f"{worst_region} trails at {worst_rate}% (a {best_rate - worst_rate:.1f}pp gap)",
            'why_it_matters': "This gap suggests systemic differences in execution, market conditions, "
                              "or team capabilities between regions. "
                              "This pattern is directionally strong but should be validated "
                              "with qualitative sales feedback before intervention.",
            'action': f"Investigate {worst_region} - review lost deal reasons, rep performance, "
                      f"and consider replicating {best_region}'s winning playbooks."
        })
    
    # Insight 3: Lead source effectiveness
    source_stats = analyze_segment_performance(df, 'lead_source')
    best_source = source_stats.index[0]
    best_source_rate = source_stats.loc[best_source, 'win_rate']
    best_source_deals = source_stats.loc[best_source, 'total_deals']
    
    insights.append({
        'title': 'Highest Converting Lead Source Identified',
        'finding': f"{best_source} leads convert at {best_source_rate}% "
                   f"(based on {int(best_source_deals)} deals), "
                   f"which is {best_source_rate - company_avg:.1f}pp above company average",
        'why_it_matters': "Lead source is a controllable factor - investing in higher-converting "
                          "channels improves overall win rate.",
        'action': f"Work with marketing to increase {best_source} lead volume. "
                  f"Analyze what makes these leads more qualified."
    })
    
    # Insight 4: Product type performance
    product_stats = analyze_segment_performance(df, 'product_type')
    for product in product_stats.index:
        rate = product_stats.loc[product, 'win_rate']
        vs_avg = product_stats.loc[product, 'vs_company_avg']
        deals = product_stats.loc[product, 'total_deals']
        
        # Skip segments below the confidence threshold.
        # Prefer silence over noisy insight.
        if deals < MIN_DEALS_FOR_INSIGHT:
            continue
        
        if vs_avg < -8 and deals > 500:  # Significantly underperforming
            insights.append({
                'title': f'{product} Product Underperforming',
                'finding': f"{product} deals have a {rate}% win rate, "
                           f"which is {abs(vs_avg):.1f}pp below company average",
                'why_it_matters': "Product-specific win rate issues may indicate pricing, "
                                  "positioning, or competitive challenges.",
                'action': f"Review {product} sales process, pricing, and competitive positioning. "
                          f"Consider specialized training for reps selling {product}."
            })
            break  # Only report one product issue
    
    # Insight 5: Sales cycle impact
    won_deals = df[df['is_won'] == 1]
    lost_deals = df[df['is_won'] == 0]
    avg_won_cycle = won_deals['sales_cycle_days'].mean()
    avg_lost_cycle = lost_deals['sales_cycle_days'].mean()
    
    if avg_lost_cycle > avg_won_cycle * 1.2:  # Lost deals take 20%+ longer
        insights.append({
            'title': 'Slow Deals More Likely to Lose',
            'finding': f"Lost deals average {avg_lost_cycle:.0f} days in the pipeline vs "
                       f"{avg_won_cycle:.0f} days for won deals",
            'why_it_matters': "Longer sales cycles correlate with lower win probability. "
                              "Deals that stall often signal buyer disengagement.",
            'action': "Implement deal aging alerts at 60/90 day marks. "
                      "Train reps to qualify out stalled deals earlier."
        })
    
    return insights


if __name__ == "__main__":
    from data_loader import load_sales_data
    
    df = load_sales_data()
    
    print("=" * 60)
    print("EXPLORATORY DATA ANALYSIS RESULTS")
    print("=" * 60)
    
    # Win rate trends
    print("\n1. WIN RATE TRENDS")
    print("-" * 40)
    trends = analyze_win_rate_trends(df)
    print(f"Current Win Rate: {trends['current_win_rate']:.1f}%")
    print(f"Trend Direction: {trends['trend_direction']}")
    
    # Problem segments
    print("\n2. UNDERPERFORMING SEGMENTS")
    print("-" * 40)
    problems = identify_problem_segments(df)
    for dimension, segments in problems.items():
        print(f"  {dimension}: {', '.join(segments)}")
    
    # High performers
    print("\n3. HIGH-PERFORMING SEGMENTS")
    print("-" * 40)
    performers = identify_high_performers(df)
    for dimension, segments in performers.items():
        print(f"  {dimension}: {', '.join(segments)}")
    
    # Business insights
    print("\n4. KEY BUSINESS INSIGHTS")
    print("-" * 40)
    insights = generate_business_insights(df)
    for i, insight in enumerate(insights, 1):
        print(f"\nInsight {i}: {insight['title']}")
        print(f"  Finding: {insight['finding']}")
        print(f"  Why it matters: {insight['why_it_matters']}")
        print(f"  Action: {insight['action']}")
