import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import re
import logging
from datetime import datetime
import json

class AdvancedNLPAnalyzer:
    """Advanced NLP analyzer for flexible data questioning"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.column_info = self._analyze_columns()
        self.query_cache = {}
        
    def _analyze_columns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze each column to understand its characteristics"""
        column_info = {}
        
        for col in self.data.columns:
            col_data = self.data[col]
            
            info = {
                'name': col,
                'dtype': str(col_data.dtype),
                'null_count': col_data.isnull().sum(),
                'unique_count': col_data.nunique(),
                'sample_values': col_data.dropna().head(5).tolist(),
                'is_numeric': pd.api.types.is_numeric_dtype(col_data),
                'is_datetime': pd.api.types.is_datetime64_any_dtype(col_data),
                'is_categorical': col_data.nunique() / len(col_data) < 0.5 if len(col_data) > 0 else False
            }
            
            # Try to infer semantic meaning from column name
            col_lower = col.lower()
            info['semantic_type'] = self._infer_semantic_type(col_lower, col_data)
            
            # Add statistical info for numeric columns
            if info['is_numeric']:
                info.update({
                    'mean': col_data.mean(),
                    'median': col_data.median(),
                    'std': col_data.std(),
                    'min': col_data.min(),
                    'max': col_data.max()
                })
            
            column_info[col] = info
            
        return column_info
    
    def _infer_semantic_type(self, col_name: str, col_data: pd.Series) -> str:
        """Infer semantic meaning of column based on name and data"""
        
        # Common patterns
        patterns = {
            'id': r'.*id$|.*_id|^id_.*|identifier|key',
            'name': r'name|title|label|description',
            'date': r'date|time|created|updated|modified|timestamp',
            'amount': r'amount|value|price|cost|revenue|sales|fee|charge',
            'count': r'count|quantity|qty|number|num|total',
            'rate': r'rate|ratio|percent|percentage|score',
            'status': r'status|state|stage|phase|type|category',
            'location': r'location|address|city|state|country|region|zip|postal',
            'contact': r'email|phone|contact|mobile|telephone'
        }
        
        for semantic_type, pattern in patterns.items():
            if re.search(pattern, col_name):
                return semantic_type
        
        # Fallback based on data characteristics
        if pd.api.types.is_numeric_dtype(col_data):
            return 'numeric'
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            return 'date'
        elif col_data.nunique() / len(col_data) < 0.1:
            return 'category'
        else:
            return 'text'
    
    def process_natural_language_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query and return structured response"""
        
        # Cache check
        if query in self.query_cache:
            return self.query_cache[query]
        
        query_lower = query.lower().strip()
        
        # Parse the query
        intent = self._classify_intent(query_lower)
        entities = self._extract_entities(query_lower)
        
        # Execute the query
        result = self._execute_query(intent, entities, query_lower)
        
        # Cache the result
        self.query_cache[query] = result
        
        return result
    
    def _classify_intent(self, query: str) -> str:
        """Classify the intent of the query"""
        
        intents = {
            'count': r'how many|count|number of|total.*rows|total.*records',
            'summary': r'summary|overview|describe|statistics|stats',
            'missing': r'missing|null|empty|blank|na|nan',
            'unique': r'unique|distinct|different',
            'average': r'average|mean|avg',
            'maximum': r'maximum|max|highest|largest|biggest',
            'minimum': r'minimum|min|lowest|smallest',
            'correlation': r'correlat|relationship|related|connect',
            'distribution': r'distribution|spread|range|histogram',
            'comparison': r'compare|versus|vs|difference|between',
            'filter': r'where|filter|show.*only|records.*with',
            'groupby': r'group.*by|by.*group|breakdown|segment',
            'trend': r'trend|over time|timeline|change.*over',
            'top': r'top|best|highest.*value|largest.*value',
            'bottom': r'bottom|worst|lowest.*value|smallest.*value'
        }
        
        for intent, pattern in intents.items():
            if re.search(pattern, query):
                return intent
        
        return 'general'
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities (column names, values, etc.) from query"""
        
        entities = {
            'columns': [],
            'values': [],
            'operators': [],
            'aggregations': []
        }
        
        # Find column names mentioned in query
        for col_name in self.data.columns:
            col_variations = [
                col_name.lower(),
                col_name.lower().replace('_', ' '),
                col_name.lower().replace('-', ' ')
            ]
            
            for variation in col_variations:
                if variation in query:
                    entities['columns'].append(col_name)
                    break
        
        # Find aggregation functions
        aggregations = ['sum', 'average', 'mean', 'count', 'max', 'min', 'median']
        for agg in aggregations:
            if agg in query:
                entities['aggregations'].append(agg)
        
        # Find comparison operators
        operators = ['greater than', 'less than', 'equal to', 'not equal', '>', '<', '=', '!=']
        for op in operators:
            if op in query:
                entities['operators'].append(op)
        
        return entities
    
    def _execute_query(self, intent: str, entities: Dict[str, List[str]], query: str) -> Dict[str, Any]:
        """Execute the parsed query and return results"""
        
        try:
            if intent == 'count':
                return self._handle_count_query(entities, query)
            elif intent == 'summary':
                return self._handle_summary_query(entities)
            elif intent == 'missing':
                return self._handle_missing_query(entities)
            elif intent == 'unique':
                return self._handle_unique_query(entities)
            elif intent in ['average', 'maximum', 'minimum']:
                return self._handle_aggregation_query(intent, entities)
            elif intent == 'correlation':
                return self._handle_correlation_query(entities)
            elif intent == 'distribution':
                return self._handle_distribution_query(entities)
            elif intent == 'comparison':
                return self._handle_comparison_query(entities, query)
            elif intent in ['top', 'bottom']:
                return self._handle_ranking_query(intent, entities, query)
            else:
                return self._handle_general_query(query)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggestion': 'Try rephrasing your question or ask for help with available commands.'
            }
    
    def _handle_count_query(self, entities: Dict[str, List[str]], query: str) -> Dict[str, Any]:
        """Handle counting queries"""
        
        if 'rows' in query or 'records' in query:
            return {
                'success': True,
                'answer': f"The dataset contains {len(self.data):,} rows.",
                'value': len(self.data),
                'type': 'count'
            }
        elif 'columns' in query:
            return {
                'success': True,
                'answer': f"The dataset has {len(self.data.columns)} columns.",
                'value': len(self.data.columns),
                'type': 'count'
            }
        elif entities['columns']:
            col = entities['columns'][0]
            count = self.data[col].count()
            return {
                'success': True,
                'answer': f"Column '{col}' has {count:,} non-null values.",
                'value': count,
                'type': 'count',
                'column': col
            }
        else:
            return {
                'success': True,
                'answer': f"Dataset overview: {len(self.data):,} rows × {len(self.data.columns)} columns",
                'rows': len(self.data),
                'columns': len(self.data.columns),
                'type': 'count'
            }
    
    def _handle_summary_query(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle summary/overview queries"""
        
        if entities['columns']:
            col = entities['columns'][0]
            col_info = self.column_info[col]
            
            summary = f"Column '{col}' summary:\n"
            summary += f"- Data type: {col_info['dtype']}\n"
            summary += f"- Non-null values: {len(self.data) - col_info['null_count']:,}\n"
            summary += f"- Unique values: {col_info['unique_count']:,}\n"
            
            if col_info['is_numeric']:
                summary += f"- Mean: {col_info['mean']:.2f}\n"
                summary += f"- Range: {col_info['min']:.2f} to {col_info['max']:.2f}"
            
            return {
                'success': True,
                'answer': summary,
                'column_info': col_info,
                'type': 'summary'
            }
        else:
            # Dataset summary
            numeric_cols = [col for col, info in self.column_info.items() if info['is_numeric']]
            categorical_cols = [col for col, info in self.column_info.items() if info['is_categorical']]
            
            summary = f"Dataset Summary:\n"
            summary += f"- Total rows: {len(self.data):,}\n"
            summary += f"- Total columns: {len(self.data.columns)}\n"
            summary += f"- Numeric columns: {len(numeric_cols)}\n"
            summary += f"- Categorical columns: {len(categorical_cols)}\n"
            summary += f"- Memory usage: {self.data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB"
            
            return {
                'success': True,
                'answer': summary,
                'stats': {
                    'rows': len(self.data),
                    'columns': len(self.data.columns),
                    'numeric_columns': len(numeric_cols),
                    'categorical_columns': len(categorical_cols)
                },
                'type': 'summary'
            }
    
    def _handle_missing_query(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle missing value queries"""
        
        if entities['columns']:
            col = entities['columns'][0]
            missing_count = self.data[col].isnull().sum()
            total_count = len(self.data)
            missing_pct = (missing_count / total_count) * 100
            
            return {
                'success': True,
                'answer': f"Column '{col}' has {missing_count:,} missing values ({missing_pct:.1f}%)",
                'missing_count': missing_count,
                'missing_percentage': missing_pct,
                'column': col,
                'type': 'missing'
            }
        else:
            # Overall missing values
            missing_summary = self.data.isnull().sum()
            missing_cols = missing_summary[missing_summary > 0]
            
            if len(missing_cols) == 0:
                return {
                    'success': True,
                    'answer': "Great news! There are no missing values in the dataset.",
                    'missing_count': 0,
                    'type': 'missing'
                }
            else:
                answer = f"Found missing values in {len(missing_cols)} columns:\n"
                for col, count in missing_cols.head(5).items():
                    pct = (count / len(self.data)) * 100
                    answer += f"- {col}: {count:,} ({pct:.1f}%)\n"
                
                if len(missing_cols) > 5:
                    answer += f"... and {len(missing_cols) - 5} more columns"
                
                return {
                    'success': True,
                    'answer': answer,
                    'missing_summary': missing_cols.to_dict(),
                    'type': 'missing'
                }
    
    def _handle_aggregation_query(self, intent: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle aggregation queries (average, max, min)"""
        
        if not entities['columns']:
            numeric_cols = [col for col, info in self.column_info.items() if info['is_numeric']]
            return {
                'success': False,
                'error': f"Please specify a column name. Available numeric columns: {', '.join(numeric_cols)}",
                'type': 'error'
            }
        
        col = entities['columns'][0]
        
        if not self.column_info[col]['is_numeric']:
            return {
                'success': False,
                'error': f"Column '{col}' is not numeric. Cannot calculate {intent}.",
                'type': 'error'
            }
        
        col_data = self.data[col].dropna()
        
        if intent == 'average':
            value = col_data.mean()
            answer = f"The average {col} is {value:.2f}"
        elif intent == 'maximum':
            value = col_data.max()
            answer = f"The maximum {col} is {value:.2f}"
        elif intent == 'minimum':
            value = col_data.min()
            answer = f"The minimum {col} is {value:.2f}"
        
        return {
            'success': True,
            'answer': answer,
            'value': value,
            'column': col,
            'type': intent
        }
    
    def _handle_correlation_query(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Handle correlation queries"""
        
        numeric_cols = [col for col, info in self.column_info.items() if info['is_numeric']]
        
        if len(numeric_cols) < 2:
            return {
                'success': False,
                'error': "Need at least 2 numeric columns to calculate correlations.",
                'type': 'error'
            }
        
        if len(entities['columns']) >= 2:
            # Specific correlation between two columns
            col1, col2 = entities['columns'][:2]
            if col1 in numeric_cols and col2 in numeric_cols:
                corr_value = self.data[col1].corr(self.data[col2])
                return {
                    'success': True,
                    'answer': f"Correlation between {col1} and {col2}: {corr_value:.3f}",
                    'correlation': corr_value,
                    'columns': [col1, col2],
                    'type': 'correlation'
                }
        
        # General correlation analysis
        corr_matrix = self.data[numeric_cols].corr()
        
        # Find strongest correlations
        correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if not pd.isna(corr_val):
                    correlations.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_val
                    ))
        
        # Sort by absolute correlation value
        correlations.sort(key=lambda x: abs(x[2]), reverse=True)
        
        if correlations:
            strongest = correlations[0]
            answer = f"Strongest correlation: {strongest[0]} and {strongest[1]} ({strongest[2]:.3f})"
            
            if len(correlations) > 1:
                answer += f"\nOther strong correlations:\n"
                for col1, col2, corr_val in correlations[1:4]:  # Show top 3 more
                    answer += f"- {col1} & {col2}: {corr_val:.3f}\n"
        else:
            answer = "No correlations could be calculated."
        
        return {
            'success': True,
            'answer': answer,
            'correlations': correlations[:5],
            'type': 'correlation'
        }
    
    def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries that don't fit specific patterns"""
        
        # Try to provide helpful suggestions
        suggestions = [
            "Try asking about: row counts, column summaries, missing values, or correlations",
            "Example questions: 'How many rows?', 'What's the average sales?', 'Are there missing values?'",
            f"Available columns: {', '.join(list(self.data.columns)[:5])}{'...' if len(self.data.columns) > 5 else ''}"
        ]
        
        return {
            'success': True,
            'answer': "I'm not sure how to answer that specific question. Here are some things I can help with:",
            'suggestions': suggestions,
            'type': 'help'
        }
    
    def _handle_ranking_query(self, intent: str, entities: Dict[str, List[str]], query: str) -> Dict[str, Any]:
        """Handle top/bottom ranking queries"""
        
        if not entities['columns']:
            return {
                'success': False,
                'error': "Please specify which column to rank by.",
                'type': 'error'
            }
        
        col = entities['columns'][0]
        
        # Extract number if mentioned
        numbers = re.findall(r'\d+', query)
        n = int(numbers[0]) if numbers else 5
        n = min(n, 20)  # Limit to 20 results
        
        if intent == 'top':
            if self.column_info[col]['is_numeric']:
                top_values = self.data.nlargest(n, col)[col]
                answer = f"Top {n} values in {col}:\n"
                for i, val in enumerate(top_values, 1):
                    answer += f"{i}. {val}\n"
            else:
                top_values = self.data[col].value_counts().head(n)
                answer = f"Top {n} most frequent values in {col}:\n"
                for val, count in top_values.items():
                    answer += f"- {val}: {count} times\n"
        else:  # bottom
            if self.column_info[col]['is_numeric']:
                bottom_values = self.data.nsmallest(n, col)[col]
                answer = f"Bottom {n} values in {col}:\n"
                for i, val in enumerate(bottom_values, 1):
                    answer += f"{i}. {val}\n"
            else:
                bottom_values = self.data[col].value_counts().tail(n)
                answer = f"Bottom {n} least frequent values in {col}:\n"
                for val, count in bottom_values.items():
                    answer += f"- {val}: {count} times\n"
        
        return {
            'success': True,
            'answer': answer,
            'column': col,
            'n': n,
            'type': f'{intent}_values'
        }
    
    def get_smart_suggestions(self, partial_query: str = "") -> List[str]:
        """Get smart suggestions based on data structure and partial query"""
        
        suggestions = []
        
        # Basic questions
        suggestions.extend([
            "How many rows are there?",
            "What are the column names?",
            "Are there any missing values?",
            "Show me a summary of the data"
        ])
        
        # Column-specific suggestions
        numeric_cols = [col for col, info in self.column_info.items() if info['is_numeric']]
        if numeric_cols:
            col = numeric_cols[0]
            suggestions.extend([
                f"What's the average {col}?",
                f"What's the maximum {col}?",
                f"Show me the top 10 {col} values"
            ])
        
        # Correlation suggestions
        if len(numeric_cols) >= 2:
            suggestions.append("What are the correlations between numeric columns?")
        
        # Categorical analysis
        categorical_cols = [col for col, info in self.column_info.items() if info['is_categorical']]
        if categorical_cols:
            col = categorical_cols[0]
            suggestions.append(f"What are the most common values in {col}?")
        
        return suggestions[:8]  # Return top 8 suggestions