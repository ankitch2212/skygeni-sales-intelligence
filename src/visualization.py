"""
SkyGeni Sales Intelligence - Visualization Module
Creates charts and visual reports for sales analysis.

Design Philosophy:
  Visualizations prioritize interpretability over aesthetics.
  Each chart is designed to support a specific business question.
  Color semantics are consistent: green = above average, red = below, amber = average.
  Sample sizes (n=) are included wherever possible to signal data confidence.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
from typing import Optional


# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


def save_figure(fig: plt.Figure, filename: str, output_dir: str = "outputs") -> str:
    """Save figure to output directory."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filepath = Path(output_dir) / filename
    fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return str(filepath)


def plot_quarterly_win_rate_trend(df: pd.DataFrame, output_dir: str = "outputs") -> str:
    """
    Plot win rate trend over quarters.
    
    Args:
        df: DataFrame with sales data
        output_dir: Directory to save the chart
        
    Returns:
        Path to saved figure
    """
    quarterly = df.groupby('closed_quarter').agg({
        'deal_id': 'count',
        'is_won': 'mean'
    }).reset_index()
    quarterly['win_rate'] = quarterly['is_won'] * 100
    quarterly['quarter_str'] = quarterly['closed_quarter'].astype(str)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Bar chart for deal count
    bars = ax1.bar(quarterly['quarter_str'], quarterly['deal_id'], 
                   alpha=0.3, color='steelblue', label='Deal Count')
    ax1.set_xlabel('Quarter', fontsize=12)
    ax1.set_ylabel('Number of Deals', color='steelblue', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='steelblue')
    
    # Line chart for win rate
    ax2 = ax1.twinx()
    line = ax2.plot(quarterly['quarter_str'], quarterly['win_rate'], 
                    color='darkred', marker='o', linewidth=3, markersize=10,
                    label='Win Rate %')
    ax2.set_ylabel('Win Rate (%)', color='darkred', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='darkred')
    ax2.set_ylim(0, 100)
    
    # Add value labels on the line
    for i, (q, wr) in enumerate(zip(quarterly['quarter_str'], quarterly['win_rate'])):
        ax2.annotate(f'{wr:.1f}%', (q, wr), textcoords="offset points", 
                     xytext=(0, 10), ha='center', fontsize=10, fontweight='bold')
    
    plt.title('Win Rate Trend Over Time', fontsize=16, fontweight='bold', pad=20)
    fig.tight_layout()
    
    return save_figure(fig, 'win_rate_trend.png', output_dir)


def plot_segment_heatmap(df: pd.DataFrame, row_col: str, col_col: str,
                         output_dir: str = "outputs") -> str:
    """
    Create heatmap of win rates by two dimensions.
    
    Args:
        df: DataFrame with sales data
        row_col: Column for rows
        col_col: Column for columns
        output_dir: Directory to save the chart
        
    Returns:
        Path to saved figure
    """
    pivot = df.pivot_table(
        values='is_won',
        index=row_col,
        columns=col_col,
        aggfunc='mean'
    ) * 100
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=50,
                vmin=30, vmax=70, ax=ax, cbar_kws={'label': 'Win Rate %'},
                annot_kws={'fontsize': 11})
    
    plt.title(f'Win Rate (%) by {row_col} and {col_col}', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel(col_col, fontsize=12)
    plt.ylabel(row_col, fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    fig.tight_layout()
    
    return save_figure(fig, f'heatmap_{row_col}_{col_col}.png', output_dir)


def plot_factor_comparison(df: pd.DataFrame, factor: str,
                           output_dir: str = "outputs") -> str:
    """
    Compare win rates across a factor with deal counts.
    
    Args:
        df: DataFrame with sales data
        factor: Column to analyze
        output_dir: Directory to save the chart
        
    Returns:
        Path to saved figure
    """
    stats = df.groupby(factor).agg({
        'deal_id': 'count',
        'is_won': 'mean',
        'deal_amount': 'mean'
    }).reset_index()
    stats['win_rate'] = stats['is_won'] * 100
    stats = stats.sort_values('win_rate', ascending=True)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color bars based on win rate
    colors = ['#e74c3c' if wr < 45 else '#27ae60' if wr > 55 else '#f39c12' 
              for wr in stats['win_rate']]
    
    bars = ax.barh(stats[factor], stats['win_rate'], color=colors, edgecolor='white')
    
    # Add value labels
    for bar, count in zip(bars, stats['deal_id']):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}% (n={count})',
                va='center', fontsize=10)
    
    ax.set_xlabel('Win Rate (%)', fontsize=12)
    ax.set_ylabel(factor, fontsize=12)
    ax.set_xlim(0, max(stats['win_rate']) + 15)
    ax.axvline(x=df['is_won'].mean() * 100, color='gray', linestyle='--', 
               linewidth=2, label='Average')
    
    # Legend
    legend_elements = [
        mpatches.Patch(color='#27ae60', label='Above Average (>55%)'),
        mpatches.Patch(color='#f39c12', label='Average (45-55%)'),
        mpatches.Patch(color='#e74c3c', label='Below Average (<45%)'),
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.title(f'Win Rate by {factor}', fontsize=16, fontweight='bold', pad=20)
    fig.tight_layout()
    
    return save_figure(fig, f'win_rate_by_{factor.lower()}.png', output_dir)


def plot_rep_performance(df: pd.DataFrame, top_n: int = 15,
                        output_dir: str = "outputs") -> str:
    """
    Plot top and bottom performing sales reps.
    
    Args:
        df: DataFrame with sales data
        top_n: Number of reps to show
        output_dir: Directory to save the chart
        
    Returns:
        Path to saved figure
    """
    rep_stats = df.groupby('sales_rep_id').agg({
        'deal_id': 'count',
        'is_won': ['sum', 'mean'],
        'deal_amount': 'sum'
    })
    rep_stats.columns = ['deals', 'wins', 'win_rate', 'revenue']
    rep_stats['win_rate'] = rep_stats['win_rate'] * 100
    rep_stats = rep_stats[rep_stats['deals'] >= 50]  # Min 50 deals
    rep_stats = rep_stats.sort_values('win_rate', ascending=False)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Top performers
    top = rep_stats.head(top_n // 2)
    axes[0].barh(top.index, top['win_rate'], color='#27ae60', edgecolor='white')
    axes[0].set_xlabel('Win Rate (%)', fontsize=12)
    axes[0].set_title('Top Performers', fontsize=14, fontweight='bold')
    for i, (idx, row) in enumerate(top.iterrows()):
        axes[0].text(row['win_rate'] + 0.5, i, f"{row['win_rate']:.1f}%", va='center')
    
    # Bottom performers  
    bottom = rep_stats.tail(top_n // 2)
    axes[1].barh(bottom.index, bottom['win_rate'], color='#e74c3c', edgecolor='white')
    axes[1].set_xlabel('Win Rate (%)', fontsize=12)
    axes[1].set_title('Needs Improvement', fontsize=14, fontweight='bold')
    for i, (idx, row) in enumerate(bottom.iterrows()):
        axes[1].text(row['win_rate'] + 0.5, i, f"{row['win_rate']:.1f}%", va='center')
    
    plt.suptitle('Sales Rep Performance Analysis', fontsize=16, fontweight='bold')
    fig.tight_layout()
    
    return save_figure(fig, 'rep_performance.png', output_dir)


def plot_deal_stage_funnel(df: pd.DataFrame, output_dir: str = "outputs") -> str:
    """
    Plot win rates by deal stage.
    
    Semantic note:
        Win rate reflects final outcomes of deals that reached each stage,
        not probability of conversion from that stage. This distinction
        matters when interpreting the chart — a high win rate at 'Negotiation'
        means deals that entered Negotiation tend to close, not that reaching
        Negotiation guarantees a win.
    
    Args:
        df: DataFrame with sales data
        output_dir: Directory to save the chart
        
    Returns:
        Path to saved figure
    """
    stage_stats = df.groupby('deal_stage').agg({
        'deal_id': 'count',
        'is_won': 'mean'
    }).reset_index()
    stage_stats['win_rate'] = stage_stats['is_won'] * 100
    stage_stats = stage_stats.sort_values('win_rate', ascending=False)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = plt.cm.RdYlGn(stage_stats['win_rate'] / 100)
    bars = ax.bar(stage_stats['deal_stage'], stage_stats['win_rate'], 
                  color=colors, edgecolor='white', linewidth=2)
    
    # Add value labels
    for bar, count in zip(bars, stage_stats['deal_id']):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 1,
                f'{height:.1f}%\n(n={count})',
                ha='center', fontsize=10)
    
    ax.set_xlabel('Deal Stage', fontsize=12)
    ax.set_ylabel('Win Rate (%)', fontsize=12)
    ax.set_ylim(0, max(stage_stats['win_rate']) + 15)
    ax.axhline(y=df['is_won'].mean() * 100, color='gray', linestyle='--', 
               linewidth=2, label='Average')
    
    plt.title('Win Rate by Deal Stage', fontsize=16, fontweight='bold', pad=20)
    plt.legend()
    fig.tight_layout()
    
    return save_figure(fig, 'deal_stage_analysis.png', output_dir)


def generate_all_charts(df: pd.DataFrame, output_dir: str = "outputs") -> list:
    """
    Generate all standard charts.
    
    Args:
        df: DataFrame with sales data
        output_dir: Directory to save charts
        
    Returns:
        List of paths to generated charts
    """
    charts = []
    
    print("Generating win rate trend chart...")
    charts.append(plot_quarterly_win_rate_trend(df, output_dir))
    
    print("Generating region-industry heatmap...")
    charts.append(plot_segment_heatmap(df, 'industry', 'region', output_dir))
    
    print("Generating factor comparison charts...")
    for factor in ['region', 'industry', 'product_type', 'lead_source']:
        charts.append(plot_factor_comparison(df, factor, output_dir))
    
    print("Generating rep performance chart...")
    charts.append(plot_rep_performance(df, output_dir=output_dir))
    
    print("Generating deal stage chart...")
    charts.append(plot_deal_stage_funnel(df, output_dir))
    
    print(f"\nGenerated {len(charts)} charts in {output_dir}/")
    return charts


if __name__ == "__main__":
    from data_loader import load_sales_data
    
    df = load_sales_data()
    charts = generate_all_charts(df)
    print("\nGenerated charts:")
    for chart in charts:
        print(f"  - {chart}")
