import boto3
import pandas as pd
import os
from typing import Dict, List, Optional
import logging
from .quicksight_connector import ContentEffectivenessDataLoader
from .amazon_internal_connector import EnhancedDataLoader

class QuickSightConnector:
    """Handles secure connections to QuickSight datasets"""
    
    def __init__(self):
        self.quicksight_client = boto3.client(
            'quicksight',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.account_id = os.getenv('QUICKSIGHT_ACCOUNT_ID')
        self.namespace = os.getenv('QUICKSIGHT_NAMESPACE', 'default')
        
    def get_dataset_data(self, dataset_id: str) -> pd.DataFrame:
        """Retrieve data from QuickSight dataset"""
        try:
            # Get dataset metadata
            response = self.quicksight_client.describe_dataset(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id
            )
            
            # For now, we'll simulate data retrieval
            # In production, you'd use QuickSight APIs or direct data source connection
            logging.info(f"Retrieved dataset: {dataset_id}")
            
            # Placeholder - replace with actual data retrieval logic
            return self._get_sample_data(dataset_id)
            
        except Exception as e:
            logging.error(f"Error retrieving dataset {dataset_id}: {str(e)}")
            return pd.DataFrame()
    
    def _get_sample_data(self, dataset_id: str) -> pd.DataFrame:
        """Generate sample data for testing - replace with actual data"""
        if 'highspot' in dataset_id.lower():
            return self._generate_highspot_data()
        elif 'sim' in dataset_id.lower():
            return self._generate_sim_data()
        elif 'amazon' in dataset_id.lower():
            return self._generate_amazon_learn_data()
        else:
            return pd.DataFrame()
    
    def _generate_highspot_data(self) -> pd.DataFrame:
        """Sample Highspot interaction data"""
        import numpy as np
        np.random.seed(42)
        
        n_records = 1000
        data = {
            'seller_id': [f'S{i:04d}' for i in range(n_records)],
            'sales_manager_id': [f'SM{i//10:03d}' for i in range(n_records)],
            'visit_date': pd.date_range('2024-01-01', periods=n_records, freq='D'),
            'content_accessed': np.random.choice(['Private_Pricing', 'Product_Info', 'Competitive', 'Training'], n_records),
            'time_spent_minutes': np.random.exponential(15, n_records),
            'seller_accredited': np.random.choice([True, False], n_records, p=[0.7, 0.3]),
            'sm_accredited': np.random.choice([True, False], n_records, p=[0.8, 0.2]),
            'content_found': np.random.choice([True, False], n_records, p=[0.85, 0.15])
        }
        return pd.DataFrame(data)
    
    def _generate_sim_data(self) -> pd.DataFrame:
        """Sample SIM ticket data"""
        import numpy as np
        np.random.seed(43)
        
        n_records = 500
        data = {
            'ticket_id': [f'SIM{i:05d}' for i in range(n_records)],
            'seller_id': [f'S{i:04d}' for i in np.random.randint(0, 1000, n_records)],
            'submission_date': pd.date_range('2024-01-01', periods=n_records, freq='2D'),
            'deal_value': np.random.lognormal(10, 1, n_records),
            'deal_cycle_days': np.random.gamma(2, 30, n_records),
            'win_rate': np.random.beta(2, 3, n_records),
            'content_category': np.random.choice(['Private_Pricing', 'Product_Config', 'Competitive'], n_records),
            'resolution_time_hours': np.random.exponential(24, n_records)
        }
        return pd.DataFrame(data)
    
    def _generate_amazon_learn_data(self) -> pd.DataFrame:
        """Sample Amazon Learn completion data"""
        import numpy as np
        np.random.seed(44)
        
        n_records = 800
        data = {
            'seller_id': [f'S{i:04d}' for i in np.random.randint(0, 1000, n_records)],
            'course_name': np.random.choice(['Private_Pricing_101', 'Advanced_Negotiation', 'Product_Deep_Dive'], n_records),
            'completion_date': pd.date_range('2024-01-01', periods=n_records, freq='3D'),
            'score': np.random.normal(85, 10, n_records),
            'time_to_complete_hours': np.random.gamma(2, 5, n_records),
            'certification_earned': np.random.choice([True, False], n_records, p=[0.6, 0.4])
        }
        return pd.DataFrame(data)

class DataIntegrator:
    """Integrates data from multiple sources for analysis"""
    
    def __init__(self):
        # Use enhanced Amazon-style data loader
        self.enhanced_loader = EnhancedDataLoader()
        # Keep the QuickSight loader for future use
        self.cee_loader = ContentEffectivenessDataLoader()
        self.datasets = {}
        self.connection_tested = False
        
    def load_all_datasets(self):
        """Load all required datasets"""
        # For now, use the enhanced Amazon-style sample data
        # This provides realistic data that matches your use case
        self.datasets['integrated'] = self.enhanced_loader.load_data()
            
    def get_integrated_data(self) -> pd.DataFrame:
        """Get the integrated dataset"""
        if not self.datasets:
            self.load_all_datasets()
            
        return self.datasets.get('integrated', pd.DataFrame())
    
    def get_connection_status(self) -> Dict:
        """Get connection status information"""
        if not self.connection_tested:
            # Test QuickSight connection
            qs_status = self.cee_loader.get_connection_info()
            self.connection_tested = True
            
            # Add information about data source
            qs_status['data_source'] = 'Enhanced Amazon-style sample data'
            qs_status['note'] = 'Target dashboard is in Amazon internal account. Using realistic sample data.'
            
            return qs_status
        else:
            return {
                'connection_status': 'success',
                'account_id': os.getenv('QUICKSIGHT_ACCOUNT_ID'),
                'dashboard_found': False,
                'data_source': 'Enhanced Amazon-style sample data',
                'message': 'Using enhanced sample data matching Amazon Content Effectiveness patterns'
            }
    
    def refresh_data(self) -> pd.DataFrame:
        """Force refresh data"""
        self.datasets['integrated'] = self.enhanced_loader.load_data(force_refresh=True)
        return self.datasets['integrated']
    
    def get_data_summary(self) -> Dict:
        """Get summary information about the loaded data"""
        return self.enhanced_loader.get_data_info()