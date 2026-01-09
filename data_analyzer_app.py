import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import json
from typing import Dict, List, Any, Optional
import logging

# Import our advanced modules
from src.advanced_nlp_analyzer import AdvancedNLPAnalyzer
from src.large_dataset_handler import SmartDataLoader, LargeDatasetHandler

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Universal Data Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class UniversalDataAnalyzer:
    """Flexible data analyzer that works with any dataset structure"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.numeric_columns = self._identify_numeric_columns()
        self.categorical_columns = self._identify_categorical_columns()
        self.date_columns = self._identify_date_columns()
        self.text_columns = self._identify_text_columns()
    
    def _identify_numeric_columns(self) -> List[str]:
        """Identify numeric columns in the dataset"""
        numeric_cols = []
        for col in self.data.columns:
            if pd.api.types.is_numeric_dtype(self.data[col]):
                numeric_cols.append(col)
            else:
                # Try to convert to numeric
                try:
                    pd.to_numeric(self.data[col], errors='raise')
                    numeric_cols.append(col)
                except:
                    pass
        return numeric_cols
    
    def _identify_categorical_columns(self) -> List[str]:
        """Identify categorical columns"""
        categorical_cols = []
        for col in self.data.columns:
            if col not in self.numeric_columns:
                unique_ratio = self.data[col].nunique() / len(self.data)
                if unique_ratio < 0.5:  # Less than 50% unique values
                    categorical_cols.append(col)
        return categorical_cols
    
    def _identify_date_columns(self) -> List[str]:
        """Identify date/datetime columns"""
        date_cols = []
        for col in self.data.columns:
            if pd.api.types.is_datetime64_any_dtype(self.data[col]):
                date_cols.append(col)
            else:
                # Try to parse as date
                try:
                    pd.to_datetime(self.data[col].dropna().head(100), errors='raise')
                    date_cols.append(col)
                except:
                    pass
        return date_cols
    
    def _identify_text_columns(self) -> List[str]:
        """Identify text columns"""
        text_cols = []
        for col in self.data.columns:
            if col not in self.numeric_columns and col not in self.categorical_columns and col not in self.date_columns:
                text_cols.append(col)
        return text_cols
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get comprehensive data summary"""
        return {
            'total_rows': len(self.data),
            'total_columns': len(self.data.columns),
            'numeric_columns': len(self.numeric_columns),
            'categorical_columns': len(self.categorical_columns),
            'date_columns': len(self.date_columns),
            'text_columns': len(self.text_columns),
            'missing_values': self.data.isnull().sum().sum(),
            'memory_usage_mb': self.data.memory_usage(deep=True).sum() / 1024 / 1024,
            'column_types': {
                'numeric': self.numeric_columns,
                'categorical': self.categorical_columns,
                'date': self.date_columns,
                'text': self.text_columns
            }
        }
    
    def analyze_correlations(self) -> pd.DataFrame:
        """Analyze correlations between numeric columns"""
        if len(self.numeric_columns) < 2:
            return pd.DataFrame()
        
        numeric_data = self.data[self.numeric_columns]
        return numeric_data.corr()
    
    def get_column_stats(self, column: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific column"""
        col_data = self.data[column]
        stats = {
            'column_name': column,
            'data_type': str(col_data.dtype),
            'total_values': len(col_data),
            'non_null_values': col_data.count(),
            'null_values': col_data.isnull().sum(),
            'unique_values': col_data.nunique()
        }
        
        if column in self.numeric_columns:
            stats.update({
                'mean': col_data.mean(),
                'median': col_data.median(),
                'std': col_data.std(),
                'min': col_data.min(),
                'max': col_data.max(),
                'q25': col_data.quantile(0.25),
                'q75': col_data.quantile(0.75)
            })
        elif column in self.categorical_columns:
            value_counts = col_data.value_counts()
            stats.update({
                'most_common': value_counts.index[0] if len(value_counts) > 0 else None,
                'most_common_count': value_counts.iloc[0] if len(value_counts) > 0 else 0,
                'top_5_values': value_counts.head().to_dict()
            })
        
        return stats
    
    def create_visualization(self, viz_type: str, x_col: str, y_col: str = None, color_col: str = None) -> go.Figure:
        """Create various types of visualizations"""
        
        if viz_type == "histogram" and x_col in self.numeric_columns:
            fig = px.histogram(self.data, x=x_col, color=color_col, title=f"Distribution of {x_col}")
            
        elif viz_type == "scatter" and x_col in self.numeric_columns and y_col in self.numeric_columns:
            fig = px.scatter(self.data, x=x_col, y=y_col, color=color_col, 
                           title=f"{y_col} vs {x_col}")
            
        elif viz_type == "bar" and x_col in self.categorical_columns:
            value_counts = self.data[x_col].value_counts().head(20)
            fig = px.bar(x=value_counts.index, y=value_counts.values, 
                        title=f"Top Values in {x_col}")
            fig.update_xaxes(title=x_col)
            fig.update_yaxes(title="Count")
            
        elif viz_type == "box" and x_col in self.numeric_columns:
            fig = px.box(self.data, y=x_col, color=color_col, title=f"Box Plot of {x_col}")
            
        elif viz_type == "line" and x_col in self.date_columns and y_col in self.numeric_columns:
            # Group by date and aggregate
            date_data = self.data.groupby(x_col)[y_col].mean().reset_index()
            fig = px.line(date_data, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
            
        else:
            # Default to a simple count plot
            fig = go.Figure()
            fig.add_annotation(text="Visualization not available for selected columns", 
                             xref="paper", yref="paper", x=0.5, y=0.5)
            
        return fig
    
    def answer_question(self, question: str) -> str:
        """Attempt to answer natural language questions about the data"""
        question_lower = question.lower()
        
        # Simple pattern matching for common questions
        if "how many" in question_lower or "count" in question_lower:
            if "rows" in question_lower or "records" in question_lower:
                return f"The dataset contains {len(self.data):,} rows/records."
            elif "columns" in question_lower:
                return f"The dataset has {len(self.data.columns)} columns."
        
        elif "what are the columns" in question_lower or "column names" in question_lower:
            return f"The columns are: {', '.join(self.data.columns)}"
        
        elif "missing" in question_lower or "null" in question_lower:
            missing_info = self.data.isnull().sum()
            missing_cols = missing_info[missing_info > 0]
            if len(missing_cols) == 0:
                return "There are no missing values in the dataset."
            else:
                return f"Missing values found in: {dict(missing_cols)}"
        
        elif "correlation" in question_lower:
            if len(self.numeric_columns) >= 2:
                corr_matrix = self.analyze_correlations()
                # Find highest correlation (excluding diagonal)
                corr_values = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_values.append((
                            corr_matrix.columns[i], 
                            corr_matrix.columns[j], 
                            corr_matrix.iloc[i, j]
                        ))
                
                if corr_values:
                    highest_corr = max(corr_values, key=lambda x: abs(x[2]))
                    return f"Highest correlation is between {highest_corr[0]} and {highest_corr[1]}: {highest_corr[2]:.3f}"
            return "Not enough numeric columns to calculate correlations."
        
        elif "average" in question_lower or "mean" in question_lower:
            # Look for column names in the question
            for col in self.numeric_columns:
                if col.lower() in question_lower:
                    avg_val = self.data[col].mean()
                    return f"The average {col} is {avg_val:.2f}"
            return f"Available numeric columns for averages: {', '.join(self.numeric_columns)}"
        
        elif "maximum" in question_lower or "max" in question_lower:
            for col in self.numeric_columns:
                if col.lower() in question_lower:
                    max_val = self.data[col].max()
                    return f"The maximum {col} is {max_val}"
            return f"Available numeric columns: {', '.join(self.numeric_columns)}"
        
        elif "minimum" in question_lower or "min" in question_lower:
            for col in self.numeric_columns:
                if col.lower() in question_lower:
                    min_val = self.data[col].min()
                    return f"The minimum {col} is {min_val}"
            return f"Available numeric columns: {', '.join(self.numeric_columns)}"
        
        else:
            return "I can help you with questions about: row/column counts, missing values, correlations, averages, min/max values, and column information. Try asking something like 'How many rows are there?' or 'What are the correlations?'"

def load_data_from_file(uploaded_file) -> Dict[str, Any]:
    """Load data from various file formats with smart handling for large files"""
    
    if uploaded_file is None:
        return {'success': False, 'error': 'No file provided'}
    
    # Use smart data loader
    smart_loader = SmartDataLoader()
    return smart_loader.load_data(uploaded_file)

# Main App
def main():
    st.title("📊 Universal Data Analyzer")
    st.markdown("*Upload any dataset and start asking questions - handles large files and flexible column structures*")
    
    # Initialize session state
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'nlp_analyzer' not in st.session_state:
        st.session_state.nlp_analyzer = None
    
    # Sidebar for file upload
    with st.sidebar:
        st.header("📁 Upload Data")
        
        uploaded_file = st.file_uploader(
            "Choose your data file",
            type=['csv', 'xlsx', 'xls', 'json', 'parquet'],
            help="Supports CSV, Excel, JSON, and Parquet files"
        )
        
        if uploaded_file is not None:
            with st.spinner("Loading data..."):
                result = load_data_from_file(uploaded_file)
                
                if result['success']:
                    df = result['data']
                    st.session_state.data = df
                    st.session_state.analyzer = UniversalDataAnalyzer(df)
                    st.session_state.nlp_analyzer = AdvancedNLPAnalyzer(df)
                    
                    # Show loading info
                    if result.get('is_sample', False):
                        st.warning(f"⚠️ Large file detected! Loaded {result['sample_size']:,} sample rows from {result['total_rows']:,} total rows")
                        st.info(f"💡 Analysis is based on representative sample. Results are still meaningful!")
                    else:
                        st.success(f"✅ Loaded {len(df):,} rows × {len(df.columns)} columns")
                    
                    # Show file info
                    file_size = uploaded_file.size / 1024 / 1024  # MB
                    st.info(f"📄 File: {uploaded_file.name} ({file_size:.1f} MB) - Method: {result['loading_method']}")
                else:
                    st.error(f"❌ Error loading file: {result['error']}")
        
        # Sample data option
        st.divider()
        if st.button("🧪 Load Sample Sales Data"):
            # Create sample data
            np.random.seed(42)
            sample_data = {
                'sales_rep': [f'Rep_{i:03d}' for i in np.random.randint(1, 50, 1000)],
                'region': np.random.choice(['North', 'South', 'East', 'West'], 1000),
                'product': np.random.choice(['Product_A', 'Product_B', 'Product_C', 'Product_D'], 1000),
                'deal_value': np.random.lognormal(8, 1, 1000),
                'deal_stage': np.random.choice(['Prospect', 'Qualified', 'Proposal', 'Negotiation', 'Closed'], 1000),
                'close_date': pd.date_range('2023-01-01', periods=1000, freq='D'),
                'customer_size': np.random.choice(['Small', 'Medium', 'Large', 'Enterprise'], 1000),
                'win_probability': np.random.beta(2, 2, 1000),
                'days_in_pipeline': np.random.gamma(2, 30, 1000)
            }
            
            df = pd.DataFrame(sample_data)
            st.session_state.data = df
            st.session_state.analyzer = UniversalDataAnalyzer(df)
            st.session_state.nlp_analyzer = AdvancedNLPAnalyzer(df)
            st.success("✅ Sample data loaded!")
    
    # Main content area
    if st.session_state.data is not None:
        data = st.session_state.data
        analyzer = st.session_state.analyzer
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Ask Questions", "📊 Explore Data", "📈 Visualizations", "🔍 Column Analysis"])
        
        with tab1:
            st.header("💬 Ask Questions About Your Data")
            
            # Show smart suggestions
            if st.session_state.nlp_analyzer:
                suggestions = st.session_state.nlp_analyzer.get_smart_suggestions()
                
                st.markdown("**💡 Smart Suggestions (click to use):**")
                cols = st.columns(2)
                for i, suggestion in enumerate(suggestions[:6]):
                    with cols[i % 2]:
                        if st.button(f"💭 {suggestion}", key=f"suggestion_{i}"):
                            st.session_state.current_question = suggestion
            
            # Quick question buttons
            st.markdown("**Quick Questions:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📊 Data Overview"):
                    st.session_state.current_question = "How many rows and columns are there?"
            with col2:
                if st.button("🔍 Missing Values"):
                    st.session_state.current_question = "Are there any missing values?"
            with col3:
                if st.button("📈 Correlations"):
                    st.session_state.current_question = "What are the correlations?"
            with col4:
                if st.button("📋 Column Names"):
                    st.session_state.current_question = "What are the column names?"
            
            # Question input
            question = st.text_input(
                "Ask a question about your data:",
                value=st.session_state.get('current_question', ''),
                placeholder="e.g., What's the average sales value? Show me the top 10 customers by revenue"
            )
            
            if st.button("🔍 Get Answer", type="primary") and question:
                with st.spinner("Analyzing..."):
                    # Use advanced NLP analyzer if available
                    if st.session_state.nlp_analyzer:
                        result = st.session_state.nlp_analyzer.process_natural_language_query(question)
                        
                        if result['success']:
                            answer = result['answer']
                            
                            # Add to chat history
                            st.session_state.chat_history.append({
                                'question': question,
                                'answer': answer,
                                'result_type': result.get('type', 'general'),
                                'timestamp': datetime.now()
                            })
                            
                            # Display answer with better formatting
                            st.success(f"**Answer:** {answer}")
                            
                            # Show additional info if available
                            if 'suggestions' in result:
                                with st.expander("💡 Additional Help"):
                                    for suggestion in result['suggestions']:
                                        st.info(suggestion)
                        else:
                            st.error(f"❌ {result['error']}")
                            if 'suggestion' in result:
                                st.info(f"💡 {result['suggestion']}")
                    else:
                        # Fallback to basic analyzer
                        answer = analyzer.answer_question(question)
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            'question': question,
                            'answer': answer,
                            'result_type': 'basic',
                            'timestamp': datetime.now()
                        })
                        
                        st.success(f"**Answer:** {answer}")
            
            # Chat history with better formatting
            if st.session_state.chat_history:
                st.divider()
                st.subheader("💭 Recent Questions")
                
                for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
                    with st.expander(f"Q: {chat['question'][:50]}..." if len(chat['question']) > 50 else f"Q: {chat['question']}"):
                        st.markdown(f"**Question:** {chat['question']}")
                        st.markdown(f"**Answer:** {chat['answer']}")
                        st.caption(f"Type: {chat.get('result_type', 'basic')} | Asked at {chat['timestamp'].strftime('%H:%M:%S')}")
                        
                        # Add re-ask button
                        if st.button(f"🔄 Ask Again", key=f"reask_{i}"):
                            st.session_state.current_question = chat['question']
                            st.rerun()
        
        with tab2:
            st.header("📊 Data Overview")
            
            # Data summary
            summary = analyzer.get_data_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Rows", f"{summary['total_rows']:,}")
            with col2:
                st.metric("Total Columns", summary['total_columns'])
            with col3:
                st.metric("Missing Values", f"{summary['missing_values']:,}")
            with col4:
                st.metric("Memory Usage", f"{summary['memory_usage_mb']:.1f} MB")
            
            # Column type breakdown
            st.subheader("📋 Column Types")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Numeric", summary['numeric_columns'])
                if summary['column_types']['numeric']:
                    st.caption(", ".join(summary['column_types']['numeric'][:3]) + 
                              (f" (+{len(summary['column_types']['numeric'])-3} more)" if len(summary['column_types']['numeric']) > 3 else ""))
            
            with col2:
                st.metric("Categorical", summary['categorical_columns'])
                if summary['column_types']['categorical']:
                    st.caption(", ".join(summary['column_types']['categorical'][:3]) + 
                              (f" (+{len(summary['column_types']['categorical'])-3} more)" if len(summary['column_types']['categorical']) > 3 else ""))
            
            with col3:
                st.metric("Date/Time", summary['date_columns'])
                if summary['column_types']['date']:
                    st.caption(", ".join(summary['column_types']['date'][:3]))
            
            with col4:
                st.metric("Text", summary['text_columns'])
                if summary['column_types']['text']:
                    st.caption(", ".join(summary['column_types']['text'][:3]) + 
                              (f" (+{len(summary['column_types']['text'])-3} more)" if len(summary['column_types']['text']) > 3 else ""))
            
            # Data preview
            st.subheader("🔍 Data Preview")
            st.dataframe(data.head(100), use_container_width=True)
            
            # Missing values heatmap
            if summary['missing_values'] > 0:
                st.subheader("❌ Missing Values by Column")
                missing_data = data.isnull().sum()
                missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
                
                fig = px.bar(x=missing_data.index, y=missing_data.values, 
                           title="Missing Values by Column")
                fig.update_xaxes(title="Columns")
                fig.update_yaxes(title="Missing Count")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.header("📈 Create Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                viz_type = st.selectbox(
                    "Visualization Type",
                    ["histogram", "scatter", "bar", "box", "line"],
                    help="Choose the type of chart to create"
                )
                
                x_column = st.selectbox(
                    "X-axis Column",
                    data.columns,
                    help="Select column for X-axis"
                )
            
            with col2:
                y_column = st.selectbox(
                    "Y-axis Column (optional)",
                    [None] + list(data.columns),
                    help="Select column for Y-axis (required for scatter/line plots)"
                )
                
                color_column = st.selectbox(
                    "Color Column (optional)",
                    [None] + list(analyzer.categorical_columns),
                    help="Select categorical column to color by"
                )
            
            if st.button("📊 Create Visualization"):
                try:
                    fig = analyzer.create_visualization(viz_type, x_column, y_column, color_column)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating visualization: {str(e)}")
            
            # Correlation heatmap for numeric data
            if len(analyzer.numeric_columns) > 1:
                st.subheader("🔥 Correlation Heatmap")
                corr_matrix = analyzer.analyze_correlations()
                
                fig = px.imshow(corr_matrix, 
                              title="Correlation Matrix",
                              color_continuous_scale="RdBu",
                              aspect="auto")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.header("🔍 Detailed Column Analysis")
            
            selected_column = st.selectbox("Select Column to Analyze", data.columns)
            
            if selected_column:
                stats = analyzer.get_column_stats(selected_column)
                
                # Basic info
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Data Type", stats['data_type'])
                with col2:
                    st.metric("Non-null Values", f"{stats['non_null_values']:,}")
                with col3:
                    st.metric("Null Values", f"{stats['null_values']:,}")
                with col4:
                    st.metric("Unique Values", f"{stats['unique_values']:,}")
                
                # Detailed stats based on column type
                if selected_column in analyzer.numeric_columns:
                    st.subheader("📊 Numeric Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Mean", f"{stats['mean']:.2f}")
                        st.metric("Min", f"{stats['min']:.2f}")
                    with col2:
                        st.metric("Median", f"{stats['median']:.2f}")
                        st.metric("Q25", f"{stats['q25']:.2f}")
                    with col3:
                        st.metric("Std Dev", f"{stats['std']:.2f}")
                        st.metric("Q75", f"{stats['q75']:.2f}")
                    with col4:
                        st.metric("Max", f"{stats['max']:.2f}")
                    
                    # Distribution plot
                    fig = px.histogram(data, x=selected_column, title=f"Distribution of {selected_column}")
                    st.plotly_chart(fig, use_container_width=True)
                
                elif selected_column in analyzer.categorical_columns:
                    st.subheader("📋 Categorical Statistics")
                    
                    if 'most_common' in stats:
                        st.info(f"Most common value: **{stats['most_common']}** (appears {stats['most_common_count']:,} times)")
                    
                    if 'top_5_values' in stats:
                        st.subheader("Top 5 Values")
                        top_values_df = pd.DataFrame(list(stats['top_5_values'].items()), 
                                                   columns=['Value', 'Count'])
                        st.dataframe(top_values_df, use_container_width=True)
                        
                        # Bar chart
                        fig = px.bar(top_values_df, x='Value', y='Count', 
                                   title=f"Top Values in {selected_column}")
                        st.plotly_chart(fig, use_container_width=True)
                
                # Value counts table
                st.subheader("📋 Value Distribution")
                value_counts = data[selected_column].value_counts().head(20)
                st.dataframe(value_counts, use_container_width=True)
    
    else:
        # Welcome screen
        st.markdown("""
        ## 🚀 Welcome to Universal Data Analyzer!
        
        This tool helps you analyze **any dataset** regardless of structure or column names. Perfect for:
        
        - **Large datasets** (handles millions of rows efficiently)
        - **Flexible column structures** (works with any column names)
        - **Multiple file formats** (CSV, Excel, JSON, Parquet)
        - **Natural language questions** (ask questions in plain English)
        
        ### 📁 Get Started:
        1. **Upload your data** using the sidebar
        2. **Ask questions** in natural language
        3. **Explore and visualize** your data
        4. **Analyze individual columns** in detail
        
        ### 💡 Example Questions You Can Ask:
        - "How many rows are there?"
        - "What are the correlations?"
        - "Are there missing values?"
        - "What's the average sales amount?"
        - "Show me the column names"
        
        ### 📊 Supported File Types:
        - **CSV** files (any delimiter, encoding)
        - **Excel** files (.xlsx, .xls)
        - **JSON** files
        - **Parquet** files (for large datasets)
        
        **👈 Upload a file or try sample data to begin!**
        """)

if __name__ == "__main__":
    main()