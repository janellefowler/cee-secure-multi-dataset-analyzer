import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional
import io
import json
from datetime import datetime

class DashboardDataImporter:
    """
    Import data from QuickSight dashboard exports
    Supports CSV, Excel, and JSON formats
    """
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.json']
        
    def import_from_file(self, uploaded_file) -> pd.DataFrame:
        """Import data from uploaded file"""
        
        if uploaded_file is None:
            return pd.DataFrame()
            
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        try:
            if file_extension == 'csv':
                df = pd.read_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file)
            elif file_extension == 'json':
                df = pd.read_json(uploaded_file)
            else:
                st.error(f"Unsupported file format: {file_extension}")
                return pd.DataFrame()
                
            # Clean and standardize the data
            df = self._standardize_columns(df)
            
            return df
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return pd.DataFrame()
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to match CEE expectations"""
        
        # Common column mappings from QuickSight exports
        column_mappings = {
            # Seller information
            'seller': 'seller_id',
            'seller_id': 'seller_id',
            'seller_name': 'seller_id',
            'sales_rep': 'seller_id',
            'rep_id': 'seller_id',
            
            # Manager information
            'manager': 'sales_manager_id',
            'sales_manager': 'sales_manager_id',
            'manager_id': 'sales_manager_id',
            'sm_id': 'sales_manager_id',
            
            # Time fields
            'date': 'interaction_date',
            'timestamp': 'interaction_timestamp',
            'interaction_date': 'interaction_date',
            'visit_date': 'interaction_date',
            'access_date': 'interaction_date',
            
            # Content fields
            'content': 'content_type',
            'content_type': 'content_type',
            'material_type': 'content_type',
            'document_type': 'content_type',
            
            # Platform fields
            'platform': 'platform',
            'source': 'platform',
            'system': 'platform',
            
            # Engagement metrics
            'time_spent': 'time_spent_minutes',
            'duration': 'time_spent_minutes',
            'engagement_time': 'time_spent_minutes',
            'session_duration': 'time_spent_minutes',
            
            # Success metrics
            'found': 'content_found',
            'success': 'content_found',
            'located': 'content_found',
            'discovered': 'content_found',
            
            # Accreditation
            'accredited': 'seller_accredited',
            'certified': 'seller_accredited',
            'trained': 'seller_accredited',
            
            # Deal metrics
            'deal_value': 'deal_value_usd',
            'opportunity_value': 'deal_value_usd',
            'deal_size': 'deal_value_usd',
            'cycle_time': 'deal_cycle_days',
            'sales_cycle': 'deal_cycle_days',
            'win_rate': 'win_probability',
            'close_rate': 'win_probability',
            
            # Support metrics
            'sim_ticket': 'sim_ticket_created',
            'help_contact': 'pp_help_contacted',
            'support_ticket': 'sim_ticket_created'
        }
        
        # Normalize column names (lowercase, replace spaces/special chars)
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
        
        # Apply mappings
        df = df.rename(columns=column_mappings)
        
        # Convert data types
        df = self._convert_data_types(df)
        
        return df
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to appropriate data types"""
        
        # Date columns
        date_columns = ['interaction_date', 'interaction_timestamp', 'visit_date', 'access_date']
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass
        
        # Boolean columns
        boolean_columns = ['content_found', 'seller_accredited', 'sm_accredited', 
                          'sim_ticket_created', 'pp_help_contacted']
        for col in boolean_columns:
            if col in df.columns:
                try:
                    # Handle various boolean representations
                    df[col] = df[col].map({
                        'true': True, 'false': False, 'True': True, 'False': False,
                        'yes': True, 'no': False, 'Yes': True, 'No': False,
                        'y': True, 'n': False, 'Y': True, 'N': False,
                        1: True, 0: False, '1': True, '0': False
                    }).fillna(df[col])
                except:
                    pass
        
        # Numeric columns
        numeric_columns = ['time_spent_minutes', 'deal_value_usd', 'deal_cycle_days', 'win_probability']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    pass
        
        return df
    
    def validate_imported_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the imported data and provide feedback"""
        
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': [],
            'data_summary': {}
        }
        
        if df.empty:
            validation_results['is_valid'] = False
            validation_results['errors'].append("No data found in the uploaded file")
            return validation_results
        
        # More flexible validation - look for any identifier column
        identifier_columns = ['seller_id', 'seller', 'seller_name', 'sales_rep', 'rep_id', 'user_id', 'employee_id']
        has_identifier = any(col in df.columns for col in identifier_columns)
        
        if not has_identifier:
            # Try to find any column that could be an identifier
            potential_ids = [col for col in df.columns if 'id' in col.lower() or 'name' in col.lower() or 'seller' in col.lower()]
            if potential_ids:
                validation_results['warnings'].append(f"No standard seller ID found, but found potential identifiers: {potential_ids}")
                validation_results['suggestions'].append("Consider renaming one of these columns to 'seller_id' for better analysis")
            else:
                validation_results['warnings'].append("No clear identifier column found - analysis may be limited")
        
        # Check for useful data columns (more flexible)
        useful_columns = {
            'time_data': ['date', 'timestamp', 'time', 'created', 'modified', 'interaction'],
            'content_data': ['content', 'type', 'category', 'material', 'document'],
            'engagement_data': ['time_spent', 'duration', 'engagement', 'session', 'minutes', 'seconds'],
            'outcome_data': ['found', 'success', 'result', 'outcome', 'win', 'close', 'deal'],
            'platform_data': ['platform', 'source', 'system', 'tool', 'application']
        }
        
        found_categories = []
        for category, keywords in useful_columns.items():
            if any(any(keyword in col.lower() for keyword in keywords) for col in df.columns):
                found_categories.append(category.replace('_data', ''))
        
        if found_categories:
            validation_results['suggestions'].append(f"Found data categories: {', '.join(found_categories)}")
        
        # Data quality checks (more lenient)
        if has_identifier:
            # Find the actual identifier column
            id_col = next((col for col in identifier_columns if col in df.columns), None)
            if id_col:
                null_count = df[id_col].isnull().sum()
                if null_count > len(df) * 0.5:  # More than 50% null
                    validation_results['warnings'].append(f"More than half of the identifier values are missing")
                elif null_count > 0:
                    validation_results['warnings'].append(f"{null_count} rows have missing identifiers")
        
        # Check for reasonable data size
        if len(df) < 10:
            validation_results['warnings'].append("Very small dataset - results may not be meaningful")
        elif len(df) > 100000:
            validation_results['warnings'].append("Large dataset - processing may take longer")
        
        # Generate data summary
        validation_results['data_summary'] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'date_range': self._get_date_range(df),
            'unique_sellers': self._count_unique_identifiers(df),
            'columns_found': list(df.columns),
            'data_categories': found_categories
        }
        
        return validation_results
    
    def _count_unique_identifiers(self, df: pd.DataFrame) -> int:
        """Count unique identifiers in the data"""
        identifier_columns = ['seller_id', 'seller', 'seller_name', 'sales_rep', 'rep_id', 'user_id', 'employee_id']
        
        for col in identifier_columns:
            if col in df.columns:
                return df[col].nunique()
        
        # Fallback: look for any column that might be an identifier
        for col in df.columns:
            if 'id' in col.lower() or 'name' in col.lower():
                return df[col].nunique()
        
        return 0
    
    def _get_date_range(self, df: pd.DataFrame) -> str:
        """Get the date range of the data"""
        
        date_columns = ['interaction_date', 'interaction_timestamp', 'visit_date', 'access_date']
        
        for col in date_columns:
            if col in df.columns:
                try:
                    dates = pd.to_datetime(df[col], errors='coerce').dropna()
                    if len(dates) > 0:
                        return f"{dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}"
                except:
                    continue
        
        return "No date information found"

class QuickSightURLConnector:
    """
    Connect to QuickSight dashboards using embedded URLs
    This approach uses the dashboard's embed functionality
    """
    
    def __init__(self):
        self.dashboard_url = None
        
    def set_dashboard_url(self, url: str):
        """Set the QuickSight dashboard URL"""
        self.dashboard_url = url
        
    def generate_embed_instructions(self) -> str:
        """Generate instructions for accessing the dashboard"""
        
        instructions = """
        ## 📊 How to Export Data from Your QuickSight Dashboard
        
        Since your dashboard is in Amazon's internal account (`amazonbi`), here's how to get the data:
        
        ### Method 1: Direct Export from Dashboard
        1. **Open your dashboard**: [Your Dashboard](https://us-east-1.quicksight.aws.amazon.com/sn/account/amazonbi/dashboards/2721e5d2-fd1c-4993-9ea3-9c7cbb234f90?directory_alias=amazonbi&ignore=true)
        2. **Click the Export button** (usually in the top-right corner)
        3. **Select "Export to CSV"** or "Export to Excel"
        4. **Download the file** and upload it below
        
        ### Method 2: Export Individual Visuals
        1. **Click on any chart/table** in your dashboard
        2. **Click the three dots (⋮)** in the top-right of the visual
        3. **Select "Export to CSV"**
        4. **Repeat for key visuals** you want to analyze
        
        ### Method 3: Use QuickSight's Data Export
        1. **Go to the Datasets section** in QuickSight
        2. **Find your dataset** (likely named something with "content effectiveness" or "private pricing")
        3. **Export the raw dataset**
        
        ### What Data to Export:
        The CEE works best with data containing:
        - **Seller IDs** and **Manager IDs**
        - **Content interaction dates**
        - **Content types** (Private Pricing, Product Info, etc.)
        - **Platform usage** (Highspot, Amazon Learn, etc.)
        - **Time spent** on content
        - **Success metrics** (content found, deal outcomes)
        - **Accreditation status**
        """
        
        return instructions

def create_upload_interface():
    """Create the Streamlit interface for data upload"""
    
    st.subheader("📤 Import Data from QuickSight Dashboard")
    
    # Show instructions
    connector = QuickSightURLConnector()
    with st.expander("💡 How to Export Data from Your Dashboard"):
        st.markdown(connector.generate_embed_instructions())
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your exported data file",
        type=['csv', 'xlsx', 'xls', 'json'],
        help="Export data from your QuickSight dashboard and upload it here"
    )
    
    if uploaded_file is not None:
        importer = DashboardDataImporter()
        
        # Import the data
        with st.spinner("Processing uploaded file..."):
            df = importer.import_from_file(uploaded_file)
        
        if not df.empty:
            # Validate the data
            validation = importer.validate_imported_data(df)
            
            # Show validation results
            if validation['is_valid']:
                st.success("✅ Data imported successfully!")
            else:
                st.error("❌ Data validation failed")
                for error in validation['errors']:
                    st.error(f"Error: {error}")
            
            # Show warnings
            for warning in validation['warnings']:
                st.warning(f"Warning: {warning}")
            
            # Show data summary
            summary = validation['data_summary']
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Rows", f"{summary['total_rows']:,}")
            with col2:
                st.metric("Columns", summary['total_columns'])
            with col3:
                st.metric("Unique Sellers", f"{summary['unique_sellers']:,}")
            with col4:
                st.metric("Date Range", summary['date_range'])
            
            # Show column mapping
            with st.expander("📋 Column Mapping Results"):
                st.write("**Columns found in your data:**")
                st.write(summary['columns_found'])
            
            # Preview the data
            with st.expander("🔍 Data Preview"):
                st.dataframe(df.head(10))
            
            return df
    
    return None