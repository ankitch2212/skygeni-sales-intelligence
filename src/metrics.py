"""
SkyGeni Sales Intelligence - Custom Metrics Module
Defines custom business metrics for sales analysis.

NOTE: Metrics may be unstable for low-volume reps or segments.
Results are filtered or interpreted conservatively downstream.
Thresholds (MIN_DEALS_FOR_INSIGHT, MIN_DEALS_FOR_REP) are defined in main.py.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_deal_velocity_score(df: pd.DataFrame) -> pd.Series:
    """
    Custom Metric 1: Deal Velocity Score
    Definition: Deal Amount ÷ Sales Cycle Days
    Interpretation: Higher score = more value generated per day of sales effort
    
    Args:
        df: DataFrame with deal_amount and sales_cycle_days columns
        
    Returns:
        Series with velocity scores
    """
    # Avoid division by zero
    cycle_days = df['sales_cycle_days'].replace(0, 1)
    return df['deal_amount'] / cycle_days


def calculate_rep_momentum_index(df: pd.DataFrame, rep_id: str, 
                                  recent_days: int = 30, 
                                  historical_days: int = 90) -> float:
    """
    Custom Metric 2: Rep Momentum Index
    Definition: (Recent Win Rate) ÷ (Historical Win Rate)
    Interpretation: 
        > 1.0 = Rep is improving
        < 1.0 = Rep is declining
        = 1.0 = Stable performance
    
    IMPORTANT: Momentum is a directional signal, not a performance verdict.
    It should not be used for compensation or punitive evaluation.
    Its purpose is to flag trajectory changes for coaching conversations.
    
    Args:
        df: DataFrame with sales data
        rep_id: Sales rep identifier
        recent_days: Days to consider as "recent"
        historical_days: Days for historical baseline
        
    Returns:
        Momentum index value
    """
    rep_data = df[df['sales_rep_id'] == rep_id].copy()
    
    if len(rep_data) == 0:
        return np.nan
    
    max_date = rep_data['closed_date'].max()
    recent_cutoff = max_date - pd.Timedelta(days=recent_days)
    historical_cutoff = max_date - pd.Timedelta(days=historical_days)
    
    recent_deals = rep_data[rep_data['closed_date'] >= recent_cutoff]
    historical_deals = rep_data[rep_data['closed_date'] >= historical_cutoff]
    
    if len(recent_deals) < 3 or len(historical_deals) < 5:
        return np.nan  # Not enough data
    
    recent_win_rate = recent_deals['is_won'].mean()
    historical_win_rate = historical_deals['is_won'].mean()
    
    if historical_win_rate == 0:
        return np.nan
    
    return recent_win_rate / historical_win_rate


def calculate_all_rep_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate momentum index for all reps.
    
    Args:
        df: DataFrame with sales data
        
    Returns:
        DataFrame with rep_id and momentum_index
    """
    reps = df['sales_rep_id'].unique()
    results = []
    
    for rep in reps:
        momentum = calculate_rep_momentum_index(df, rep)
        rep_data = df[df['sales_rep_id'] == rep]
        results.append({
            'sales_rep_id': rep,
            'momentum_index': momentum,
            'total_deals': len(rep_data),
            'win_rate': rep_data['is_won'].mean() * 100,
            'total_revenue': rep_data[rep_data['is_won'] == 1]['deal_amount'].sum()
        })
    
    return pd.DataFrame(results).sort_values('momentum_index', ascending=False)


def calculate_segment_performance(df: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    """
    Calculate key metrics by segment.
    
    Args:
        df: DataFrame with sales data
        segment_col: Column to segment by
        
    Returns:
        DataFrame with segment performance metrics
    """
    agg = df.groupby(segment_col).agg({
        'deal_id': 'count',
        'is_won': ['sum', 'mean'],
        'deal_amount': ['mean', 'sum'],
        'sales_cycle_days': 'mean'
    }).round(2)
    
    agg.columns = ['total_deals', 'won_deals', 'win_rate', 
                   'avg_deal_size', 'total_revenue', 'avg_cycle_days']
    agg['win_rate'] = (agg['win_rate'] * 100).round(1)
    agg['total_revenue'] = agg['total_revenue'].apply(lambda x: x if pd.isna(x) else int(x))
    
    # Calculate deal velocity for won deals
    won_deals = df[df['is_won'] == 1]
    velocity = won_deals.groupby(segment_col).apply(
        lambda x: (x['deal_amount'] / x['sales_cycle_days'].replace(0, 1)).mean()
    ).round(0)
    agg['avg_velocity_score'] = velocity
    
    return agg.sort_values('win_rate', ascending=False)


def calculate_quarterly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate quarterly performance trends.
    
    Args:
        df: DataFrame with sales data
        
    Returns:
        DataFrame with quarterly metrics
    """
    quarterly = df.groupby('closed_quarter').agg({
        'deal_id': 'count',
        'is_won': ['sum', 'mean'],
        'deal_amount': ['mean', 'sum'],
        'sales_cycle_days': 'mean'
    }).round(2)
    
    quarterly.columns = ['total_deals', 'won_deals', 'win_rate',
                         'avg_deal_size', 'total_revenue', 'avg_cycle_days']
    quarterly['win_rate'] = (quarterly['win_rate'] * 100).round(1)
    
    # Calculate quarter-over-quarter changes
    quarterly['win_rate_change'] = quarterly['win_rate'].diff()
    quarterly['deal_count_change'] = quarterly['total_deals'].diff()
    
    return quarterly


def calculate_stage_conversion_rates(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate win rates by deal stage.
    
    Args:
        df: DataFrame with sales data
        
    Returns:
        Dictionary with stage conversion rates
    """
    stage_order = ['Qualified', 'Demo', 'Proposal', 'Negotiation', 'Closed']
    
    results = {}
    for stage in df['deal_stage'].unique():
        stage_data = df[df['deal_stage'] == stage]
        results[stage] = {
            'count': len(stage_data),
            'win_rate': round(stage_data['is_won'].mean() * 100, 1),
            'avg_amount': round(stage_data['deal_amount'].mean(), 0)
        }
    
    return results


if __name__ == "__main__":
    from data_loader import load_sales_data
    
    df = load_sales_data()
    
    # Test Deal Velocity Score
    df['velocity_score'] = calculate_deal_velocity_score(df)
    print("Deal Velocity Score (sample):")
    print(df[['deal_id', 'deal_amount', 'sales_cycle_days', 'velocity_score']].head())
    
    # Test Rep Momentum
    print("\n\nRep Momentum Index:")
    momentum_df = calculate_all_rep_momentum(df)
    print(momentum_df.head(10))
    
    # Test Segment Performance
    print("\n\nPerformance by Region:")
    print(calculate_segment_performance(df, 'region'))
