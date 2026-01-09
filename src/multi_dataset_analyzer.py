import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime
import re

class MultiDatasetAnalyzer:
    """Analyze multiple datasets simultaneously for cross-dataset insights"""
    
    def __init__(self):
        self.datasets = {}  # {name: {'data': df, 'analyzer': analyzer, 'metadata': {}}}
        self.logger = logging.getLogger(__name__)
        
    def add_dataset(self, name: str, data: pd.DataFrame, metadata: Dict[str, Any] = None):
        """Add a dataset to the multi-dataset analyzer"""
        from .advanced_nlp_analyzer import AdvancedNLPAnalyzer
        
        self.datasets[name] = {
            'data': data,
            'analyzer': AdvancedNLPAnalyzer(data),
            'metadata': metadata or {},
            'added_at': datetime.now()
        }
        
        self.logger.info(f"Added dataset '{name}' with {len(data)} rows and {len(data.columns)} columns")
    
    def remove_dataset(self, name: str):
        """Remove a dataset"""
        if name in self.datasets:
            del self.datasets[name]
            self.logger.info(f"Removed dataset '{name}'")
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all loaded datasets with summary info"""
        dataset_list = []
        
        for name, info in self.datasets.items():
            data = info['data']
            dataset_list.append({
                'name': name,
                'rows': len(data),
                'columns': len(data.columns),
                'size_mb': data.memory_usage(deep=True).sum() / 1024 / 1024,
                'added_at': info['added_at'],
                'column_names': list(data.columns),
                'numeric_columns': data.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical_columns': data.select_dtypes(include=['object', 'category']).columns.tolist(),
                'date_columns': data.select_dtypes(include=['datetime64']).columns.tolist()
            })
        
        return dataset_list
    
    def find_common_columns(self) -> Dict[str, List[str]]:
        """Find columns that appear across multiple datasets"""
        if len(self.datasets) < 2:
            return {}
        
        all_columns = {}
        for name, info in self.datasets.items():
            for col in info['data'].columns:
                col_lower = col.lower().strip()
                if col_lower not in all_columns:
                    all_columns[col_lower] = []
                all_columns[col_lower].append((name, col))
        
        # Find columns that appear in multiple datasets
        common_columns = {}
        for col_lower, appearances in all_columns.items():
            if len(appearances) > 1:
                common_columns[col_lower] = appearances
        
        return common_columns
    
    def find_similar_columns(self, similarity_threshold: float = 0.7) -> Dict[str, List[Tuple[str, str, float]]]:
        """Find columns with similar names across datasets"""
        from difflib import SequenceMatcher
        
        similar_columns = {}
        dataset_names = list(self.datasets.keys())
        
        for i, name1 in enumerate(dataset_names):
            for j, name2 in enumerate(dataset_names[i+1:], i+1):
                cols1 = self.datasets[name1]['data'].columns
                cols2 = self.datasets[name2]['data'].columns
                
                for col1 in cols1:
                    for col2 in cols2:
                        similarity = SequenceMatcher(None, col1.lower(), col2.lower()).ratio()
                        if similarity >= similarity_threshold and col1.lower() != col2.lower():
                            key = f"{name1}_{col1}___{name2}_{col2}"
                            similar_columns[key] = (name1, col1, name2, col2, similarity)
        
        return similar_columns
    
    def compare_datasets_summary(self) -> Dict[str, Any]:
        """Generate comprehensive comparison of all datasets"""
        if not self.datasets:
            return {'error': 'No datasets loaded'}
        
        comparison = {
            'total_datasets': len(self.datasets),
            'dataset_summaries': {},
            'common_columns': self.find_common_columns(),
            'similar_columns': self.find_similar_columns(),
            'size_comparison': {},
            'column_overlap': {}
        }
        
        # Individual dataset summaries
        for name, info in self.datasets.items():
            data = info['data']
            comparison['dataset_summaries'][name] = {
                'rows': len(data),
                'columns': len(data.columns),
                'memory_mb': data.memory_usage(deep=True).sum() / 1024 / 1024,
                'missing_values': data.isnull().sum().sum(),
                'numeric_columns': len(data.select_dtypes(include=[np.number]).columns),
                'categorical_columns': len(data.select_dtypes(include=['object', 'category']).columns),
                'date_columns': len(data.select_dtypes(include=['datetime64']).columns)
            }
        
        # Size comparison
        sizes = [(name, info['data'].memory_usage(deep=True).sum() / 1024 / 1024) 
                for name, info in self.datasets.items()]
        sizes.sort(key=lambda x: x[1], reverse=True)
        comparison['size_comparison'] = {
            'largest': sizes[0] if sizes else None,
            'smallest': sizes[-1] if sizes else None,
            'total_memory_mb': sum(size[1] for size in sizes)
        }
        
        return comparison
    
    def analyze_cross_dataset_correlations(self, column_mapping: Dict[str, List[Tuple[str, str]]]) -> Dict[str, Any]:
        """Analyze correlations between similar columns across datasets"""
        correlations = {}
        
        for concept, dataset_columns in column_mapping.items():
            if len(dataset_columns) < 2:
                continue
            
            # Extract data for each dataset
            concept_data = {}
            for dataset_name, column_name in dataset_columns:
                if dataset_name in self.datasets:
                    data = self.datasets[dataset_name]['data'][column_name]
                    if pd.api.types.is_numeric_dtype(data):
                        concept_data[f"{dataset_name}_{column_name}"] = data
            
            if len(concept_data) >= 2:
                # Create correlation matrix for this concept
                concept_df = pd.DataFrame(concept_data)
                corr_matrix = concept_df.corr()
                
                correlations[concept] = {
                    'correlation_matrix': corr_matrix,
                    'datasets_involved': list(concept_data.keys()),
                    'strongest_correlation': self._find_strongest_correlation(corr_matrix)
                }
        
        return correlations
    
    def _find_strongest_correlation(self, corr_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Find the strongest correlation in a correlation matrix"""
        if corr_matrix.empty or len(corr_matrix) < 2:
            return {}
        
        # Get upper triangle (excluding diagonal)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        correlations = corr_matrix.where(mask).stack().dropna()
        
        if correlations.empty:
            return {}
        
        strongest_idx = correlations.abs().idxmax()
        strongest_value = correlations[strongest_idx]
        
        return {
            'columns': strongest_idx,
            'correlation': strongest_value,
            'strength': 'Strong' if abs(strongest_value) > 0.7 else 'Moderate' if abs(strongest_value) > 0.3 else 'Weak'
        }
    
    def analyze_trends_across_datasets(self, date_column_mapping: Dict[str, List[Tuple[str, str]]], 
                                     value_column_mapping: Dict[str, List[Tuple[str, str]]]) -> Dict[str, Any]:
        """Analyze trends across datasets with time series data"""
        trends = {}
        
        for concept, date_mappings in date_column_mapping.items():
            if concept not in value_column_mapping:
                continue
            
            value_mappings = value_column_mapping[concept]
            trend_data = {}
            
            # Extract time series data from each dataset
            for (dataset_name, date_col), (val_dataset, value_col) in zip(date_mappings, value_mappings):
                if dataset_name == val_dataset and dataset_name in self.datasets:
                    data = self.datasets[dataset_name]['data']
                    
                    if date_col in data.columns and value_col in data.columns:
                        # Group by date and aggregate
                        try:
                            date_data = pd.to_datetime(data[date_col])
                            ts_data = data.groupby(date_data.dt.date)[value_col].mean()
                            trend_data[dataset_name] = ts_data
                        except Exception as e:
                            self.logger.warning(f"Could not process time series for {dataset_name}: {str(e)}")
            
            if trend_data:
                trends[concept] = {
                    'datasets': list(trend_data.keys()),
                    'time_series': trend_data,
                    'trend_analysis': self._analyze_trend_patterns(trend_data)
                }
        
        return trends
    
    def _analyze_trend_patterns(self, trend_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Analyze patterns in trend data"""
        analysis = {
            'dataset_trends': {},
            'correlation_between_trends': {},
            'synchronized_periods': []
        }
        
        # Analyze individual trends
        for dataset_name, series in trend_data.items():
            if len(series) > 1:
                # Calculate trend direction
                slope = np.polyfit(range(len(series)), series.values, 1)[0]
                analysis['dataset_trends'][dataset_name] = {
                    'direction': 'Increasing' if slope > 0 else 'Decreasing' if slope < 0 else 'Stable',
                    'slope': slope,
                    'volatility': series.std(),
                    'mean_value': series.mean()
                }
        
        # Analyze correlations between trends
        if len(trend_data) >= 2:
            # Align time series and calculate correlations
            aligned_data = pd.DataFrame(trend_data).dropna()
            if len(aligned_data) > 1:
                corr_matrix = aligned_data.corr()
                analysis['correlation_between_trends'] = corr_matrix.to_dict()
        
        return analysis
    
    def generate_cross_dataset_insights(self) -> List[str]:
        """Generate insights from cross-dataset analysis"""
        insights = []
        
        if len(self.datasets) < 2:
            insights.append("Load at least 2 datasets to generate cross-dataset insights.")
            return insights
        
        # Dataset size insights
        comparison = self.compare_datasets_summary()
        dataset_summaries = comparison['dataset_summaries']
        
        # Size comparison insights
        sizes = [(name, summary['memory_mb']) for name, summary in dataset_summaries.items()]
        sizes.sort(key=lambda x: x[1], reverse=True)
        
        if len(sizes) >= 2:
            largest = sizes[0]
            smallest = sizes[-1]
            size_ratio = largest[1] / smallest[1] if smallest[1] > 0 else float('inf')
            
            if size_ratio > 10:
                insights.append(f"📊 Dataset '{largest[0]}' is {size_ratio:.1f}x larger than '{smallest[0]}' - consider data sampling for balanced analysis.")
        
        # Common columns insights
        common_cols = comparison['common_columns']
        if common_cols:
            insights.append(f"🔗 Found {len(common_cols)} common column patterns across datasets - potential for data integration.")
            
            # Highlight most common patterns
            most_common = max(common_cols.items(), key=lambda x: len(x[1]))
            datasets_with_pattern = [appearance[0] for appearance in most_common[1]]
            insights.append(f"📋 Column pattern '{most_common[0]}' appears in {len(datasets_with_pattern)} datasets: {', '.join(datasets_with_pattern)}")
        
        # Row count insights
        row_counts = [(name, summary['rows']) for name, summary in dataset_summaries.items()]
        total_rows = sum(count[1] for count in row_counts)
        avg_rows = total_rows / len(row_counts)
        
        outliers = [name for name, rows in row_counts if abs(rows - avg_rows) > avg_rows * 0.5]
        if outliers:
            insights.append(f"📈 Datasets with unusual row counts detected: {', '.join(outliers)} - may need different analysis approaches.")
        
        # Missing data insights
        missing_data = [(name, summary['missing_values']) for name, summary in dataset_summaries.items()]
        high_missing = [name for name, missing in missing_data if missing > summary['rows'] * 0.1]
        
        if high_missing:
            insights.append(f"⚠️ High missing data detected in: {', '.join(high_missing)} - consider data quality assessment.")
        
        # Column type distribution insights
        numeric_ratios = [(name, summary['numeric_columns'] / summary['columns']) 
                         for name, summary in dataset_summaries.items() if summary['columns'] > 0]
        
        highly_numeric = [name for name, ratio in numeric_ratios if ratio > 0.7]
        highly_categorical = [name for name, ratio in numeric_ratios if ratio < 0.3]
        
        if highly_numeric:
            insights.append(f"🔢 Highly numeric datasets: {', '.join(highly_numeric)} - good for statistical analysis and correlations.")
        
        if highly_categorical:
            insights.append(f"📊 Highly categorical datasets: {', '.join(highly_categorical)} - good for segmentation and classification analysis.")
        
        return insights
    
    def create_cross_dataset_visualizations(self) -> Dict[str, go.Figure]:
        """Create visualizations comparing datasets"""
        figures = {}
        
        if not self.datasets:
            return figures
        
        # Dataset size comparison
        dataset_info = [(name, len(info['data']), len(info['data'].columns), 
                        info['data'].memory_usage(deep=True).sum() / 1024 / 1024)
                       for name, info in self.datasets.items()]
        
        if dataset_info:
            names, rows, cols, sizes = zip(*dataset_info)
            
            # Size comparison chart
            fig_size = go.Figure()
            fig_size.add_trace(go.Bar(name='Rows', x=names, y=rows, yaxis='y'))
            fig_size.add_trace(go.Bar(name='Columns', x=names, y=cols, yaxis='y2'))
            
            fig_size.update_layout(
                title='Dataset Size Comparison',
                xaxis=dict(title='Datasets'),
                yaxis=dict(title='Number of Rows', side='left'),
                yaxis2=dict(title='Number of Columns', side='right', overlaying='y'),
                barmode='group'
            )
            figures['size_comparison'] = fig_size
            
            # Memory usage chart
            fig_memory = px.pie(values=sizes, names=names, title='Memory Usage Distribution')
            figures['memory_usage'] = fig_memory
        
        # Column type distribution
        if len(self.datasets) > 1:
            type_data = []
            for name, info in self.datasets.items():
                data = info['data']
                numeric_cols = len(data.select_dtypes(include=[np.number]).columns)
                categorical_cols = len(data.select_dtypes(include=['object', 'category']).columns)
                date_cols = len(data.select_dtypes(include=['datetime64']).columns)
                
                type_data.extend([
                    {'Dataset': name, 'Type': 'Numeric', 'Count': numeric_cols},
                    {'Dataset': name, 'Type': 'Categorical', 'Count': categorical_cols},
                    {'Dataset': name, 'Type': 'Date/Time', 'Count': date_cols}
                ])
            
            if type_data:
                type_df = pd.DataFrame(type_data)
                fig_types = px.bar(type_df, x='Dataset', y='Count', color='Type',
                                 title='Column Type Distribution Across Datasets')
                figures['column_types'] = fig_types
        
        return figures
    
    def process_multi_dataset_query(self, query: str) -> Dict[str, Any]:
        """Process queries that span multiple datasets"""
        query_lower = query.lower()
        
        # Detect cross-dataset query patterns
        if any(word in query_lower for word in ['compare', 'versus', 'vs', 'between', 'across']):
            return self._handle_comparison_query(query)
        elif any(word in query_lower for word in ['combine', 'merge', 'join', 'together']):
            return self._handle_combination_query(query)
        elif any(word in query_lower for word in ['trend', 'over time', 'timeline', 'pattern']):
            return self._handle_trend_query(query)
        elif any(word in query_lower for word in ['correlation', 'relationship', 'related']):
            return self._handle_correlation_query(query)
        else:
            return self._handle_general_multi_query(query)
    
    def _handle_comparison_query(self, query: str) -> Dict[str, Any]:
        """Handle queries comparing datasets"""
        comparison = self.compare_datasets_summary()
        insights = self.generate_cross_dataset_insights()
        
        answer = f"Dataset Comparison Summary:\n\n"
        
        for name, summary in comparison['dataset_summaries'].items():
            answer += f"📊 **{name}**: {summary['rows']:,} rows, {summary['columns']} columns, {summary['memory_mb']:.1f}MB\n"
        
        answer += f"\n💡 **Key Insights:**\n"
        for insight in insights[:3]:
            answer += f"• {insight}\n"
        
        return {
            'success': True,
            'answer': answer,
            'type': 'comparison',
            'data': comparison
        }
    
    def _handle_combination_query(self, query: str) -> Dict[str, Any]:
        """Handle queries about combining datasets"""
        common_cols = self.find_common_columns()
        similar_cols = self.find_similar_columns()
        
        answer = "Dataset Combination Analysis:\n\n"
        
        if common_cols:
            answer += f"🔗 **Common Columns Found** ({len(common_cols)}):\n"
            for col_pattern, appearances in list(common_cols.items())[:5]:
                datasets = [app[0] for app in appearances]
                answer += f"• '{col_pattern}' in: {', '.join(datasets)}\n"
        
        if similar_cols:
            answer += f"\n🔍 **Similar Columns** ({len(similar_cols)}):\n"
            for key, (ds1, col1, ds2, col2, similarity) in list(similar_cols.items())[:3]:
                answer += f"• {ds1}.{col1} ↔ {ds2}.{col2} ({similarity:.1%} similar)\n"
        
        if not common_cols and not similar_cols:
            answer += "⚠️ No obvious column matches found. Manual mapping may be required for combination."
        
        return {
            'success': True,
            'answer': answer,
            'type': 'combination',
            'common_columns': common_cols,
            'similar_columns': similar_cols
        }
    
    def _handle_trend_query(self, query: str) -> Dict[str, Any]:
        """Handle trend analysis queries"""
        # Look for date columns across datasets
        date_columns = {}
        numeric_columns = {}
        
        for name, info in self.datasets.items():
            data = info['data']
            date_cols = data.select_dtypes(include=['datetime64']).columns.tolist()
            
            # Also try to detect date-like columns
            for col in data.columns:
                if any(date_word in col.lower() for date_word in ['date', 'time', 'created', 'updated']):
                    try:
                        pd.to_datetime(data[col].dropna().head(100))
                        date_cols.append(col)
                    except:
                        pass
            
            if date_cols:
                date_columns[name] = date_cols
                numeric_columns[name] = data.select_dtypes(include=[np.number]).columns.tolist()
        
        answer = "Trend Analysis Across Datasets:\n\n"
        
        if date_columns:
            answer += f"📅 **Datasets with Time Data**:\n"
            for dataset, cols in date_columns.items():
                answer += f"• {dataset}: {', '.join(cols)}\n"
            
            answer += f"\n📈 **Available for Trend Analysis**:\n"
            for dataset, cols in numeric_columns.items():
                if dataset in date_columns:
                    answer += f"• {dataset}: {len(cols)} numeric columns\n"
        else:
            answer += "⚠️ No date/time columns detected. Trend analysis requires temporal data."
        
        return {
            'success': True,
            'answer': answer,
            'type': 'trend',
            'date_columns': date_columns,
            'numeric_columns': numeric_columns
        }
    
    def _handle_correlation_query(self, query: str) -> Dict[str, Any]:
        """Handle correlation analysis queries"""
        common_cols = self.find_common_columns()
        
        # Find numeric columns that appear in multiple datasets
        numeric_common = {}
        for col_pattern, appearances in common_cols.items():
            numeric_datasets = []
            for dataset_name, col_name in appearances:
                if dataset_name in self.datasets:
                    data = self.datasets[dataset_name]['data']
                    if col_name in data.columns and pd.api.types.is_numeric_dtype(data[col_name]):
                        numeric_datasets.append((dataset_name, col_name))
            
            if len(numeric_datasets) >= 2:
                numeric_common[col_pattern] = numeric_datasets
        
        answer = "Cross-Dataset Correlation Analysis:\n\n"
        
        if numeric_common:
            answer += f"🔢 **Numeric Columns for Correlation** ({len(numeric_common)}):\n"
            for pattern, datasets in numeric_common.items():
                dataset_names = [ds[0] for ds in datasets]
                answer += f"• '{pattern}' across: {', '.join(dataset_names)}\n"
            
            # Perform correlation analysis on the first common numeric column
            first_pattern = list(numeric_common.keys())[0]
            correlations = self.analyze_cross_dataset_correlations({first_pattern: numeric_common[first_pattern]})
            
            if first_pattern in correlations:
                corr_info = correlations[first_pattern]
                strongest = corr_info.get('strongest_correlation', {})
                if strongest:
                    answer += f"\n📊 **Strongest Correlation in '{first_pattern}'**:\n"
                    answer += f"• {strongest['columns'][0]} ↔ {strongest['columns'][1]}: {strongest['correlation']:.3f} ({strongest['strength']})\n"
        else:
            answer += "⚠️ No common numeric columns found for correlation analysis."
        
        return {
            'success': True,
            'answer': answer,
            'type': 'correlation',
            'numeric_common': numeric_common
        }
    
    def _handle_general_multi_query(self, query: str) -> Dict[str, Any]:
        """Handle general multi-dataset queries"""
        insights = self.generate_cross_dataset_insights()
        
        answer = f"Multi-Dataset Analysis Summary:\n\n"
        answer += f"📊 **{len(self.datasets)} datasets loaded**\n\n"
        
        answer += "💡 **Key Insights:**\n"
        for insight in insights[:5]:
            answer += f"• {insight}\n"
        
        return {
            'success': True,
            'answer': answer,
            'type': 'general',
            'insights': insights
        }