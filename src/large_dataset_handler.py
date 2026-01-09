import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Iterator, Callable
import logging
from pathlib import Path
import tempfile
import os

class LargeDatasetHandler:
    """Handle very large datasets with chunked processing and memory optimization"""
    
    def __init__(self, chunk_size: int = 10000, max_memory_mb: int = 500):
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
        self.temp_dir = tempfile.mkdtemp()
        self.logger = logging.getLogger(__name__)
        
    def load_large_csv(self, file_path: str, **kwargs) -> Iterator[pd.DataFrame]:
        """Load large CSV file in chunks"""
        try:
            chunk_iter = pd.read_csv(file_path, chunksize=self.chunk_size, **kwargs)
            for chunk in chunk_iter:
                yield self._optimize_chunk_memory(chunk)
        except Exception as e:
            self.logger.error(f"Error loading CSV: {str(e)}")
            raise
    
    def load_large_excel(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Load large Excel file with memory optimization"""
        try:
            # Excel files need to be loaded entirely, but we can optimize after
            df = pd.read_excel(file_path, **kwargs)
            return self._optimize_memory(df)
        except Exception as e:
            self.logger.error(f"Error loading Excel: {str(e)}")
            raise
    
    def _optimize_memory(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize memory usage of DataFrame"""
        original_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        for col in df.columns:
            col_type = df[col].dtype
            
            if col_type != 'object':
                # Optimize numeric columns
                if pd.api.types.is_integer_dtype(df[col]):
                    df[col] = pd.to_numeric(df[col], downcast='integer')
                elif pd.api.types.is_float_dtype(df[col]):
                    df[col] = pd.to_numeric(df[col], downcast='float')
            else:
                # Optimize object columns
                num_unique_values = df[col].nunique()
                num_total_values = len(df[col])
                
                # Convert to category if it saves memory
                if num_unique_values / num_total_values < 0.5:
                    df[col] = df[col].astype('category')
        
        optimized_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        self.logger.info(f"Memory optimization: {original_memory:.1f}MB -> {optimized_memory:.1f}MB")
        
        return df
    
    def _optimize_chunk_memory(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Optimize memory for a single chunk"""
        return self._optimize_memory(chunk)
    
    def process_in_chunks(self, df: pd.DataFrame, operation: Callable, **kwargs) -> Any:
        """Process large DataFrame in chunks"""
        if len(df) <= self.chunk_size:
            return operation(df, **kwargs)
        
        results = []
        for i in range(0, len(df), self.chunk_size):
            chunk = df.iloc[i:i + self.chunk_size]
            result = operation(chunk, **kwargs)
            results.append(result)
        
        # Combine results based on type
        if isinstance(results[0], pd.DataFrame):
            return pd.concat(results, ignore_index=True)
        elif isinstance(results[0], dict):
            # Combine dictionaries
            combined = {}
            for result in results:
                for key, value in result.items():
                    if key in combined:
                        if isinstance(value, (int, float)):
                            combined[key] += value
                        elif isinstance(value, list):
                            combined[key].extend(value)
                    else:
                        combined[key] = value
            return combined
        else:
            return results
    
    def get_sample_data(self, df: pd.DataFrame, sample_size: int = 1000) -> pd.DataFrame:
        """Get representative sample from large dataset"""
        if len(df) <= sample_size:
            return df
        
        # Stratified sampling if possible
        if len(df.columns) > 0:
            # Try to find a categorical column for stratification
            categorical_cols = []
            for col in df.columns:
                if df[col].dtype == 'object' or df[col].dtype.name == 'category':
                    unique_ratio = df[col].nunique() / len(df)
                    if 0.01 < unique_ratio < 0.3:  # Good for stratification
                        categorical_cols.append(col)
            
            if categorical_cols:
                # Stratified sample
                strat_col = categorical_cols[0]
                return df.groupby(strat_col, group_keys=False).apply(
                    lambda x: x.sample(min(len(x), max(1, sample_size // df[strat_col].nunique())))
                ).reset_index(drop=True)
        
        # Random sample
        return df.sample(n=sample_size, random_state=42).reset_index(drop=True)
    
    def analyze_large_dataset_structure(self, file_path: str) -> Dict[str, Any]:
        """Analyze structure of large dataset without loading it entirely"""
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.csv':
            return self._analyze_csv_structure(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return self._analyze_excel_structure(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _analyze_csv_structure(self, file_path: str) -> Dict[str, Any]:
        """Analyze CSV structure by reading first few chunks"""
        
        # Read first chunk to get column info
        first_chunk = pd.read_csv(file_path, nrows=1000)
        
        # Estimate total rows
        with open(file_path, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f) - 1  # Subtract header
        
        # Analyze columns
        column_info = {}
        for col in first_chunk.columns:
            col_data = first_chunk[col]
            column_info[col] = {
                'dtype': str(col_data.dtype),
                'null_count': col_data.isnull().sum(),
                'unique_count': col_data.nunique(),
                'sample_values': col_data.dropna().head(3).tolist()
            }
        
        # Estimate file size
        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
        
        return {
            'total_rows': total_lines,
            'total_columns': len(first_chunk.columns),
            'file_size_mb': file_size,
            'estimated_memory_mb': file_size * 2,  # Rough estimate
            'columns': column_info,
            'sample_data': first_chunk.head(5).to_dict('records')
        }
    
    def _analyze_excel_structure(self, file_path: str) -> Dict[str, Any]:
        """Analyze Excel structure"""
        
        # Read first few rows to get structure
        sample_df = pd.read_excel(file_path, nrows=100)
        
        # Get sheet info
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        # Estimate total rows (Excel is harder to estimate without loading)
        full_df = pd.read_excel(file_path)  # Have to load for accurate count
        total_rows = len(full_df)
        
        # Analyze columns
        column_info = {}
        for col in sample_df.columns:
            col_data = sample_df[col]
            column_info[col] = {
                'dtype': str(col_data.dtype),
                'null_count': col_data.isnull().sum(),
                'unique_count': col_data.nunique(),
                'sample_values': col_data.dropna().head(3).tolist()
            }
        
        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
        
        return {
            'total_rows': total_rows,
            'total_columns': len(sample_df.columns),
            'file_size_mb': file_size,
            'estimated_memory_mb': file_size * 3,  # Excel uses more memory
            'sheet_names': sheet_names,
            'columns': column_info,
            'sample_data': sample_df.head(5).to_dict('records')
        }
    
    def create_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create summary statistics for large dataset"""
        
        def _chunk_stats(chunk: pd.DataFrame) -> Dict[str, Any]:
            stats = {
                'row_count': len(chunk),
                'numeric_stats': {},
                'categorical_stats': {},
                'missing_counts': chunk.isnull().sum().to_dict()
            }
            
            # Numeric statistics
            numeric_cols = chunk.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                col_data = chunk[col].dropna()
                if len(col_data) > 0:
                    stats['numeric_stats'][col] = {
                        'count': len(col_data),
                        'sum': col_data.sum(),
                        'sum_squares': (col_data ** 2).sum(),
                        'min': col_data.min(),
                        'max': col_data.max()
                    }
            
            # Categorical statistics
            categorical_cols = chunk.select_dtypes(include=['object', 'category']).columns
            for col in categorical_cols:
                value_counts = chunk[col].value_counts()
                stats['categorical_stats'][col] = value_counts.to_dict()
            
            return stats
        
        # Process in chunks and combine
        combined_stats = self.process_in_chunks(df, _chunk_stats)
        
        # Calculate final statistics
        final_stats = {
            'total_rows': combined_stats.get('row_count', 0),
            'columns': {},
            'missing_values': combined_stats.get('missing_counts', {})
        }
        
        # Combine numeric statistics
        for col, stats_list in combined_stats.get('numeric_stats', {}).items():
            if isinstance(stats_list, list):
                total_count = sum(s['count'] for s in stats_list)
                total_sum = sum(s['sum'] for s in stats_list)
                total_sum_squares = sum(s['sum_squares'] for s in stats_list)
                
                mean = total_sum / total_count if total_count > 0 else 0
                variance = (total_sum_squares / total_count - mean ** 2) if total_count > 0 else 0
                std = np.sqrt(variance) if variance >= 0 else 0
                
                final_stats['columns'][col] = {
                    'type': 'numeric',
                    'count': total_count,
                    'mean': mean,
                    'std': std,
                    'min': min(s['min'] for s in stats_list),
                    'max': max(s['max'] for s in stats_list)
                }
            else:
                # Single chunk case
                stats = stats_list
                count = stats['count']
                mean = stats['sum'] / count if count > 0 else 0
                
                final_stats['columns'][col] = {
                    'type': 'numeric',
                    'count': count,
                    'mean': mean,
                    'min': stats['min'],
                    'max': stats['max']
                }
        
        # Combine categorical statistics
        for col, stats_list in combined_stats.get('categorical_stats', {}).items():
            if isinstance(stats_list, list):
                combined_counts = {}
                for stats in stats_list:
                    for value, count in stats.items():
                        combined_counts[value] = combined_counts.get(value, 0) + count
                
                final_stats['columns'][col] = {
                    'type': 'categorical',
                    'unique_values': len(combined_counts),
                    'top_values': dict(sorted(combined_counts.items(), 
                                            key=lambda x: x[1], reverse=True)[:10])
                }
            else:
                # Single chunk case
                final_stats['columns'][col] = {
                    'type': 'categorical',
                    'unique_values': len(stats_list),
                    'top_values': dict(sorted(stats_list.items(), 
                                            key=lambda x: x[1], reverse=True)[:10])
                }
        
        return final_stats
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.warning(f"Could not clean up temp directory: {str(e)}")

class SmartDataLoader:
    """Smart data loader that automatically handles different file sizes and formats"""
    
    def __init__(self):
        self.large_handler = LargeDatasetHandler()
        
    def load_data(self, uploaded_file, max_rows_in_memory: int = 100000) -> Dict[str, Any]:
        """Smart data loading with automatic optimization"""
        
        # Save uploaded file temporarily
        temp_path = os.path.join(self.large_handler.temp_dir, uploaded_file.name)
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        # Analyze file structure first
        try:
            structure = self.large_handler.analyze_large_dataset_structure(temp_path)
        except Exception as e:
            # Fallback to direct loading
            return self._load_direct(uploaded_file)
        
        # Decide loading strategy based on size
        if structure['total_rows'] > max_rows_in_memory:
            return self._load_large_file(temp_path, structure)
        else:
            return self._load_direct(uploaded_file)
    
    def _load_direct(self, uploaded_file) -> Dict[str, Any]:
        """Load file directly into memory"""
        
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        try:
            if file_extension == 'csv':
                df = pd.read_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file)
            elif file_extension == 'json':
                df = pd.read_json(uploaded_file)
            elif file_extension == 'parquet':
                df = pd.read_parquet(uploaded_file)
            else:
                raise ValueError(f"Unsupported format: {file_extension}")
            
            # Optimize memory
            df = self.large_handler._optimize_memory(df)
            
            return {
                'success': True,
                'data': df,
                'is_sample': False,
                'total_rows': len(df),
                'loading_method': 'direct'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'loading_method': 'direct'
            }
    
    def _load_large_file(self, file_path: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Load large file with sampling"""
        
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                # Load a representative sample
                total_rows = structure['total_rows']
                sample_size = min(50000, max(1000, total_rows // 100))
                
                # Read sample from different parts of the file
                skip_rows = max(1, total_rows // sample_size)
                df = pd.read_csv(file_path, skiprows=lambda i: i % skip_rows != 0 and i != 0)
                
            elif file_ext in ['.xlsx', '.xls']:
                # For Excel, load and sample
                df = pd.read_excel(file_path)
                df = self.large_handler.get_sample_data(df, 50000)
            
            else:
                raise ValueError(f"Large file loading not supported for {file_ext}")
            
            # Optimize memory
            df = self.large_handler._optimize_memory(df)
            
            return {
                'success': True,
                'data': df,
                'is_sample': True,
                'sample_size': len(df),
                'total_rows': structure['total_rows'],
                'loading_method': 'sampled',
                'structure': structure
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'loading_method': 'sampled'
            }