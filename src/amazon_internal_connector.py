import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

class AmazonInternalDataConnector:
    """
    Connector for Amazon internal data scenarios
    Handles cases where dashboards are in internal accounts but we need similar analytics
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def generate_realistic_content_effectiveness_data(self, num_records: int = 5000) -> pd.DataFrame:
        """
        Generate realistic sample data that matches Amazon's Content Effectiveness patterns
        Based on the structure likely used in Private Pricing and content effectiveness tracking
        """
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic Amazon-style data
        data = {}
        
        # Seller information (Amazon-style IDs)
        seller_count = min(1000, num_records // 3)
        sm_count = seller_count // 10
        
        data['seller_id'] = np.random.choice([f'seller_{i:05d}' for i in range(seller_count)], num_records)
        data['sales_manager_id'] = np.random.choice([f'sm_{i:04d}' for i in range(sm_count)], num_records)
        
        # Time-based data
        start_date = datetime.now() - timedelta(days=365)
        timestamps = pd.date_range(start_date, periods=num_records, freq='2h')
        data['interaction_timestamp'] = timestamps
        data['interaction_date'] = timestamps.date
        
        # Content platform and types
        platforms = ['Highspot', 'Amazon_Learn', 'Internal_Wiki', 'SIM_Portal']
        content_types = [
            'Private_Pricing_Guide', 'Product_Specifications', 'Competitive_Analysis',
            'Training_Materials', 'Deal_Templates', 'Pricing_Calculator',
            'Customer_Case_Studies', 'Technical_Documentation', 'Sales_Playbooks'
        ]
        
        data['platform'] = np.random.choice(platforms, num_records, p=[0.4, 0.25, 0.2, 0.15])
        data['content_type'] = np.random.choice(content_types, num_records)
        
        # Engagement metrics
        data['time_spent_minutes'] = np.random.exponential(8, num_records)  # Average 8 minutes
        data['pages_viewed'] = np.random.poisson(3, num_records) + 1
        data['downloads'] = np.random.binomial(1, 0.3, num_records)  # 30% download rate
        
        # Success metrics
        data['content_found'] = np.random.choice([True, False], num_records, p=[0.78, 0.22])
        data['content_useful'] = np.random.choice([True, False], num_records, p=[0.85, 0.15])
        
        # Accreditation and training
        data['seller_accredited'] = np.random.choice([True, False], num_records, p=[0.72, 0.28])
        data['sm_accredited'] = np.random.choice([True, False], num_records, p=[0.88, 0.12])
        data['recent_training'] = np.random.choice([True, False], num_records, p=[0.45, 0.55])
        
        # Business outcomes
        data['deal_value_usd'] = np.random.lognormal(10.5, 1.2, num_records)  # Realistic deal sizes
        data['deal_cycle_days'] = np.random.gamma(2.5, 28, num_records)  # Average ~70 days
        data['win_probability'] = np.random.beta(2.5, 2, num_records)
        data['actual_win'] = np.random.binomial(1, data['win_probability'], num_records)
        
        # Support and help desk interactions
        data['sim_ticket_created'] = np.random.choice([True, False], num_records, p=[0.12, 0.88])
        data['pp_help_contacted'] = np.random.choice([True, False], num_records, p=[0.08, 0.92])
        data['escalation_required'] = np.random.choice([True, False], num_records, p=[0.05, 0.95])
        
        # Geographic and business unit data
        regions = ['NA_East', 'NA_West', 'EMEA', 'APAC', 'LATAM']
        business_units = ['AWS', 'Retail', 'Advertising', 'Devices', 'Prime', 'Logistics']
        
        data['region'] = np.random.choice(regions, num_records, p=[0.3, 0.25, 0.2, 0.15, 0.1])
        data['business_unit'] = np.random.choice(business_units, num_records, p=[0.35, 0.2, 0.15, 0.1, 0.1, 0.1])
        
        # Customer segment
        segments = ['Enterprise', 'Mid_Market', 'SMB', 'Public_Sector', 'Startup']
        data['customer_segment'] = np.random.choice(segments, num_records, p=[0.4, 0.25, 0.2, 0.1, 0.05])
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Add realistic correlations and business logic
        df = self._add_realistic_correlations(df)
        
        return df
    
    def _add_realistic_correlations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic business correlations to the data"""
        
        # Accredited sellers are more successful
        accredited_mask = df['seller_accredited'] == True
        df.loc[accredited_mask, 'content_found'] = np.random.choice(
            [True, False], sum(accredited_mask), p=[0.88, 0.12]
        )
        
        # Recent training improves content discovery
        training_mask = df['recent_training'] == True
        df.loc[training_mask, 'time_spent_minutes'] *= 0.8  # More efficient
        df.loc[training_mask, 'content_found'] = np.random.choice(
            [True, False], sum(training_mask), p=[0.85, 0.15]
        )
        
        # Both seller and SM accredited = better outcomes
        both_accredited = (df['seller_accredited'] == True) & (df['sm_accredited'] == True)
        df.loc[both_accredited, 'deal_cycle_days'] *= 0.75  # 25% faster
        df.loc[both_accredited, 'win_probability'] *= 1.2   # 20% higher win rate
        df.loc[both_accredited, 'win_probability'] = np.minimum(df.loc[both_accredited, 'win_probability'], 0.95)
        
        # Highspot usage correlations
        highspot_mask = df['platform'] == 'Highspot'
        df.loc[highspot_mask, 'content_found'] = np.random.choice(
            [True, False], sum(highspot_mask), p=[0.82, 0.18]
        )
        
        # Content not found leads to help desk contacts
        not_found_mask = df['content_found'] == False
        df.loc[not_found_mask, 'pp_help_contacted'] = np.random.choice(
            [True, False], sum(not_found_mask), p=[0.25, 0.75]
        )
        df.loc[not_found_mask, 'sim_ticket_created'] = np.random.choice(
            [True, False], sum(not_found_mask), p=[0.35, 0.65]
        )
        
        # Enterprise deals are larger and longer
        enterprise_mask = df['customer_segment'] == 'Enterprise'
        df.loc[enterprise_mask, 'deal_value_usd'] *= 2.5
        df.loc[enterprise_mask, 'deal_cycle_days'] *= 1.4
        
        # AWS business unit has different patterns
        aws_mask = df['business_unit'] == 'AWS'
        df.loc[aws_mask, 'deal_value_usd'] *= 1.8
        df.loc[aws_mask, 'seller_accredited'] = np.random.choice(
            [True, False], sum(aws_mask), p=[0.85, 0.15]
        )
        
        # Update actual wins based on modified probabilities
        df['actual_win'] = np.random.binomial(1, df['win_probability'])
        
        # Calculate derived metrics
        df['content_gap'] = (~df['content_found']) & (df['time_spent_minutes'] > df['time_spent_minutes'].quantile(0.7))
        df['high_value_deal'] = df['deal_value_usd'] > df['deal_value_usd'].quantile(0.8)
        df['fast_cycle'] = df['deal_cycle_days'] < df['deal_cycle_days'].quantile(0.3)
        
        return df
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for the dataset"""
        
        stats = {
            'total_interactions': len(df),
            'unique_sellers': df['seller_id'].nunique(),
            'unique_managers': df['sales_manager_id'].nunique(),
            'date_range': {
                'start': df['interaction_date'].min().strftime('%Y-%m-%d'),
                'end': df['interaction_date'].max().strftime('%Y-%m-%d')
            },
            'content_found_rate': df['content_found'].mean(),
            'avg_time_spent': df['time_spent_minutes'].mean(),
            'avg_deal_value': df['deal_value_usd'].mean(),
            'avg_deal_cycle': df['deal_cycle_days'].mean(),
            'overall_win_rate': df['actual_win'].mean(),
            'pp_help_contact_rate': df['pp_help_contacted'].mean(),
            'sim_ticket_rate': df['sim_ticket_created'].mean(),
            'accreditation_rates': {
                'sellers': df['seller_accredited'].mean(),
                'managers': df['sm_accredited'].mean()
            },
            'platform_usage': df['platform'].value_counts(normalize=True).to_dict(),
            'business_unit_distribution': df['business_unit'].value_counts(normalize=True).to_dict()
        }
        
        return stats

class EnhancedDataLoader:
    """Enhanced data loader that provides realistic Amazon-style data"""
    
    def __init__(self):
        self.connector = AmazonInternalDataConnector()
        self.data_cache = None
        self.last_generated = None
        
    def load_data(self, force_refresh: bool = False) -> pd.DataFrame:
        """Load enhanced sample data"""
        
        if self.data_cache is None or force_refresh:
            self.data_cache = self.connector.generate_realistic_content_effectiveness_data()
            self.last_generated = datetime.now()
            
        return self.data_cache
    
    def get_data_info(self) -> Dict[str, Any]:
        """Get information about the loaded data"""
        
        if self.data_cache is None:
            self.load_data()
            
        return self.connector.get_summary_stats(self.data_cache)