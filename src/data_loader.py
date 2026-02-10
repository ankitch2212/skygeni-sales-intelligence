"""
SkyGeni Sales Intelligence - Data Loader Module
Handles data ingestion, validation, and preprocessing.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, Optional


def load_sales_data(filepath: str = "data/skygeni_sales_data.csv") -> pd.DataFrame:
    """
    Load sales data from CSV file with proper type conversions.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        DataFrame with properly typed columns
    """
    df = pd.read_csv(filepath)
    
    # Convert date columns
    df['created_date'] = pd.to_datetime(df['created_date'])
    df['closed_date'] = pd.to_datetime(df['closed_date'])
    
    # Ensure numeric types
    df['deal_amount'] = pd.to_numeric(df['deal_amount'], errors='coerce')
    df['sales_cycle_days'] = pd.to_numeric(df['sales_cycle_days'], errors='coerce')
    
    # Add derived columns
    df['created_quarter'] = df['created_date'].dt.to_period('Q')
    df['closed_quarter'] = df['closed_date'].dt.to_period('Q')
    df['created_month'] = df['created_date'].dt.to_period('M')
    df['closed_month'] = df['closed_date'].dt.to_period('M')
    df['is_won'] = (df['outcome'] == 'Won').astype(int)
    
    return df


def validate_data(df: pd.DataFrame) -> Tuple[bool, list]:
    """
    Validate data quality and return issues found.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    # CRM data is expected to contain inconsistencies.
    # Validation highlights risk but does not block analysis.
    # This is a deliberate choice: real-world CRM data is messy,
    # and waiting for perfect data means never shipping insights.
    issues = []
    
    # Check for missing values
    missing = df.isnull().sum()
    if missing.any():
        for col in missing[missing > 0].index:
            issues.append(f"Missing values in {col}: {missing[col]}")
    
    # Check date sanity
    invalid_dates = df[df['closed_date'] < df['created_date']]
    if len(invalid_dates) > 0:
        issues.append(f"Deals with closed_date before created_date: {len(invalid_dates)}")
    
    # Check for negative values
    if (df['deal_amount'] < 0).any():
        issues.append("Negative deal amounts found")
    
    if (df['sales_cycle_days'] < 0).any():
        issues.append("Negative sales cycle days found")
    
    # Flag missing velocity data — a common CRM issue that can silently
    # bias Deal Velocity Score and sales cycle analyses.
    if df['sales_cycle_days'].isnull().any():
        issues.append("Missing sales cycle days may bias velocity metrics")
    
    # Check outcome values
    valid_outcomes = {'Won', 'Lost'}
    invalid_outcomes = df[~df['outcome'].isin(valid_outcomes)]
    if len(invalid_outcomes) > 0:
        issues.append(f"Invalid outcome values: {invalid_outcomes['outcome'].unique()}")
    
    return len(issues) == 0, issues


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Generate summary statistics for the dataset.
    
    Args:
        df: DataFrame to summarize
        
    Returns:
        Dictionary with summary statistics
    """
    return {
        'total_deals': len(df),
        'date_range': {
            'earliest_created': df['created_date'].min().strftime('%Y-%m-%d'),
            'latest_created': df['created_date'].max().strftime('%Y-%m-%d'),
            'earliest_closed': df['closed_date'].min().strftime('%Y-%m-%d'),
            'latest_closed': df['closed_date'].max().strftime('%Y-%m-%d'),
        },
        'outcomes': df['outcome'].value_counts().to_dict(),
        'overall_win_rate': df['is_won'].mean() * 100,
        'avg_deal_amount': df['deal_amount'].mean(),
        'avg_sales_cycle': df['sales_cycle_days'].mean(),
        'unique_reps': df['sales_rep_id'].nunique(),
        'unique_industries': df['industry'].nunique(),
        'unique_regions': df['region'].nunique(),
    }


if __name__ == "__main__":
    # Test the module
    df = load_sales_data()
    is_valid, issues = validate_data(df)
    print(f"Data valid: {is_valid}")
    if issues:
        for issue in issues:
            print(f"  - {issue}")
    
    summary = get_data_summary(df)
    print("\nData Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
