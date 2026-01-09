#!/usr/bin/env python3
"""
Quick test script to verify QuickSight connection
"""

import os
from dotenv import load_dotenv
from src.quicksight_connector import AmazonQuickSightConnector

def test_quicksight_connection():
    """Test the QuickSight connection with current credentials"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Testing QuickSight Connection...")
    print("=" * 50)
    
    # Show configuration (without sensitive data)
    print(f"Account ID: {os.getenv('QUICKSIGHT_ACCOUNT_ID')}")
    print(f"Dashboard ID: {os.getenv('QUICKSIGHT_DASHBOARD_ID')}")
    print(f"Region: {os.getenv('AWS_REGION')}")
    print(f"Access Key: {os.getenv('AWS_ACCESS_KEY_ID')[:10]}...")
    print()
    
    # Test connection
    try:
        connector = AmazonQuickSightConnector()
        result = connector.test_connection()
        
        print("📊 Connection Test Results:")
        print("-" * 30)
        
        if result['connection_status'] == 'success':
            print("✅ Status: SUCCESS")
            print(f"✅ Account ID: {result['account_id']}")
            print(f"✅ Dashboard Found: {'Yes' if result.get('dashboard_found') else 'No'}")
            print(f"✅ Total Dashboards: {result.get('dashboard_count', 0)}")
            print(f"✅ Message: {result['message']}")
            
            if result.get('dashboard_found'):
                print("\n🎯 Your target dashboard is accessible!")
                
                # Try to get dashboard info
                print("\n📋 Getting dashboard details...")
                dashboard_info = connector.get_dashboard_info()
                if dashboard_info:
                    dashboard = dashboard_info.get('Dashboard', {})
                    print(f"   Name: {dashboard.get('Name', 'Unknown')}")
                    print(f"   Version: {dashboard.get('Version', {}).get('VersionNumber', 'Unknown')}")
                    print(f"   Status: {dashboard.get('Version', {}).get('Status', 'Unknown')}")
                
                # Try to list datasets
                print("\n📊 Listing datasets in dashboard...")
                datasets = connector.list_datasets_in_dashboard()
                if datasets:
                    print(f"   Found {len(datasets)} datasets:")
                    for i, dataset in enumerate(datasets, 1):
                        print(f"   {i}. {dataset.get('identifier', 'Unknown')} (ID: {dataset.get('dataset_id', 'Unknown')})")
                else:
                    print("   No datasets found or unable to access dataset list")
            else:
                print("\n⚠️ Target dashboard not found in accessible dashboards")
                print("   This might be due to permissions or the dashboard might be in a different account/region")
        else:
            print("❌ Status: FAILED")
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            print(f"❌ Message: {result.get('message', 'Connection failed')}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_quicksight_connection()