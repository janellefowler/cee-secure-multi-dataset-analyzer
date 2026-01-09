#!/usr/bin/env python3
"""
Quick deployment script for Secure Multi-Dataset Analyzer
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def check_git_repo():
    """Check if we're in a git repository"""
    return os.path.exists('.git')

def setup_git_repo():
    """Initialize git repository if needed"""
    if not check_git_repo():
        print("\n📁 Setting up Git repository...")
        run_command("git init", "Initialize Git repository")
        run_command("git add .", "Add all files to Git")
        run_command('git commit -m "Initial commit - Secure Multi-Dataset Analyzer"', "Create initial commit")
        
        print("\n🔗 Next steps:")
        print("1. Create a repository on GitHub")
        print("2. Run: git remote add origin https://github.com/yourusername/your-repo-name.git")
        print("3. Run: git push -u origin main")
        return False
    return True

def create_streamlit_config():
    """Create Streamlit configuration for deployment"""
    config_dir = Path(".streamlit")
    config_dir.mkdir(exist_ok=True)
    
    config_content = """[server]
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
"""
    
    config_file = config_dir / "config.toml"
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print("✅ Created Streamlit configuration")

def create_secrets_template():
    """Create secrets template for Streamlit Cloud"""
    secrets_content = """# Copy this to Streamlit Cloud Secrets section
# Go to: https://share.streamlit.io/ -> Your App -> Settings -> Secrets

SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-gmail-app-password"
APP_BASE_URL = "https://your-app-name.streamlit.app"
"""
    
    with open("streamlit_secrets.toml", 'w') as f:
        f.write(secrets_content)
    
    print("✅ Created secrets template (streamlit_secrets.toml)")

def show_deployment_options():
    """Show deployment options to user"""
    print("\n🚀 Deployment Options:")
    print("\n1. 🌐 Local Network (Immediate)")
    print("   - Share: http://192.168.1.104:8508")
    print("   - Works on same WiFi/network only")
    print("   - Keep your computer running")
    
    print("\n2. ☁️ Streamlit Cloud (Recommended)")
    print("   - Free hosting")
    print("   - Go to: https://share.streamlit.io/")
    print("   - Connect your GitHub repo")
    print("   - Main file: secure_multi_dataset_app.py")
    
    print("\n3. 🚂 Railway (Production)")
    print("   - Go to: https://railway.app/")
    print("   - Deploy from GitHub")
    print("   - $5/month after free tier")
    
    print("\n4. 🎨 Render (Free Tier)")
    print("   - Go to: https://render.com/")
    print("   - Connect GitHub repo")
    print("   - Free tier available")

def main():
    print("🔐 Secure Multi-Dataset Analyzer - Deployment Helper")
    print("=" * 60)
    
    # Check current setup
    print("\n📋 Checking current setup...")
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        sys.exit(1)
    
    # Check if main app exists
    if not os.path.exists("secure_multi_dataset_app.py"):
        print("❌ secure_multi_dataset_app.py not found")
        sys.exit(1)
    
    print("✅ Main application files found")
    
    # Setup Git if needed
    git_ready = setup_git_repo()
    
    # Create deployment configurations
    create_streamlit_config()
    create_secrets_template()
    
    # Show deployment options
    show_deployment_options()
    
    print("\n" + "=" * 60)
    print("🎯 Quick Start Recommendations:")
    print("\n📱 For immediate sharing (same network):")
    print("   Share this link: http://192.168.1.104:8508")
    
    print("\n☁️ For team deployment (recommended):")
    print("   1. Push code to GitHub")
    print("   2. Deploy on Streamlit Cloud")
    print("   3. Configure secrets using streamlit_secrets.toml")
    print("   4. Share your app URL with team")
    
    print("\n📧 Team member onboarding:")
    print("   1. Login as admin (admin@dataanalyzer.com / admin123)")
    print("   2. Change admin password immediately")
    print("   3. Go to Admin Panel -> Invitations")
    print("   4. Invite team members by email")
    print("   5. They register with invitation tokens")
    
    print("\n🔒 Security reminders:")
    print("   - Change default admin password")
    print("   - Use strong passwords")
    print("   - Set up email for invitations")
    print("   - Review user access regularly")
    
    print("\n📖 For detailed instructions, see: DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    main()