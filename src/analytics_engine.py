import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Any
import logging

class ContentEffectivenessAnalyzer:
    """Core analytics engine for Content Effectiveness Engine"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.insights = {}
        
    def analyze_highspot_effectiveness(self) -> Dict[str, Any]:
        """Analyze Highspot content effectiveness"""
        results = {}
        
        # Calculate key metrics
        total_visits = len(self.data)
        content_found_rate = self.data['content_found'].mean() if 'content_found' in self.data.columns else 0
        
        results['total_visits'] = total_visits
        results['content_found_rate'] = content_found_rate
        results['content_not_found_rate'] = 1 - content_found_rate
        
        # Analyze by accreditation status
        if 'seller_accredited' in self.data.columns:
            accredited_analysis = self.data.groupby('seller_accredited').agg({
                'content_found': 'mean',
                'time_spent_minutes': 'mean',
                'seller_id': 'count'
            }).round(3)
            
            results['accredited_analysis'] = accredited_analysis
            
            # Statistical test for accreditation impact
            accredited_found = self.data[self.data['seller_accredited'] == True]['content_found']
            non_accredited_found = self.data[self.data['seller_accredited'] == False]['content_found']
            
            if len(accredited_found) > 0 and len(non_accredited_found) > 0:
                stat, p_value = stats.ttest_ind(accredited_found, non_accredited_found)
                results['accreditation_significance'] = {
                    'statistic': stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                }
        
        return results
    
    def analyze_deal_cycle_correlation(self) -> Dict[str, Any]:
        """Analyze correlation between Highspot usage and deal cycles"""
        results = {}
        
        # Check for the correct column names in the new data structure
        deal_cycle_col = 'deal_cycle_days' if 'deal_cycle_days' in self.data.columns else None
        time_spent_col = 'time_spent_minutes' if 'time_spent_minutes' in self.data.columns else None
        
        if not deal_cycle_col or not time_spent_col:
            return {'error': 'Required columns for deal cycle analysis not found'}
        
        # Filter data with both metrics
        complete_data = self.data.dropna(subset=[deal_cycle_col, time_spent_col])
        
        if len(complete_data) == 0:
            return {'error': 'No complete data available for correlation analysis'}
        
        # Correlation analysis
        correlation = complete_data[time_spent_col].corr(complete_data[deal_cycle_col])
        results['highspot_usage_deal_cycle_correlation'] = correlation
        
        # Segment analysis: High vs Low usage
        median_usage = complete_data[time_spent_col].median()
        complete_data['usage_segment'] = complete_data[time_spent_col].apply(
            lambda x: 'High Usage' if x > median_usage else 'Low Usage'
        )
        
        # Use win_probability or actual_win if available
        win_col = 'win_probability' if 'win_probability' in complete_data.columns else 'actual_win'
        deal_value_col = 'deal_value_usd' if 'deal_value_usd' in complete_data.columns else 'deal_value'
        
        agg_dict = {deal_cycle_col: ['mean', 'median', 'std']}
        if win_col in complete_data.columns:
            agg_dict[win_col] = 'mean'
        if deal_value_col in complete_data.columns:
            agg_dict[deal_value_col] = 'mean'
        
        segment_analysis = complete_data.groupby('usage_segment').agg(agg_dict).round(2)
        results['usage_segment_analysis'] = segment_analysis
        
        # Statistical significance test
        high_usage_cycles = complete_data[complete_data['usage_segment'] == 'High Usage'][deal_cycle_col]
        low_usage_cycles = complete_data[complete_data['usage_segment'] == 'Low Usage'][deal_cycle_col]
        
        if len(high_usage_cycles) > 0 and len(low_usage_cycles) > 0:
            stat, p_value = stats.ttest_ind(high_usage_cycles, low_usage_cycles)
            results['usage_impact_significance'] = {
                'statistic': stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
        
        return results
    
    def analyze_manager_impact(self) -> Dict[str, Any]:
        """Analyze impact of sales manager accreditation"""
        results = {}
        
        # Create combined accreditation categories
        self.data['accreditation_combo'] = self.data.apply(
            lambda row: f"Seller: {'Yes' if row['seller_accredited'] else 'No'}, "
                       f"SM: {'Yes' if row['sm_accredited'] else 'No'}", axis=1
        )
        
        # Analyze deal performance by accreditation combination
        # Use available columns
        agg_dict = {
            'deal_cycle_days': ['mean', 'count'],
            'content_found': 'mean',
            'time_spent_minutes': 'mean'
        }
        
        # Add win rate column if available
        if 'win_probability' in self.data.columns:
            agg_dict['win_probability'] = 'mean'
        elif 'actual_win' in self.data.columns:
            agg_dict['actual_win'] = 'mean'
        elif 'win_rate' in self.data.columns:
            agg_dict['win_rate'] = 'mean'
        
        combo_analysis = self.data.groupby('accreditation_combo').agg(agg_dict).round(2)
        
        results['accreditation_combo_analysis'] = combo_analysis
        
        # Best performing combination
        if not combo_analysis.empty and 'deal_cycle_days' in combo_analysis.columns:
            best_combo = combo_analysis[('deal_cycle_days', 'mean')].idxmin()
            
            # Get win rate for best combo
            win_rate_col = None
            if 'win_probability' in combo_analysis.columns:
                win_rate_col = ('win_probability', 'mean')
            elif 'actual_win' in combo_analysis.columns:
                win_rate_col = ('actual_win', 'mean')
            elif 'win_rate' in combo_analysis.columns:
                win_rate_col = ('win_rate', 'mean')
            
            results['best_performing_combo'] = {
                'combination': best_combo,
                'avg_deal_cycle': combo_analysis.loc[best_combo, ('deal_cycle_days', 'mean')],
                'win_rate': combo_analysis.loc[best_combo, win_rate_col] if win_rate_col else 0
            }
        
        return results
    
    def identify_content_gaps(self) -> Dict[str, Any]:
        """Identify content gaps and improvement opportunities"""
        results = {}
        
        # Analyze content not found scenarios
        content_not_found = self.data[self.data['content_found'] == False]
        
        if len(content_not_found) > 0:
            # Use the correct column name for content type
            content_col = None
            for col in ['content_type', 'content_accessed', 'content_category']:
                if col in content_not_found.columns:
                    content_col = col
                    break
            
            if content_col:
                gap_analysis = content_not_found.groupby(content_col).agg({
                    'seller_id': 'count',
                    'time_spent_minutes': 'mean'
                }).sort_values('seller_id', ascending=False)
                
                results['content_gaps_by_category'] = gap_analysis
                
                # Calculate gap percentage by category
                total_by_category = self.data.groupby(content_col)['seller_id'].count()
                gap_percentage = (gap_analysis['seller_id'] / total_by_category * 100).round(1)
                results['gap_percentage_by_category'] = gap_percentage
        
        # Analyze high time spent but content not found (indicates search difficulty)
        if len(content_not_found) > 0 and 'time_spent_minutes' in content_not_found.columns:
            difficult_searches = content_not_found[
                content_not_found['time_spent_minutes'] > content_not_found['time_spent_minutes'].quantile(0.75)
            ]
            
            results['difficult_search_scenarios'] = len(difficult_searches)
            results['avg_time_difficult_searches'] = difficult_searches['time_spent_minutes'].mean()
        
        return results
    
    def generate_insights_summary(self) -> Dict[str, Any]:
        """Generate comprehensive insights summary"""
        summary = {}
        
        # Run all analyses
        highspot_analysis = self.analyze_highspot_effectiveness()
        deal_cycle_analysis = self.analyze_deal_cycle_correlation()
        manager_analysis = self.analyze_manager_impact()
        content_gaps = self.identify_content_gaps()
        
        # Key findings
        summary['key_metrics'] = {
            'total_interactions': len(self.data),
            'content_found_rate': f"{highspot_analysis.get('content_found_rate', 0):.1%}",
            'avg_deal_cycle': f"{self.data['deal_cycle_days'].mean():.1f} days" if 'deal_cycle_days' in self.data.columns else 'N/A'
        }
        
        # Actionable insights
        insights = []
        
        if highspot_analysis.get('accreditation_significance', {}).get('significant'):
            insights.append("Seller accreditation significantly impacts content discovery success")
        
        if deal_cycle_analysis.get('usage_impact_significance', {}).get('significant'):
            correlation = deal_cycle_analysis.get('highspot_usage_deal_cycle_correlation', 0)
            if correlation < 0:
                insights.append("Higher Highspot usage correlates with shorter deal cycles")
            else:
                insights.append("Highspot usage patterns may need optimization")
        
        if 'best_performing_combo' in manager_analysis:
            best = manager_analysis['best_performing_combo']
            insights.append(f"Best performance: {best['combination']} "
                          f"(avg {best['avg_deal_cycle']:.1f} day cycles)")
        
        summary['actionable_insights'] = insights
        summary['detailed_analyses'] = {
            'highspot_effectiveness': highspot_analysis,
            'deal_cycle_correlation': deal_cycle_analysis,
            'manager_impact': manager_analysis,
            'content_gaps': content_gaps
        }
        
        return summary
    
    def create_visualizations(self) -> Dict[str, go.Figure]:
        """Create key visualizations"""
        figures = {}
        
        # 1. Content Found Rate by Accreditation
        if 'seller_accredited' in self.data.columns and 'content_found' in self.data.columns:
            accred_data = self.data.groupby('seller_accredited')['content_found'].mean().reset_index()
            accred_data['seller_accredited'] = accred_data['seller_accredited'].map({True: 'Accredited', False: 'Not Accredited'})
            
            fig1 = px.bar(accred_data, x='seller_accredited', y='content_found',
                         title='Content Found Rate by Seller Accreditation',
                         labels={'content_found': 'Content Found Rate', 'seller_accredited': 'Accreditation Status'})
            figures['content_found_by_accreditation'] = fig1
        
        # 2. Deal Cycle vs Highspot Usage
        if 'time_spent_minutes' in self.data.columns and 'deal_cycle_days' in self.data.columns:
            complete_data = self.data.dropna(subset=['deal_cycle_days', 'time_spent_minutes'])
            if len(complete_data) > 0:
                fig2 = px.scatter(complete_data, x='time_spent_minutes', y='deal_cycle_days',
                                 title='Deal Cycle vs Highspot Usage Time',
                                 labels={'time_spent_minutes': 'Time Spent on Highspot (minutes)',
                                        'deal_cycle_days': 'Deal Cycle (days)'})
                figures['deal_cycle_vs_usage'] = fig2
        
        # 3. Content Gaps by Category
        if 'content_accessed' in self.data.columns and 'content_found' in self.data.columns:
            gap_data = self.data.groupby('content_accessed').agg({
                'content_found': lambda x: (x == False).sum(),
                'seller_id': 'count'
            }).reset_index()
            gap_data['gap_rate'] = gap_data['content_found'] / gap_data['seller_id']
            
            fig3 = px.bar(gap_data, x='content_accessed', y='gap_rate',
                         title='Content Gap Rate by Category',
                         labels={'gap_rate': 'Gap Rate', 'content_accessed': 'Content Category'})
            figures['content_gaps'] = fig3
        
        return figures