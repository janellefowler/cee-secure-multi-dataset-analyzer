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
import hashlib

# Import our modules
from src.advanced_nlp_analyzer import AdvancedNLPAnalyzer
from src.large_dataset_handler import SmartDataLoader, LargeDatasetHandler
from src.multi_dataset_analyzer import MultiDatasetAnalyzer
from src.persistent_storage import DatasetManager
from src.authentication import require_authentication, get_auth_manager

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Secure Multi-Dataset Analyzer",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

class SecureMultiDatasetAnalyzer:
    """Secure multi-dataset analyzer with authentication and persistent storage"""
    
    def __init__(self, user_email: str):
        self.user_email = user_email
        self.dataset_manager = DatasetManager()
        self.multi_analyzer = MultiDatasetAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # Load user's datasets
        self._load_user_datasets()
    
    def _load_user_datasets(self):
        """Load all datasets accessible to the user"""
        datasets = self.dataset_manager.list_user_datasets(self.user_email)
        
        for dataset_info in datasets:
            try:
                data = self.dataset_manager.get_dataset(dataset_info['id'], self.user_email)
                if data is not None:
                    self.multi_analyzer.add_dataset(
                        dataset_info['name'], 
                        data, 
                        dataset_info
                    )
                    self.logger.info(f"Loaded dataset '{dataset_info['name']}' for user {self.user_email}")
            except Exception as e:
                self.logger.error(f"Error loading dataset {dataset_info['name']}: {str(e)}")
    
    def add_dataset(self, name: str, data: pd.DataFrame, metadata: Dict[str, Any]) -> str:
        """Add a new dataset with persistent storage"""
        
        # Save to persistent storage
        dataset_id = self.dataset_manager.add_dataset(name, data, metadata, self.user_email)
        
        if dataset_id:
            # Add to multi-analyzer
            full_metadata = self.dataset_manager.get_dataset_info(dataset_id)
            self.multi_analyzer.add_dataset(name, data, full_metadata)
            return dataset_id
        
        return ""
    
    def remove_dataset(self, dataset_name: str) -> bool:
        """Remove a dataset"""
        
        # Find dataset ID
        datasets = self.dataset_manager.list_user_datasets(self.user_email)
        dataset_id = None
        
        for dataset_info in datasets:
            if dataset_info['name'] == dataset_name:
                dataset_id = dataset_info['id']
                break
        
        if dataset_id:
            # Check if user owns the dataset
            dataset_info = self.dataset_manager.get_dataset_info(dataset_id)
            if dataset_info and dataset_info['uploaded_by'] == self.user_email:
                # Remove from storage
                if self.dataset_manager.delete_dataset(dataset_id, self.user_email):
                    # Remove from multi-analyzer
                    self.multi_analyzer.remove_dataset(dataset_name)
                    return True
        
        return False
    
    def share_dataset(self, dataset_name: str, target_email: str, access_level: str = "read") -> bool:
        """Share a dataset with another user"""
        
        # Find dataset ID
        datasets = self.dataset_manager.list_user_datasets(self.user_email)
        dataset_id = None
        
        for dataset_info in datasets:
            if dataset_info['name'] == dataset_name:
                dataset_id = dataset_info['id']
                break
        
        if dataset_id:
            return self.dataset_manager.share_dataset(dataset_id, target_email, access_level, self.user_email)
        
        return False
    
    def get_datasets_info(self) -> List[Dict[str, Any]]:
        """Get information about all accessible datasets"""
        return self.dataset_manager.list_user_datasets(self.user_email)
    
    def get_multi_analyzer(self) -> MultiDatasetAnalyzer:
        """Get the multi-dataset analyzer"""
        return self.multi_analyzer

def load_data_from_file(uploaded_file) -> Dict[str, Any]:
    """Load data from various file formats with smart handling for large files"""
    
    if uploaded_file is None:
        return {'success': False, 'error': 'No file provided'}
    
    # Use smart data loader
    smart_loader = SmartDataLoader()
    return smart_loader.load_data(uploaded_file)

def main():
    # Require authentication
    user_info = require_authentication()
    
    if not user_info:
        return  # Authentication interface is shown
    
    # Initialize secure analyzer
    if 'secure_analyzer' not in st.session_state or st.session_state.get('current_user') != user_info['email']:
        st.session_state.secure_analyzer = SecureMultiDatasetAnalyzer(user_info['email'])
        st.session_state.current_user = user_info['email']
        st.session_state.chat_history = []
    
    secure_analyzer = st.session_state.secure_analyzer
    multi_analyzer = secure_analyzer.get_multi_analyzer()
    
    # Header with user info and logout
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title("🔐 Secure Multi-Dataset Analyzer")
        st.markdown(f"*Welcome back, **{user_info['full_name']}** ({user_info['role']})*")
    
    with col2:
        if user_info['role'] == 'admin':
            if st.button("👥 Admin Panel"):
                st.session_state.show_admin = True
    
    with col3:
        auth_manager = get_auth_manager()
        if st.button("🚪 Logout"):
            auth_manager.logout_user(st.session_state.get('session_id', ''))
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Show admin panel if requested
    if st.session_state.get('show_admin', False) and user_info['role'] == 'admin':
        show_admin_panel()
        return
    
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
        
        # Dataset configuration
        if uploaded_file:
            default_name = uploaded_file.name.split('.')[0]
            dataset_name = st.text_input(
                "Dataset Name",
                value=default_name,
                help="Give your dataset a memorable name"
            )
            
            description = st.text_area(
                "Description (optional)",
                placeholder="Describe what this dataset contains..."
            )
            
            # Privacy settings
            col1, col2 = st.columns(2)
            with col1:
                is_public = st.checkbox("Make Public", help="Allow all users to access this dataset")
            with col2:
                access_level = st.selectbox("Access Level", ["private", "shared", "public"])
            
            if st.button("📤 Upload Dataset", type="primary"):
                if dataset_name:
                    with st.spinner(f"Uploading {dataset_name}..."):
                        result = load_data_from_file(uploaded_file)
                        
                        if result['success']:
                            df = result['data']
                            
                            # Prepare metadata
                            metadata = {
                                'filename': uploaded_file.name,
                                'file_size_mb': uploaded_file.size / 1024 / 1024,
                                'loading_method': result['loading_method'],
                                'is_sample': result.get('is_sample', False),
                                'sample_size': result.get('sample_size', len(df)),
                                'total_rows': result.get('total_rows', len(df)),
                                'description': description,
                                'is_public': is_public,
                                'access_level': access_level,
                                'tags': []
                            }
                            
                            # Add to secure analyzer
                            dataset_id = secure_analyzer.add_dataset(dataset_name, df, metadata)
                            
                            if dataset_id:
                                # Show success message
                                if result.get('is_sample', False):
                                    st.success(f"✅ Uploaded '{dataset_name}' (sample: {result['sample_size']:,} of {result['total_rows']:,} rows)")
                                else:
                                    st.success(f"✅ Uploaded '{dataset_name}' ({len(df):,} rows × {len(df.columns)} columns)")
                                
                                st.info(f"🔑 Dataset ID: {dataset_id}")
                                st.rerun()
                            else:
                                st.error("❌ Failed to save dataset")
                        else:
                            st.error(f"❌ Error loading file: {result['error']}")
                else:
                    st.error("Please provide a dataset name")
        
        # Current datasets section
        st.divider()
        st.subheader("📊 Your Datasets")
        
        datasets = secure_analyzer.get_datasets_info()
        
        if datasets:
            for i, dataset_info in enumerate(datasets):
                with st.expander(f"📋 {dataset_info['name']}", expanded=i==0):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rows", f"{dataset_info['rows']:,}")
                        st.metric("Columns", dataset_info['columns'])
                    with col2:
                        st.metric("Size", f"{dataset_info['file_size_mb']:.1f} MB")
                        st.metric("Uploaded", datetime.fromisoformat(dataset_info['upload_date']).strftime("%m/%d"))
                    
                    # Show ownership and access info
                    if dataset_info['uploaded_by'] == user_info['email']:
                        st.success("👑 You own this dataset")
                    else:
                        st.info(f"📤 Shared by: {dataset_info['uploaded_by']}")
                    
                    if dataset_info.get('is_public', False):
                        st.info("🌍 Public dataset")
                    
                    # Dataset actions
                    col1, col2, col3 = st.columns(3)
                    
                    # Only show share/delete for owned datasets
                    if dataset_info['uploaded_by'] == user_info['email']:
                        with col1:
                            if st.button(f"🔗 Share", key=f"share_{i}"):
                                st.session_state[f'show_share_{i}'] = True
                        
                        with col2:
                            if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                                if secure_analyzer.remove_dataset(dataset_info['name']):
                                    st.success("Dataset deleted")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete dataset")
                    
                    # Show sharing interface
                    if st.session_state.get(f'show_share_{i}', False):
                        st.markdown("**Share with user:**")
                        share_email = st.text_input(f"Email address", key=f"share_email_{i}")
                        share_access = st.selectbox(f"Access level", ["read", "write"], key=f"share_access_{i}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Share", key=f"confirm_share_{i}"):
                                if share_email:
                                    if secure_analyzer.share_dataset(dataset_info['name'], share_email, share_access):
                                        st.success(f"Shared with {share_email}")
                                        st.session_state[f'show_share_{i}'] = False
                                        st.rerun()
                                    else:
                                        st.error("Failed to share dataset")
                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_share_{i}"):
                                st.session_state[f'show_share_{i}'] = False
                                st.rerun()
        else:
            st.info("No datasets available. Upload files above to get started!")
        
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
                
                metadata = {
                    'description': 'Sample sales data for testing',
                    'is_public': True,
                    'access_level': 'public',
                    'tags': ['sample', 'sales']
                }
                
                secure_analyzer.add_dataset("Sample_Sales", df, metadata)
                st.success("✅ Added Sample Sales Data")
                st.rerun()
        
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
                
                metadata = {
                    'description': 'Sample customer data for testing',
                    'is_public': True,
                    'access_level': 'public',
                    'tags': ['sample', 'customers']
                }
                
                secure_analyzer.add_dataset("Sample_Customers", df, metadata)
                st.success("✅ Added Sample Customer Data")
                st.rerun()
    
    # Main content area
    datasets = multi_analyzer.list_datasets()
    
    if not datasets:
        # Welcome screen
        st.markdown(f"""
        ## 🚀 Welcome to Secure Multi-Dataset Analyzer, {user_info['full_name']}!
        
        ### 🔐 Your Secure Data Analysis Platform
        
        This platform provides **secure, collaborative data analysis** with:
        
        - **🔒 User Authentication**: Secure access control and user management
        - **💾 Persistent Storage**: Your datasets are saved and accessible across sessions
        - **🤝 Data Sharing**: Share datasets securely with team members
        - **🔍 Cross-Dataset Analysis**: Analyze multiple datasets simultaneously
        - **💬 Natural Language Queries**: Ask questions in plain English
        
        ### 📊 Your Role: {user_info['role'].title()}
        
        {"**Admin privileges**: You can manage users and access all datasets" if user_info['role'] == 'admin' else "**User access**: You can upload, analyze, and share your own datasets"}
        
        ### 🚀 Get Started:
        1. **Upload datasets** using the sidebar
        2. **Share with team members** using email addresses
        3. **Ask questions** across multiple datasets
        4. **Discover insights** through automated analysis
        
        ### 💡 Example Multi-Dataset Questions:
        - "Compare performance across all my datasets"
        - "Find correlations between customer and sales data"
        - "What trends exist across all uploaded data?"
        - "Which datasets can be integrated together?"
        
        **👈 Upload your first dataset or try sample data to begin!**
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
            st.header("💬 Ask Questions Across All Your Datasets")
            
            # Show data access info
            owned_count = sum(1 for d in datasets if d.get('uploaded_by') == user_info['email'])
            shared_count = len(datasets) - owned_count
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Datasets", len(datasets))
            with col2:
                st.metric("Owned by You", owned_count)
            with col3:
                st.metric("Shared with You", shared_count)
            
            # Multi-dataset insights
            if len(datasets) >= 2:
                insights = multi_analyzer.generate_cross_dataset_insights()
                
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
                    st.session_state.current_question = "Compare all my datasets"
            with col2:
                if st.button("🔗 Find Connections"):
                    st.session_state.current_question = "What columns can be used to connect my datasets?"
            with col3:
                if st.button("📈 Show Trends"):
                    st.session_state.current_question = "Show trends across my datasets over time"
            with col4:
                if st.button("🎯 Key Insights"):
                    st.session_state.current_question = "What are the key insights across all my datasets?"
            
            # Question input
            question = st.text_input(
                "Ask a question about your datasets:",
                value=st.session_state.get('current_question', ''),
                placeholder="e.g., Compare sales performance across datasets, Find correlations between customer and sales data"
            )
            
            if st.button("🔍 Analyze Across Datasets", type="primary") and question:
                with st.spinner("Analyzing across all datasets..."):
                    # Process multi-dataset query
                    result = multi_analyzer.process_multi_dataset_query(question)
                    
                    if result['success']:
                        answer = result['answer']
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            'question': question,
                            'answer': answer,
                            'result_type': result.get('type', 'multi_dataset'),
                            'timestamp': datetime.now(),
                            'datasets_involved': len(datasets),
                            'user': user_info['email']
                        })
                        
                        # Display answer
                        st.success(f"**Multi-Dataset Analysis:**")
                        st.markdown(answer)
                        
                        # Show additional visualizations if available
                        if result.get('type') == 'comparison':
                            figures = multi_analyzer.create_cross_dataset_visualizations()
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
                    'Owner': dataset.get('uploaded_by', 'Unknown'),
                    'Access': 'Public' if dataset.get('is_public', False) else 'Private',
                    'Uploaded': datetime.fromisoformat(dataset['upload_date']).strftime('%Y-%m-%d')
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
            
            # Visualizations
            if len(datasets) > 1:
                figures = multi_analyzer.create_cross_dataset_visualizations()
                
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
                
                common_cols = multi_analyzer.find_common_columns()
                similar_cols = multi_analyzer.find_similar_columns()
                
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
                common_cols = multi_analyzer.find_common_columns()
                
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
                            correlations = multi_analyzer.analyze_cross_dataset_correlations(common_numeric)
                            
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
                dataset_names
            )
            
            if selected_dataset:
                # Get the dataset
                dataset_data = multi_analyzer.datasets[selected_dataset]['data']
                
                # Show dataset info
                dataset_info = next(d for d in datasets if d['name'] == selected_dataset)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Rows", f"{dataset_info['rows']:,}")
                with col2:
                    st.metric("Columns", dataset_info['columns'])
                with col3:
                    st.metric("Owner", dataset_info.get('uploaded_by', 'Unknown'))
                with col4:
                    st.metric("Access", 'Public' if dataset_info.get('is_public', False) else 'Private')
                
                # Description
                if dataset_info.get('description'):
                    st.info(f"📝 **Description:** {dataset_info['description']}")
                
                # Quick analysis
                nlp_analyzer = AdvancedNLPAnalyzer(dataset_data)
                
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

def show_admin_panel():
    """Show admin panel for user management"""
    
    st.title("👥 Admin Panel")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("*User management and system administration*")
    with col2:
        if st.button("← Back to Analysis"):
            st.session_state.show_admin = False
            st.rerun()
    
    auth_manager = get_auth_manager()
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "📋 Email Whitelist", "📧 Legacy Invitations", "📊 System Stats"])
    
    with tab1:
        st.subheader("User Management")
        
        # List all users
        users = auth_manager.list_users('admin')
        
        if users:
            for user in users:
                with st.expander(f"👤 {user['full_name']} ({user['email']})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Role:** {user['role']}")
                        st.write(f"**Status:** {'Active' if user['is_active'] else 'Inactive'}")
                    
                    with col2:
                        st.write(f"**Created:** {datetime.fromisoformat(user['created_date']).strftime('%Y-%m-%d')}")
                        if user['last_login']:
                            st.write(f"**Last Login:** {datetime.fromisoformat(user['last_login']).strftime('%Y-%m-%d %H:%M')}")
                    
                    with col3:
                        # Admin actions
                        new_role = st.selectbox(f"Change Role", ['user', 'admin'], 
                                              index=0 if user['role'] == 'user' else 1,
                                              key=f"role_{user['email']}")
                        
                        if st.button(f"Update Role", key=f"update_{user['email']}"):
                            if auth_manager.update_user_role(user['email'], new_role, st.session_state.user_info['email']):
                                st.success("Role updated")
                                st.rerun()
                        
                        if user['is_active'] and st.button(f"Deactivate", key=f"deactivate_{user['email']}"):
                            if auth_manager.deactivate_user(user['email'], st.session_state.user_info['email']):
                                st.success("User deactivated")
                                st.rerun()
    
    with tab2:
        st.subheader("📋 Email Whitelist Management")
        st.markdown("*Control who can register for the system*")
        
        # Add new email to whitelist
        with st.form("whitelist_form"):
            st.markdown("**Add Email to Whitelist**")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                email = st.text_input("Email Address", placeholder="user@company.com")
                notes = st.text_input("Notes (Optional)", placeholder="Team member, contractor, etc.")
            
            with col2:
                role = st.selectbox("Role", ['user', 'admin'])
            
            if st.form_submit_button("✅ Add to Whitelist", type="primary"):
                if email:
                    if auth_manager.add_to_whitelist(email, role, st.session_state.user_info['email'], notes):
                        st.success(f"✅ Added {email} to whitelist")
                        st.rerun()
                    else:
                        st.error("Failed to add email to whitelist")
                else:
                    st.error("Please enter an email address")
        
        st.divider()
        
        # List current whitelist
        st.markdown("**Current Whitelist**")
        whitelist = auth_manager.list_whitelist('admin')
        
        if whitelist:
            for entry in whitelist:
                status_color = "🟢" if entry['is_active'] else "🔴"
                
                with st.expander(f"{status_color} {entry['email']} ({entry['role']})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Role:** {entry['role']}")
                        st.write(f"**Added by:** {entry['added_by']}")
                        st.write(f"**Added:** {datetime.fromisoformat(entry['added_date']).strftime('%Y-%m-%d %H:%M')}")
                        if entry['notes']:
                            st.write(f"**Notes:** {entry['notes']}")
                        st.write(f"**Status:** {'Active' if entry['is_active'] else 'Inactive'}")
                    
                    with col2:
                        st.info("Whitelist management features coming soon!")
        else:
            st.info("No emails in whitelist. Add emails above to allow registration.")
        
        # Bulk import section
        st.divider()
        st.markdown("**Bulk Import**")
        
        with st.expander("📤 Import Multiple Emails"):
            st.markdown("Enter one email per line:")
            bulk_emails = st.text_area("Email List", placeholder="user1@company.com\nuser2@company.com\nuser3@company.com")
            bulk_role = st.selectbox("Role for all", ['user', 'admin'], key="bulk_role")
            bulk_notes = st.text_input("Notes for all", placeholder="Bulk import batch 1")
            
            if st.button("📥 Import All"):
                if bulk_emails:
                    emails = [email.strip() for email in bulk_emails.split('\n') if email.strip()]
                    success_count = 0
                    
                    for email in emails:
                        if auth_manager.add_to_whitelist(email, bulk_role, st.session_state.user_info['email'], bulk_notes):
                            success_count += 1
                    
                    st.success(f"✅ Successfully imported {success_count} out of {len(emails)} emails")
                    if success_count > 0:
                        st.rerun()
    
    with tab3:
        st.subheader("📧 Legacy Invitation System")
        st.info("⚠️ The invitation system is now legacy. Use the Email Whitelist instead for better control.")
        
        st.markdown("The old invitation system is still available but not recommended. Use the Email Whitelist tab instead.")
    
    with tab4:
        st.subheader("System Statistics")
        
        # Get basic stats
        users = auth_manager.list_users('admin')
        whitelist = auth_manager.list_whitelist('admin')
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", len(users))
        with col2:
            active_users = sum(1 for u in users if u['is_active'])
            st.metric("Active Users", active_users)
        with col3:
            st.metric("Whitelisted Emails", len([w for w in whitelist if w['is_active']]))
        with col4:
            admin_users = sum(1 for u in users if u['role'] == 'admin')
            st.metric("Admin Users", admin_users)
