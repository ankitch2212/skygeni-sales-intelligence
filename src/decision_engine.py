"""
SkyGeni Sales Intelligence - Decision Engine Module
Option B: Win Rate Driver Analysis

Identifies which factors are hurting or improving win rate using
statistical analysis and provides actionable recommendations.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from src.metrics import calculate_deal_velocity_score, calculate_all_rep_momentum


# Minimum deals required before generating a segment-level insight.
# Matches the global threshold in main.py.
MIN_DEALS_FOR_INSIGHT = 100


class WinRateDriverAnalyzer:
    """
    Analyzes factors affecting win rate and identifies key drivers.
    Uses chi-square tests for categorical variables and provides
    actionable insights for sales leaders.
    
    Alternative considered:
    Predictive ML models (e.g., gradient boosting).
    Rejected due to lower interpretability and higher overfitting risk
    for CRO-facing decisions. A sales leader needs to understand *why*
    a recommendation is made, not just trust a black-box score.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the analyzer with sales data.
        
        Args:
            df: DataFrame with sales data including 'is_won' column
        """
        self.df = df
        self.overall_win_rate = df['is_won'].mean() * 100
        self.total_deals = len(df)
        self.factors = ['region', 'industry', 'product_type', 
                        'lead_source', 'deal_stage', 'sales_rep_id']
        self.results = {}
    
    def analyze_factor_impact(self, factor: str) -> Dict[str, Any]:
        """
        Analyze impact of a single factor on win rate.
        
        Args:
            factor: Column name to analyze
            
        Returns:
            Dictionary with statistical analysis results
        """
        # Create contingency table
        contingency = pd.crosstab(self.df[factor], self.df['is_won'])
        
        # Guard: skip statistically fragile segments with too few deals
        if contingency.values.sum() < MIN_DEALS_FOR_INSIGHT:
            return None  # Skip statistically fragile segments
        
        # Perform chi-square test
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
        
        # Calculate win rates by category
        factor_stats = self.df.groupby(factor).agg({
            'deal_id': 'count',
            'is_won': 'mean',
            'deal_amount': 'sum'
        }).reset_index()
        factor_stats.columns = [factor, 'deal_count', 'win_rate', 'total_revenue']
        factor_stats['win_rate'] = factor_stats['win_rate'] * 100
        factor_stats['win_rate_diff'] = factor_stats['win_rate'] - self.overall_win_rate
        
        # Calculate effect size (Cramer's V)
        n = contingency.sum().sum()
        min_dim = min(contingency.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
        
        return {
            'factor': factor,
            'chi_square': chi2,
            'p_value': p_value,
            'degrees_of_freedom': dof,
            'cramers_v': cramers_v,
            'significant': p_value < 0.05,
            'effect_size': 'large' if cramers_v > 0.25 else 'medium' if cramers_v > 0.15 else 'small',
            'category_stats': factor_stats.to_dict('records'),
            'best_category': factor_stats.loc[factor_stats['win_rate'].idxmax(), factor],
            'worst_category': factor_stats.loc[factor_stats['win_rate'].idxmin(), factor],
            'best_win_rate': factor_stats['win_rate'].max(),
            'worst_win_rate': factor_stats['win_rate'].min(),
            'spread': factor_stats['win_rate'].max() - factor_stats['win_rate'].min()
        }
    
    def analyze_all_factors(self) -> Dict[str, Dict]:
        """
        Analyze impact of all factors on win rate.
        
        Returns:
            Dictionary with analysis results for each factor
        """
        for factor in self.factors:
            result = self.analyze_factor_impact(factor)
            if result is not None:
                self.results[factor] = result
        
        # Rank factors by impact (Cramer's V)
        factor_ranking = sorted(
            self.results.items(),
            key=lambda x: x[1]['cramers_v'],
            reverse=True
        )
        
        self.factor_ranking = [f[0] for f in factor_ranking]
        return self.results
    
    def get_top_drivers(self, n: int = 3) -> List[Dict]:
        """
        Get the top N factors affecting win rate.
        
        Args:
            n: Number of top factors to return
            
        Returns:
            List of top factor analysis results
        """
        if not self.results:
            self.analyze_all_factors()
        
        sorted_factors = sorted(
            self.results.items(),
            key=lambda x: x[1]['cramers_v'],
            reverse=True
        )
        
        return [v for k, v in sorted_factors[:n]]
    
    def get_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify specific improvement opportunities based on analysis.
        
        Returns:
            List of improvement opportunities with actionable recommendations
        """
        if not self.results:
            self.analyze_all_factors()
        
        opportunities = []
        
        for factor, result in self.results.items():
            if factor == 'sales_rep_id':
                continue  # Handle reps separately
            
            for cat_stat in result['category_stats']:
                diff = cat_stat['win_rate_diff']
                if diff < -5 and cat_stat['deal_count'] > 100:  # Underperforming + significant volume
                    opportunity = {
                        'factor': factor,
                        'category': cat_stat[factor],
                        'current_win_rate': round(cat_stat['win_rate'], 1),
                        'vs_average': round(diff, 1),
                        'deal_count': cat_stat['deal_count'],
                        'potential_additional_wins': int(abs(diff) / 100 * cat_stat['deal_count']),
                        'priority': 'High' if diff < -10 else 'Medium',
                        'recommendation': self._generate_recommendation(factor, cat_stat, diff)
                    }
                    opportunities.append(opportunity)
        
        # Sort by potential impact
        return sorted(opportunities, key=lambda x: x['potential_additional_wins'], reverse=True)
    
    def _generate_recommendation(self, factor: str, stats: Dict, diff: float) -> str:
        """Generate actionable recommendation for a problem area."""
        category = stats[factor]
        
        recommendations = {
            'region': f"Analyze {category} sales process. Consider region-specific training, "
                      f"local competitive analysis, or resource reallocation.",
            'industry': f"Review {category} vertical strategy. May need industry-specific "
                        f"value propositions, case studies, or specialized sales support.",
            'product_type': f"Evaluate {category} pricing, positioning, and competitive landscape. "
                            f"Consider product training for sales team.",
            'lead_source': f"Assess quality of {category} leads with marketing. May need "
                           f"better lead qualification criteria or nurturing programs.",
            'deal_stage': f"Investigate objections causing drop-off at {category} stage. "
                          f"Review sales enablement materials and talk tracks."
        }
        
        return recommendations.get(factor, f"Investigate root cause for {category} underperformance.")
    
    def get_rep_performance_tiers(self) -> Dict[str, List[str]]:
        """
        Categorize sales reps into performance tiers.
        
        Returns:
            Dictionary with lists of reps by tier
        """
        result = self.analyze_factor_impact('sales_rep_id')
        
        tiers = {
            'top_performers': [],
            'solid_performers': [],
            'needs_improvement': [],
            'at_risk': []
        }
        
        for stat in result['category_stats']:
            rep = stat['sales_rep_id']
            rate = stat['win_rate']
            count = stat['deal_count']
            
            if count < 50:  # Not enough data
                continue
            
            if rate >= self.overall_win_rate + 10:
                tiers['top_performers'].append((rep, rate, count))
            elif rate >= self.overall_win_rate:
                tiers['solid_performers'].append((rep, rate, count))
            elif rate >= self.overall_win_rate - 10:
                tiers['needs_improvement'].append((rep, rate, count))
            else:
                tiers['at_risk'].append((rep, rate, count))
        
        return tiers
    
    def generate_executive_summary(self) -> str:
        """
        Generate an executive summary of the win rate driver analysis.
        
        Returns:
            Formatted string with executive summary
        """
        if not self.results:
            self.analyze_all_factors()
        
        top_drivers = self.get_top_drivers(3)
        opportunities = self.get_improvement_opportunities()[:5]
        rep_tiers = self.get_rep_performance_tiers()
        
        summary = []
        summary.append("=" * 60)
        summary.append("WIN RATE DRIVER ANALYSIS - EXECUTIVE SUMMARY")
        summary.append("=" * 60)
        summary.append(f"\nOverall Win Rate: {self.overall_win_rate:.1f}%")
        summary.append(f"Total Deals Analyzed: {self.total_deals:,}")
        
        summary.append("\n" + "-" * 40)
        summary.append("TOP FACTORS AFFECTING WIN RATE")
        summary.append("-" * 40)
        
        for i, driver in enumerate(top_drivers, 1):
            significance = "***" if driver['significant'] else ""
            summary.append(f"\n{i}. {driver['factor'].upper()} (Effect: {driver['effect_size']}) {significance}")
            summary.append(f"   Best: {driver['best_category']} ({driver['best_win_rate']:.1f}%)")
            summary.append(f"   Worst: {driver['worst_category']} ({driver['worst_win_rate']:.1f}%)")
            summary.append(f"   Spread: {driver['spread']:.1f} percentage points")
        
        summary.append("\n" + "-" * 40)
        summary.append("TOP IMPROVEMENT OPPORTUNITIES")
        summary.append("-" * 40)
        
        for opp in opportunities:
            summary.append(f"\n• {opp['factor']}: {opp['category']}")
            summary.append(f"  Current: {opp['current_win_rate']}% | Gap: {opp['vs_average']}pp")
            summary.append(f"  Potential wins if improved: +{opp['potential_additional_wins']} deals")
            summary.append(f"  Action: {opp['recommendation']}")
        
        summary.append("\n" + "-" * 40)
        summary.append("SALES REP PERFORMANCE DISTRIBUTION")
        summary.append("-" * 40)
        
        summary.append(f"\n  Top Performers (>{self.overall_win_rate + 10:.0f}%): {len(rep_tiers['top_performers'])} reps")
        summary.append(f"  Solid Performers: {len(rep_tiers['solid_performers'])} reps")
        summary.append(f"  Needs Improvement: {len(rep_tiers['needs_improvement'])} reps")
        summary.append(f"  At Risk (<{self.overall_win_rate - 10:.0f}%): {len(rep_tiers['at_risk'])} reps")
        
        if rep_tiers['at_risk']:
            summary.append("\n  At-Risk Reps (prioritize for coaching):")
            for rep, rate, count in sorted(rep_tiers['at_risk'], key=lambda x: x[1])[:5]:
                summary.append(f"    - {rep}: {rate:.1f}% win rate ({count} deals)")
        
        # --- NEW: Strategic Metrics Summary ---
        summary.append("\n" + "-" * 40)
        summary.append("STRATEGIC METRICS SUMMARY")
        summary.append("-" * 40)
        
        # 1. Deal Velocity Score (if in df or calculable)
        if 'velocity_score' not in self.df.columns:
            self.df['velocity_score'] = calculate_deal_velocity_score(self.df)
        
        avg_velocity = self.df[self.df['is_won'] == 1]['velocity_score'].mean()
        summary.append(f"\n• Avg Deal Velocity (Won Deals): ${avg_velocity:,.0f}/day")
        
        # Top segments by velocity
        top_vel_industry = self.df[self.df['is_won'] == 1].groupby('industry')['velocity_score'].mean().idxmax()
        top_vel_val = self.df[self.df['is_won'] == 1].groupby('industry')['velocity_score'].mean().max()
        summary.append(f"  Highest Velocity Industry: {top_vel_industry} (${top_vel_val:,.0f}/day)")
        
        # 2. Rep Momentum
        momentum_df = calculate_all_rep_momentum(self.df)
        improving = len(momentum_df[momentum_df['momentum_index'] > 1.1])
        declining = len(momentum_df[momentum_df['momentum_index'] < 0.9])
        summary.append(f"\n• Rep Momentum Status:")
        summary.append(f"  Improving (>1.1): {improving} reps")
        summary.append(f"  Declining (<0.9): {declining} reps")
        
        # Explicit framing: these are hypotheses, not verdicts
        summary.append("")
        summary.append(
            "NOTE: Identified drivers indicate correlation, not causation. "
            "They are intended to guide investigation, not automate decisions."
        )
        
        return "\n".join(summary)
    
    def get_actionable_outputs(self) -> Dict[str, Any]:
        """
        Generate outputs formatted for a sales leader dashboard.
        
        Returns:
            Dictionary with structured outputs for each audience
        """
        if not self.results:
            self.analyze_all_factors()
        
        return {
            'summary_metrics': {
                'overall_win_rate': round(self.overall_win_rate, 1),
                'total_deals': self.total_deals,
                'factor_ranking': self.factor_ranking
            },
            'factor_analysis': self.results,
            'improvement_opportunities': self.get_improvement_opportunities(),
            'rep_tiers': self.get_rep_performance_tiers(),
            'executive_summary': self.generate_executive_summary()
        }


def run_win_rate_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Main function to run win rate driver analysis.
    
    Args:
        df: DataFrame with sales data
        
    Returns:
        Dictionary with all analysis outputs
    """
    analyzer = WinRateDriverAnalyzer(df)
    return analyzer.get_actionable_outputs()


if __name__ == "__main__":
    from data_loader import load_sales_data
    
    df = load_sales_data()
    
    analyzer = WinRateDriverAnalyzer(df)
    analyzer.analyze_all_factors()
    
    # Print executive summary
    print(analyzer.generate_executive_summary())
    
    # Print detailed improvements
    print("\n\n" + "=" * 60)
    print("DETAILED IMPROVEMENT OPPORTUNITIES")
    print("=" * 60)
    
    for opp in analyzer.get_improvement_opportunities():
        print(f"\n{opp['factor'].upper()}: {opp['category']}")
        print(f"  Priority: {opp['priority']}")
        print(f"  Current Win Rate: {opp['current_win_rate']}%")
        print(f"  Gap vs Average: {opp['vs_average']}pp")
        print(f"  Deal Volume: {opp['deal_count']} deals")
        print(f"  Potential Wins: +{opp['potential_additional_wins']} if improved")
        print(f"  Recommendation: {opp['recommendation']}")
