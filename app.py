import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import our modules
from src.data_connector import DataIntegrator
from src.analytics_engine import ContentEffectivenessAnalyzer
from src.nlp_processor import NaturalLanguageProcessor
from src.dashboard_import import create_upload_interface
from src.quicksight_auth import create_midway_auth_interface, QuickSightDashboardManager

# Page configuration
st.set_page_config(
    page_title="Content Effectiveness Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Simple authentication bypass for now
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Content Effectiveness Engine")
    st.markdown("*Please enter your name to access the analytics dashboard*")
    
    name = st.text_input("Your Name:", placeholder="Enter your name")
    
    if st.button("Access Dashboard", type="primary") and name:
        st.session_state.authenticated = True
        st.session_state.user_name = name
        st.rerun()
    
    if name:
        st.info("👆 Click 'Access Dashboard' to continue")
    
else:
    # Main application - authenticated user
    name = st.session_state.get('user_name', 'User')
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📊 Content Effectiveness Engine")
        st.markdown("*Automated analysis of content effectiveness across Highspot, SIM, and Amazon Learn*")
    with col2:
        st.markdown(f"**Welcome {name}**")
        if st.button('Logout'):
            st.session_state.authenticated = False
            st.session_state.user_name = None
            st.rerun()
    
    # Initialize session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'integrated_data' not in st.session_state:
        st.session_state.integrated_data = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'show_connection_panel' not in st.session_state:
        st.session_state.show_connection_panel = True
    
    # Main interface
    if st.session_state.integrated_data is None:
        # === DATA CONNECTION SECTION ===
        st.header("🔗 Connect Your Data")
        st.markdown("Connect to your QuickSight dashboard to start analyzing content effectiveness data.")
        
        # Connection tabs
        tab1, tab2 = st.tabs(["🔐 Midway SSO Authentication", "📤 Import Data File"])
        
        with tab1:
            st.markdown("**Connect directly to Amazon's internal QuickSight environment**")
            
            # Initialize authenticator in session state
            if 'midway_auth' not in st.session_state:
                from src.quicksight_auth import QuickSightMidwayAuthenticator
                st.session_state.midway_auth = QuickSightMidwayAuthenticator()
            
            auth = st.session_state.midway_auth
            
            if not auth.authenticated:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if not st.session_state.get('midway_auth_initiated', False):
                        if st.button("🔑 Start Midway SSO Login", type="primary", key="sso_login"):
                            result = auth.initiate_midway_auth()
                            
                            if result['success']:
                                st.session_state.midway_auth_initiated = True
                                st.success("✅ SSO authentication initiated!")
                                
                                # Show the SSO URL
                                st.markdown("**[Click here to authenticate via Midway SSO]({})** 🔗".format(result['auth_url']))
                                st.markdown("Complete the login in the browser, then return here and click 'Check Status'")
                                st.rerun()
                            else:
                                st.error(f"❌ {result['message']}")
                    
                    else:
                        st.info("🔄 SSO authentication initiated. Complete the login in the browser.")
                        
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            if st.button("🔍 Check Authentication Status", key="check_auth"):
                                result = auth.check_authentication_status()
                                
                                if result['success']:
                                    st.success(f"✅ {result['message']}")
                                    st.rerun()
                                else:
                                    st.warning(f"⏳ {result['message']}")
                        
                        with col_b:
                            if st.button("🔄 Restart Authentication", key="restart_auth"):
                                st.session_state.midway_auth_initiated = False
                                auth.logout()
                                st.rerun()
                
                with col2:
                    st.markdown("**About Midway SSO**")
                    st.markdown("""
                    - Same login as other Amazon tools
                    - Secure federated authentication
                    - Direct dashboard access
                    """)
            
            else:
                st.success("✅ Authenticated via Midway SSO")
                
                # Show available dashboards
                manager = QuickSightDashboardManager(auth)
                dashboards = manager.list_dashboards()
                
                st.markdown("**Available Dashboards:**")
                
                for dashboard in dashboards:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**📈 {dashboard['name']}**")
                            st.caption(f"{dashboard['description']} • {dashboard['owner']}")
                        
                        with col2:
                            if st.button(f"📊 Load Data", key=f"load_{dashboard['id']}"):
                                with st.spinner("Loading dashboard data..."):
                                    try:
                                        df = manager.extract_dashboard_data(dashboard['id'])
                                        
                                        # Store in session state
                                        st.session_state.integrated_data = df
                                        st.session_state.data_loaded = True
                                        st.session_state.data_source = f"QuickSight Dashboard: {dashboard['name']} (Midway Auth)"
                                        st.session_state.show_connection_panel = False
                                        
                                        st.success(f"✅ Loaded {len(df)} records from {dashboard['name']}")
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"Error loading data: {str(e)}")
        
        with tab2:
            st.markdown("**Upload data exported from your QuickSight dashboard**")
            
            # File upload
            uploaded_file = st.file_uploader(
                "Choose your data file",
                type=['csv', 'xlsx', 'xls'],
                help="Export data from your QuickSight dashboard and upload it here"
            )
            
            if uploaded_file is not None:
                from src.dashboard_import import DashboardDataImporter
                
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
                        
                        # Show data summary
                        summary = validation['data_summary']
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Rows", f"{summary['total_rows']:,}")
                        with col2:
                            st.metric("Unique Sellers", f"{summary['unique_sellers']:,}")
                        with col3:
                            st.metric("Date Range", summary['date_range'])
                        
                        # Store the imported data
                        st.session_state.integrated_data = df
                        st.session_state.data_loaded = True
                        st.session_state.data_source = "Imported from QuickSight"
                        st.session_state.show_connection_panel = False
                        
                        st.rerun()
                    else:
                        st.error("❌ Data validation failed")
                        for error in validation['errors']:
                            st.error(f"Error: {error}")
    
    else:
        # === MAIN ANALYTICS INTERFACE ===
        
        # Data source header
        data_source = st.session_state.get('data_source', 'Unknown source')
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if "QuickSight Dashboard:" in data_source:
                st.success(f"📊 Connected: {data_source}")
            elif data_source == "Imported from QuickSight":
                st.success("📊 Using imported QuickSight data")
            else:
                st.info(f"📊 Data loaded: {data_source}")
        
        with col2:
            if st.button("🔄 Change Data Source"):
                st.session_state.integrated_data = None
                st.session_state.data_loaded = False
                st.session_state.show_connection_panel = True
                st.rerun()
        
        st.divider()
        
        # Main content area with tabs
        tab1, tab2, tab3 = st.tabs(["💬 Ask Questions", "📊 Dashboard", "🔬 Detailed Analytics"])
        
        with tab1:
            # === NATURAL LANGUAGE QUERY INTERFACE ===
            st.header("💬 Ask Questions About Your Data")
            
            # Quick example buttons
            st.markdown("**Quick Questions:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📈 Deal Cycle Analysis", key="q1"):
                    st.session_state.current_query = "How does seller accreditation affect deal cycles?"
            
            with col2:
                if st.button("🎯 Content Effectiveness", key="q2"):
                    st.session_state.current_query = "What's the correlation between Highspot usage and win rates?"
            
            with col3:
                if st.button("👥 Manager Impact", key="q3"):
                    st.session_state.current_query = "Compare performance when both seller and sales manager are accredited"
            
            # Query input
            query_value = st.session_state.get('current_query', '')
            user_query = st.text_input(
                "Ask your question:",
                value=query_value,
                placeholder="e.g., Show me sellers who visit Highspot frequently - how do their deal cycles compare?",
                key="main_query"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                analyze_button = st.button("🔍 Analyze", type="primary")
            
            if analyze_button and user_query:
                with st.spinner("Analyzing your question..."):
                    try:
                        nlp_processor = NaturalLanguageProcessor()
                        result = nlp_processor.process_query(user_query, st.session_state.integrated_data)
                        
                        if result['success']:
                            # Add to chat history
                            st.session_state.chat_history.append({
                                'query': user_query,
                                'result': result,
                                'timestamp': datetime.now()
                            })
                            
                            # Display results
                            st.markdown("---")
                            st.subheader("📋 Analysis Results")
                            
                            # Show intent and entities
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"**Query Type:** {result['intent'].replace('_', ' ').title()}")
                            with col2:
                                if result['entities']['metrics']:
                                    st.info(f"**Metrics:** {', '.join(result['entities']['metrics'])}")
                            
                            # Generate natural language response first
                            if os.getenv('OPENAI_API_KEY'):
                                response = nlp_processor.generate_natural_response(user_query, result['analysis'])
                                st.markdown("**💬 Answer:**")
                                st.success(response)
                            else:
                                # Fallback to formatted response
                                if 'analysis' in result:
                                    analysis = result['analysis']
                                    
                                    # Create a natural language summary
                                    summary = "Based on your question, here's what I found:\n\n"
                                    
                                    if 'key_metrics' in analysis:
                                        metrics = analysis['key_metrics']
                                        summary += f"📊 **Key Numbers:**\n"
                                        if 'total_interactions' in metrics:
                                            summary += f"• We analyzed {metrics['total_interactions']:,} interactions\n"
                                        if 'content_found_rate' in metrics:
                                            summary += f"• {metrics['content_found_rate']} of sellers found what they needed\n"
                                        if 'avg_deal_cycle' in metrics:
                                            summary += f"• Average deal cycle is {metrics['avg_deal_cycle']}\n"
                                        summary += "\n"
                                    
                                    if 'actionable_insights' in analysis:
                                        summary += "💡 **Key Insights:**\n"
                                        for insight in analysis['actionable_insights']:
                                            summary += f"• {insight}\n"
                                    
                                    st.markdown(summary)
                            
                            # Show key metrics in a clean format
                            if 'analysis' in result and 'key_metrics' in result['analysis']:
                                metrics = result['analysis']['key_metrics']
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    if 'total_interactions' in metrics:
                                        st.metric("Total Records", f"{metrics['total_interactions']:,}")
                                with col2:
                                    if 'content_found_rate' in metrics:
                                        st.metric("Success Rate", metrics['content_found_rate'])
                                with col3:
                                    if 'avg_deal_cycle' in metrics:
                                        st.metric("Avg Deal Cycle", metrics['avg_deal_cycle'])
                            
                            # Show detailed data if available (collapsed by default)
                            if 'analysis' in result:
                                with st.expander("🔍 View Detailed Analysis Data", expanded=False):
                                    # Format the detailed analysis better
                                    analysis = result['analysis']
                                    
                                    if 'detailed_analyses' in analysis:
                                        for analysis_type, data in analysis['detailed_analyses'].items():
                                            st.subheader(f"📈 {analysis_type.replace('_', ' ').title()}")
                                            
                                            # Show key findings for each analysis type
                                            if analysis_type == 'highspot_effectiveness':
                                                if 'content_found_rate' in data:
                                                    st.write(f"Content found rate: {data['content_found_rate']:.1%}")
                                                if 'accreditation_significance' in data:
                                                    sig = data['accreditation_significance']
                                                    if sig.get('significant'):
                                                        st.success("✅ Accreditation significantly impacts content discovery")
                                                    else:
                                                        st.info("ℹ️ No significant difference between accredited and non-accredited sellers")
                                            
                                            elif analysis_type == 'manager_impact':
                                                if 'best_performing_combo' in data:
                                                    best = data['best_performing_combo']
                                                    st.success(f"🏆 Best combo: {best['combination']} - {best['avg_deal_cycle']:.1f} days, {best['win_rate']:.1%} win rate")
                                            
                                            elif analysis_type == 'content_gaps':
                                                if 'difficult_search_scenarios' in data:
                                                    st.warning(f"⚠️ {data['difficult_search_scenarios']} difficult search scenarios identified")
                                            
                                            st.divider()
                        else:
                            st.error(f"Error: {result['error']}")
                    
                    except Exception as e:
                        st.error(f"Error processing query: {str(e)}")
            
            # Chat history
            if st.session_state.chat_history:
                st.markdown("---")
                st.subheader("📝 Recent Questions")
                
                # Show last 3 queries
                for i, chat in enumerate(reversed(st.session_state.chat_history[-3:])):
                    with st.expander(f"Q: {chat['query'][:60]}..." if len(chat['query']) > 60 else f"Q: {chat['query']}"):
                        st.markdown(f"**Asked:** {chat['timestamp'].strftime('%H:%M:%S')}")
                        st.markdown(f"**Query:** {chat['query']}")
                        st.markdown(f"**Type:** {chat['result']['intent'].replace('_', ' ').title()}")
                        
                        if 'actionable_insights' in chat['result'].get('analysis', {}):
                            st.markdown("**Insights:**")
                            for insight in chat['result']['analysis']['actionable_insights'][:2]:
                                st.markdown(f"• {insight}")
        
        with tab2:
            # === DASHBOARD VIEW ===
            st.header("📊 Executive Dashboard")
            
            data = st.session_state.integrated_data
            analyzer = ContentEffectivenessAnalyzer(data)
            
            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_interactions = len(data)
                st.metric("Total Interactions", f"{total_interactions:,}")
            
            with col2:
                content_found_rate = data['content_found'].mean() if 'content_found' in data.columns else 0
                st.metric("Content Found Rate", f"{content_found_rate:.1%}")
            
            with col3:
                avg_deal_cycle = data['deal_cycle_days'].mean() if 'deal_cycle_days' in data.columns else 0
                st.metric("Avg Deal Cycle", f"{avg_deal_cycle:.1f} days")
            
            with col4:
                avg_win_rate = data['win_probability'].mean() if 'win_probability' in data.columns else (data['actual_win'].mean() if 'actual_win' in data.columns else 0)
                st.metric("Avg Win Rate", f"{avg_win_rate:.1%}")
            
            st.divider()
            
            # Generate insights
            insights = analyzer.generate_insights_summary()
            
            # Key insights
            st.subheader("🎯 Key Insights")
            if 'actionable_insights' in insights:
                for insight in insights['actionable_insights']:
                    st.info(f"💡 {insight}")
            
            # Visualizations
            st.subheader("📊 Visualizations")
            figures = analyzer.create_visualizations()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'content_found_by_accreditation' in figures:
                    st.plotly_chart(figures['content_found_by_accreditation'], use_container_width=True)
            
            with col2:
                if 'content_gaps' in figures:
                    st.plotly_chart(figures['content_gaps'], use_container_width=True)
            
            if 'deal_cycle_vs_usage' in figures:
                st.plotly_chart(figures['deal_cycle_vs_usage'], use_container_width=True)
        
        with tab3:
            # === DETAILED ANALYTICS ===
            st.header("🔬 Detailed Analytics")
            
            data = st.session_state.integrated_data
            analyzer = ContentEffectivenessAnalyzer(data)
            
            # Analysis selection
            analysis_type = st.selectbox(
                "Select Analysis Type:",
                ["Highspot Effectiveness", "Deal Cycle Correlation", "Manager Impact", "Content Gaps"]
            )
            
            if analysis_type == "Highspot Effectiveness":
                results = analyzer.analyze_highspot_effectiveness()
                st.subheader("📊 Highspot Content Effectiveness Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Content Found Rate", f"{results['content_found_rate']:.1%}")
                with col2:
                    st.metric("Total Visits", f"{results['total_visits']:,}")
                
                if 'accredited_analysis' in results:
                    st.subheader("Analysis by Accreditation Status")
                    st.dataframe(results['accredited_analysis'])
                
                if results.get('accreditation_significance', {}).get('significant'):
                    st.success("✅ Accreditation has a statistically significant impact on content discovery")
                else:
                    st.info("ℹ️ No statistically significant difference found between accredited and non-accredited sellers")
            
            elif analysis_type == "Deal Cycle Correlation":
                results = analyzer.analyze_deal_cycle_correlation()
                st.subheader("📈 Deal Cycle Correlation Analysis")
                
                if 'error' not in results:
                    correlation = results.get('highspot_usage_deal_cycle_correlation', 0)
                    st.metric("Correlation Coefficient", f"{correlation:.3f}")
                    
                    if correlation < -0.3:
                        st.success("✅ Strong negative correlation: Higher Highspot usage → Shorter deal cycles")
                    elif correlation > 0.3:
                        st.warning("⚠️ Positive correlation: Higher usage → Longer cycles (investigate)")
                    else:
                        st.info("ℹ️ Weak correlation between Highspot usage and deal cycles")
                    
                    if 'usage_segment_analysis' in results:
                        st.subheader("Performance by Usage Level")
                        st.dataframe(results['usage_segment_analysis'])
                else:
                    st.error(results['error'])
            
            elif analysis_type == "Manager Impact":
                results = analyzer.analyze_manager_impact()
                st.subheader("👥 Sales Manager Impact Analysis")
                
                if 'accreditation_combo_analysis' in results:
                    st.dataframe(results['accreditation_combo_analysis'])
                
                if 'best_performing_combo' in results:
                    best = results['best_performing_combo']
                    st.success(f"🏆 Best Performance: {best['combination']}")
                    st.info(f"Average Deal Cycle: {best['avg_deal_cycle']:.1f} days")
                    st.info(f"Win Rate: {best['win_rate']:.1%}")
            
            elif analysis_type == "Content Gaps":
                results = analyzer.identify_content_gaps()
                st.subheader("🔍 Content Gap Analysis")
                
                if 'content_gaps_by_category' in results:
                    st.subheader("Gaps by Content Category")
                    st.dataframe(results['content_gaps_by_category'])
                
                if 'gap_percentage_by_category' in results:
                    st.subheader("Gap Percentage by Category")
                    gap_df = pd.DataFrame({
                        'Category': results['gap_percentage_by_category'].index,
                        'Gap Percentage': results['gap_percentage_by_category'].values
                    })
                    fig = px.bar(gap_df, x='Category', y='Gap Percentage', 
                               title='Content Gap Percentage by Category')
                    st.plotly_chart(fig, use_container_width=True)
                
                difficult_searches = results.get('difficult_search_scenarios', 0)
                if difficult_searches > 0:
                    st.warning(f"⚠️ {difficult_searches} instances of difficult content searches identified")