#!/usr/bin/env python3
"""
Script to discover the correct AWS account ID for QuickSight
"""

import boto3
import os
from dotenv import load_dotenv

def discover_account_info():
    """Discover AWS account information"""
    
    load_dotenv()
    
    print("🔍 Discovering AWS Account Information...")
    print("=" * 50)
    
    try:
        # Get STS client to find account ID
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Get caller identity
        identity = sts_client.get_caller_identity()
        account_id = identity['Account']
        user_arn = identity['Arn']
        
        print(f"✅ AWS Account ID: {account_id}")
        print(f"✅ User ARN: {user_arn}")
        print()
        
        # Now try QuickSight with the correct account ID
        print("🔍 Testing QuickSight with discovered account ID...")
        
        quicksight_client = boto3.client(
            'quicksight',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # List dashboards
        response = quicksight_client.list_dashboards(
            AwsAccountId=account_id,
            MaxResults=50
        )
        
        dashboards = response.get('DashboardSummaryList', [])
        print(f"✅ Found {len(dashboards)} dashboards in account {account_id}")
        
        # Look for our target dashboard
        target_dashboard_id = os.getenv('QUICKSIGHT_DASHBOARD_ID')
        dashboard_found = False
        
        for dashboard in dashboards:
            dashboard_id = dashboard.get('DashboardId')
            dashboard_name = dashboard.get('Name', 'Unknown')
            
            if dashboard_id == target_dashboard_id:
                print(f"🎯 Target dashboard found!")
                print(f"   ID: {dashboard_id}")
                print(f"   Name: {dashboard_name}")
                dashboard_found = True
            else:
                print(f"   - {dashboard_name} (ID: {dashboard_id})")
        
        if not dashboard_found:
            print(f"\n⚠️ Target dashboard {target_dashboard_id} not found in this account")
            print("   Available dashboards are listed above")
        
        return account_id
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    account_id = discover_account_info()
    
    if account_id:
        print(f"\n💡 Update your .env file with:")
        print(f"QUICKSIGHT_ACCOUNT_ID={account_id}")