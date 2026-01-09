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
from src.multi_dataset_analyzer import MultiDatasetAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Multi-Dataset Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
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

def load_data_from_file(uploaded_file) -> Dict[str, Any]:
    """Load data from various file formats with smart handling for large files"""
    
    if uploaded_file is None:
        return {'success': False, 'error': 'No file provided'}
    
    # Use smart data loader
    smart_loader = SmartDataLoader()
    return smart_loader.load_data(uploaded_file)

def main():
    st.title("📊 Multi-Dataset Analyzer")
    st.markdown("*Upload multiple datasets and analyze them together - find correlations, trends, and insights across your data*")
    
    # Initialize session state
    if 'multi_analyzer' not in st.session_state:
        st.session_state.multi_analyzer = MultiDatasetAnalyzer()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_dataset' not in st.session_state:
        st.session_state.current_dataset = None
    
    # Sidebar for dataset management
    with st.sidebar:
        st.header("📁 Dataset Management")
        
        # File upload section
        st.subheader("Upload New Dataset")
        uploaded_file = st.file_uploader(
            "Choose your data file",
            type=['csv', 'xlsx', 'xls', 'json', 'parquet'],
            help="Supports CSV, Excel, JSON, and Parquet files",
            key="file_uploader"
        )
        
        # Dataset name input
        if uploaded_file:
            default_name = uploaded_file.name.split('.')[0]
            dataset_name = st.text_input(
                "Dataset Name",
                value=default_name,
                help="Give your dataset a memorable name"
            )
            
            if st.button("📤 Load Dataset", type="primary"):
                if dataset_name:
                    with st.spinner(f"Loading {dataset_name}..."):
                        result = load_data_from_file(uploaded_file)
                        
                        if result['success']:
                            df = result['data']
                            
                            # Add metadata
                            metadata = {
                                'filename': uploaded_file.name,
                                'file_size_mb': uploaded_file.size / 1024 / 1024,
                                'loading_method': result['loading_method'],
                                'is_sample': result.get('is_sample', False),
                                'sample_size': result.get('sample_size', len(df)),
                                'total_rows': result.get('total_rows', len(df))
                            }
                            
                            # Add to multi-analyzer
                            st.session_state.multi_analyzer.add_dataset(dataset_name, df, metadata)
                            st.session_state.current_dataset = dataset_name
                            
                            # Show success message
                            if result.get('is_sample', False):
                                st.success(f"✅ Added '{dataset_name}' (sample: {result['sample_size']:,} of {result['total_rows']:,} rows)")
                            else:
                                st.success(f"✅ Added '{dataset_name}' ({len(df):,} rows × {len(df.columns)} columns)")
                        else:
                            st.error(f"❌ Error loading file: {result['error']}")
                else:
                    st.error("Please provide a dataset name")
        
        # Current datasets section
        st.divider()
        st.subheader("📊 Loaded Datasets")
        
        datasets = st.session_state.multi_analyzer.list_datasets()
        
        if datasets:
            for i, dataset_info in enumerate(datasets):
                with st.expander(f"📋 {dataset_info['name']}", expanded=i==0):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rows", f"{dataset_info['rows']:,}")
                        st.metric("Columns", dataset_info['columns'])
                    with col2:
                        st.metric("Size", f"{dataset_info['size_mb']:.1f} MB")
                        st.metric("Added", dataset_info['added_at'].strftime("%H:%M"))
                    
                    # Dataset actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🔍 Analyze", key=f"analyze_{i}"):
                            st.session_state.current_dataset = dataset_info['name']
                    with col2:
                        if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                            st.session_state.multi_analyzer.remove_dataset(dataset_info['name'])
                            if st.session_state.current_dataset == dataset_info['name']:
                                st.session_state.current_dataset = None
                            st.rerun()
        else:
            st.info("No datasets loaded yet. Upload files above to get started!")
        
        # Sample data options
        st.divider()
        st.subheader("🧪 Sample Data")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📈 Sales Data"):
                # Create sample sales data
                np.random.seed(42)
                sales_data = {
                    'sales_rep': [f'Rep_{i:03d}' for i in np.random.randint(1, 50, 1000)],
                    'region': np.random.choice(['North', 'South', 'East', 'West'], 1000),
                    'product': np.random.choice(['Product_A', 'Product_B', 'Product_C'], 1000),
                    'deal_value': np.random.lognormal(8, 1, 1000),
                    'close_date': pd.date_range('2023-01-01', periods=1000, freq='D'),
                    'customer_size': np.random.choice(['Small', 'Medium', 'Large'], 1000),
                    'win_probability': np.random.beta(2, 2, 1000)
                }
                df = pd.DataFrame(sales_data)
                st.session_state.multi_analyzer.add_dataset("Sample_Sales", df, {'type': 'sample'})
                st.success("✅ Added Sample Sales Data")
        
        with col2:
            if st.button("👥 Customer Data"):
                # Create sample customer data
                np.random.seed(43)
                customer_data = {
                    'customer_id': [f'CUST_{i:05d}' for i in range(500)],
                    'region': np.random.choice(['North', 'South', 'East', 'West'], 500),
                    'industry': np.random.choice(['Tech', 'Finance', 'Healthcare', 'Retail'], 500),
                    'company_size': np.random.choice(['Small', 'Medium', 'Large'], 500),
                    'annual_revenue': np.random.lognormal(12, 1.5, 500),
                    'signup_date': pd.date_range('2022-01-01', periods=500, freq='2D'),
                    'satisfaction_score': np.random.normal(7.5, 1.5, 500).clip(1, 10)
                }
                df = pd.DataFrame(customer_data)
                st.session_state.multi_analyzer.add_dataset("Sample_Customers", df, {'type': 'sample'})
                st.success("✅ Added Sample Customer Data")
    
    # Main content area
    datasets = st.session_state.multi_analyzer.list_datasets()
    
    if not datasets:
        # Welcome screen
        st.markdown("""
        ## 🚀 Welcome to Multi-Dataset Analyzer!
        
        This powerful tool lets you analyze **multiple datasets simultaneously** to discover:
        
        ### 🔍 Cross-Dataset Insights
        - **Correlations** between datasets
        - **Trends** across time periods
        - **Common patterns** and relationships
        - **Data integration** opportunities
        
        ### 📊 Advanced Analysis Features
        - **Natural language queries** across all datasets
        - **Automatic column matching** and similarity detection
        - **Cross-dataset visualizations** and comparisons
        - **Trend analysis** with time series data
        - **Smart suggestions** based on your data structure
        
        ### 🚀 Get Started:
        1. **Upload datasets** using the sidebar (CSV, Excel, JSON, Parquet)
        2. **Ask questions** that span multiple datasets
        3. **Discover insights** through automated analysis
        4. **Visualize relationships** between your data sources
        
        ### 💡 Example Multi-Dataset Questions:
        - "Compare sales performance across all datasets"
        - "Find correlations between customer data and sales data"
        - "Show trends over time across datasets"
        - "Which datasets can be combined or merged?"
        - "What patterns exist across all my data?"
        
        **👈 Start by uploading your first dataset in the sidebar!**
        """)
    
    else:
        # Main analysis interface
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "💬 Multi-Dataset Questions", 
            "📊 Dataset Overview", 
            "🔗 Cross-Dataset Analysis", 
            "📈 Trends & Correlations",
            "🔍 Individual Dataset"
        ])
        
        with tab1:
            st.header("💬 Ask Questions Across All Datasets")
            
            # Multi-dataset insights
            if len(datasets) >= 2:
                insights = st.session_state.multi_analyzer.generate_cross_dataset_insights()
                
                st.markdown("**🧠 Smart Insights (click to explore):**")
                cols = st.columns(2)
                for i, insight in enumerate(insights[:6]):
                    with cols[i % 2]:
                        if st.button(f"💡 {insight[:60]}...", key=f"insight_{i}"):
                            st.session_state.current_question = f"Tell me more about: {insight}"
            
            # Multi-dataset question suggestions
            st.markdown("**🔍 Multi-Dataset Questions:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📊 Compare Datasets"):
                    st.session_state.current_question = "Compare all datasets"
            with col2:
                if st.button("🔗 Find Connections"):
                    st.session_state.current_question = "What columns can be used to connect datasets?"
            with col3:
                if st.button("📈 Show Trends"):
                    st.session_state.current_question = "Show trends across datasets over time"
            with col4:
                if st.button("🎯 Key Insights"):
                    st.session_state.current_question = "What are the key insights across all datasets?"
            
            # Question input
            question = st.text_input(
                "Ask a question about your datasets:",
                value=st.session_state.get('current_question', ''),
                placeholder="e.g., Compare sales performance across datasets, Find correlations between customer and sales data"
            )
            
            if st.button("🔍 Analyze Across Datasets", type="primary") and question:
                with st.spinner("Analyzing across all datasets..."):
                    # Process multi-dataset query
                    result = st.session_state.multi_analyzer.process_multi_dataset_query(question)
                    
                    if result['success']:
                        answer = result['answer']
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            'question': question,
                            'answer': answer,
                            'result_type': result.get('type', 'multi_dataset'),
                            'timestamp': datetime.now(),
                            'datasets_involved': len(datasets)
                        })
                        
                        # Display answer
                        st.success(f"**Multi-Dataset Analysis:**")
                        st.markdown(answer)
                        
                        # Show additional visualizations if available
                        if result.get('type') == 'comparison':
                            figures = st.session_state.multi_analyzer.create_cross_dataset_visualizations()
                            if figures:
                                st.subheader("📊 Visual Comparison")
                                for name, fig in figures.items():
                                    st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error(f"❌ {result.get('error', 'Analysis failed')}")
            
            # Chat history
            if st.session_state.chat_history:
                st.divider()
                st.subheader("💭 Analysis History")
                
                for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
                    with st.expander(f"Q: {chat['question'][:60]}..." if len(chat['question']) > 60 else f"Q: {chat['question']}"):
                        st.markdown(f"**Question:** {chat['question']}")
                        st.markdown(f"**Answer:** {chat['answer']}")
                        st.caption(f"Type: {chat.get('result_type', 'unknown')} | Datasets: {chat.get('datasets_involved', 0)} | {chat['timestamp'].strftime('%H:%M:%S')}")
        
        with tab2:
            st.header("📊 All Datasets Overview")
            
            # Summary metrics
            total_rows = sum(d['rows'] for d in datasets)
            total_columns = sum(d['columns'] for d in datasets)
            total_size = sum(d['size_mb'] for d in datasets)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Datasets", len(datasets))
            with col2:
                st.metric("Total Rows", f"{total_rows:,}")
            with col3:
                st.metric("Total Columns", total_columns)
            with col4:
                st.metric("Total Size", f"{total_size:.1f} MB")
            
            # Dataset comparison table
            st.subheader("📋 Dataset Comparison")
            comparison_data = []
            for dataset in datasets:
                comparison_data.append({
                    'Dataset': dataset['name'],
                    'Rows': f"{dataset['rows']:,}",
                    'Columns': dataset['columns'],
                    'Size (MB)': f"{dataset['size_mb']:.1f}",
                    'Numeric Cols': len(dataset['numeric_columns']),
                    'Categorical Cols': len(dataset['categorical_columns']),
                    'Date Cols': len(dataset['date_columns'])
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
            
            # Visualizations
            if len(datasets) > 1:
                figures = st.session_state.multi_analyzer.create_cross_dataset_visualizations()
                
                col1, col2 = st.columns(2)
                with col1:
                    if 'size_comparison' in figures:
                        st.plotly_chart(figures['size_comparison'], use_container_width=True)
                with col2:
                    if 'memory_usage' in figures:
                        st.plotly_chart(figures['memory_usage'], use_container_width=True)
                
                if 'column_types' in figures:
                    st.plotly_chart(figures['column_types'], use_container_width=True)
        
        with tab3:
            st.header("🔗 Cross-Dataset Analysis")
            
            if len(datasets) < 2:
                st.warning("⚠️ Upload at least 2 datasets to perform cross-dataset analysis")
            else:
                # Common columns analysis
                st.subheader("🔍 Column Matching Analysis")
                
                common_cols = st.session_state.multi_analyzer.find_common_columns()
                similar_cols = st.session_state.multi_analyzer.find_similar_columns()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🎯 Exact Column Matches**")
                    if common_cols:
                        for col_pattern, appearances in list(common_cols.items())[:10]:
                            datasets_with_col = [app[0] for app in appearances]
                            st.info(f"**{col_pattern}** in: {', '.join(datasets_with_col)}")
                    else:
                        st.warning("No exact column matches found")
                
                with col2:
                    st.markdown("**🔍 Similar Column Names**")
                    if similar_cols:
                        for key, (ds1, col1, ds2, col2, similarity) in list(similar_cols.items())[:5]:
                            st.info(f"**{ds1}.{col1}** ↔ **{ds2}.{col2}** ({similarity:.1%})")
                    else:
                        st.warning("No similar columns detected")
                
                # Integration opportunities
                st.subheader("🔗 Data Integration Opportunities")
                
                if common_cols or similar_cols:
                    st.success(f"✅ Found {len(common_cols)} exact matches and {len(similar_cols)} similar columns")
                    st.info("💡 These columns could be used for joining or merging datasets")
                    
                    # Show potential join keys
                    potential_keys = []
                    for col_pattern, appearances in common_cols.items():
                        if len(appearances) >= 2:
                            # Check if this could be a key column
                            key_indicators = ['id', 'key', 'code', 'number']
                            if any(indicator in col_pattern.lower() for indicator in key_indicators):
                                potential_keys.append((col_pattern, appearances))
                    
                    if potential_keys:
                        st.markdown("**🔑 Potential Join Keys:**")
                        for col_pattern, appearances in potential_keys:
                            datasets_involved = [app[0] for app in appearances]
                            st.success(f"🔑 **{col_pattern}** could join: {', '.join(datasets_involved)}")
                else:
                    st.warning("⚠️ Limited integration opportunities detected. Consider manual column mapping.")
        
        with tab4:
            st.header("📈 Trends & Correlations")
            
            if len(datasets) < 2:
                st.warning("⚠️ Upload at least 2 datasets to analyze trends and correlations")
            else:
                # Time series analysis
                st.subheader("📅 Time Series Analysis")
                
                # Find datasets with date columns
                datasets_with_dates = []
                for dataset_info in datasets:
                    if dataset_info['date_columns']:
                        datasets_with_dates.append({
                            'name': dataset_info['name'],
                            'date_columns': dataset_info['date_columns'],
                            'numeric_columns': dataset_info['numeric_columns']
                        })
                
                if datasets_with_dates:
                    st.success(f"📊 Found {len(datasets_with_dates)} datasets with time data")
                    
                    for ds_info in datasets_with_dates:
                        with st.expander(f"📈 {ds_info['name']} - Time Series Potential"):
                            st.markdown(f"**Date Columns:** {', '.join(ds_info['date_columns'])}")
                            st.markdown(f"**Numeric Columns:** {', '.join(ds_info['numeric_columns'][:5])}{'...' if len(ds_info['numeric_columns']) > 5 else ''}")
                else:
                    st.info("ℹ️ No date/time columns detected. Upload datasets with temporal data for trend analysis.")
                
                # Correlation analysis
                st.subheader("🔗 Cross-Dataset Correlations")
                
                common_numeric = {}
                common_cols = st.session_state.multi_analyzer.find_common_columns()
                
                for col_pattern, appearances in common_cols.items():
                    numeric_appearances = []
                    for dataset_name, col_name in appearances:
                        dataset_info = next((d for d in datasets if d['name'] == dataset_name), None)
                        if dataset_info and col_name in dataset_info['numeric_columns']:
                            numeric_appearances.append((dataset_name, col_name))
                    
                    if len(numeric_appearances) >= 2:
                        common_numeric[col_pattern] = numeric_appearances
                
                if common_numeric:
                    st.success(f"🔢 Found {len(common_numeric)} numeric column patterns for correlation analysis")
                    
                    for pattern, appearances in common_numeric.items():
                        dataset_names = [app[0] for app in appearances]
                        st.info(f"**{pattern}** across: {', '.join(dataset_names)}")
                    
                    # Perform correlation analysis
                    if st.button("🔍 Analyze Correlations"):
                        with st.spinner("Calculating cross-dataset correlations..."):
                            correlations = st.session_state.multi_analyzer.analyze_cross_dataset_correlations(common_numeric)
                            
                            for pattern, corr_info in correlations.items():
                                st.subheader(f"📊 Correlation Analysis: {pattern}")
                                
                                if 'strongest_correlation' in corr_info and corr_info['strongest_correlation']:
                                    strongest = corr_info['strongest_correlation']
                                    st.metric(
                                        f"Strongest Correlation",
                                        f"{strongest['correlation']:.3f}",
                                        f"{strongest['strength']} correlation"
                                    )
                                    st.info(f"Between: {strongest['columns'][0]} ↔ {strongest['columns'][1]}")
                else:
                    st.info("ℹ️ No common numeric columns found for correlation analysis.")
        
        with tab5:
            st.header("🔍 Individual Dataset Analysis")
            
            # Dataset selector
            dataset_names = [d['name'] for d in datasets]
            selected_dataset = st.selectbox(
                "Select Dataset to Analyze",
                dataset_names,
                index=dataset_names.index(st.session_state.current_dataset) if st.session_state.current_dataset in dataset_names else 0
            )
            
            if selected_dataset:
                # Get the dataset
                dataset_data = st.session_state.multi_analyzer.datasets[selected_dataset]['data']
                analyzer = UniversalDataAnalyzer(dataset_data)
                nlp_analyzer = AdvancedNLPAnalyzer(dataset_data)
                
                # Dataset summary
                summary = analyzer.get_data_summary()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Rows", f"{summary['total_rows']:,}")
                with col2:
                    st.metric("Columns", summary['total_columns'])
                with col3:
                    st.metric("Missing Values", f"{summary['missing_values']:,}")
                with col4:
                    st.metric("Memory", f"{summary['memory_usage_mb']:.1f} MB")
                
                # Quick questions for this dataset
                st.subheader(f"💬 Ask Questions About {selected_dataset}")
                
                suggestions = nlp_analyzer.get_smart_suggestions()
                if suggestions:
                    st.markdown("**💡 Suggestions:**")
                    cols = st.columns(3)
                    for i, suggestion in enumerate(suggestions[:6]):
                        with cols[i % 3]:
                            if st.button(suggestion, key=f"single_suggestion_{i}"):
                                result = nlp_analyzer.process_natural_language_query(suggestion)
                                if result['success']:
                                    st.success(f"**Answer:** {result['answer']}")
                
                # Data preview
                st.subheader("🔍 Data Preview")
                st.dataframe(dataset_data.head(100), use_container_width=True)
                
                # Column analysis
                st.subheader("📊 Column Analysis")
                selected_column = st.selectbox(
                    "Select Column",
                    dataset_data.columns,
                    key="individual_column_select"
                )
                
                if selected_column:
                    col_data = dataset_data[selected_column]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Data Type", str(col_data.dtype))
                    with col2:
                        st.metric("Unique Values", col_data.nunique())
                    with col3:
                        st.metric("Missing Values", col_data.isnull().sum())
                    
                    # Visualization based on column type
                    if pd.api.types.is_numeric_dtype(col_data):
                        fig = px.histogram(dataset_data, x=selected_column, title=f"Distribution of {selected_column}")
                        st.plotly_chart(fig, use_container_width=True)
                    elif col_data.nunique() < 20:
                        value_counts = col_data.value_counts().head(10)
                        fig = px.bar(x=value_counts.index, y=value_counts.values, title=f"Top Values in {selected_column}")
                        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()