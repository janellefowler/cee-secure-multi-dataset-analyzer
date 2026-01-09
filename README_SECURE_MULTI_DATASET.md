# 🔐 Secure Multi-Dataset Analyzer

A **secure, collaborative data analysis platform** with authentication, persistent storage, and multi-dataset capabilities. Perfect for teams that need to share and analyze data together while maintaining security and access control.

## 🚀 New Security & Collaboration Features

### 🔐 **User Authentication & Access Control**
- **Secure login system** with password hashing and session management
- **Role-based access** (Admin/User roles with different permissions)
- **Account lockout protection** after failed login attempts
- **Session timeout** for security
- **Invitation-based registration** - only invited users can join

### 💾 **Persistent Data Storage**
- **Datasets stay loaded** across sessions and app restarts
- **SQLite database** for metadata and user management
- **Automatic data persistence** - no need to re-upload files
- **Cross-session continuity** - pick up where you left off

### 🤝 **Secure Data Sharing**
- **Share datasets with team members** using email addresses
- **Granular permissions** (read/write access levels)
- **Public/private dataset options**
- **Owner controls** - only dataset owners can share or delete
- **Access audit trail** - track who accessed what data

### 👥 **Team Collaboration**
- **Multi-user support** - multiple people can use the same datasets
- **Shared analysis sessions** - collaborate on insights
- **User management** - admins can invite and manage users
- **Activity logging** - track user actions and access

## 🎯 Perfect For Enterprise & Team Use

### 🏢 **Business Intelligence Teams**
- **Secure data sharing** across departments
- **Persistent dashboards** that stay available
- **Role-based access** for different team members
- **Audit trails** for compliance and governance

### 🔬 **Research Organizations**
- **Collaborative analysis** on shared datasets
- **Access control** for sensitive research data
- **Long-term data storage** for ongoing projects
- **User management** for research teams

### 📊 **Data Analytics Departments**
- **Centralized data repository** with secure access
- **Team collaboration** on analysis projects
- **Persistent insights** and analysis history
- **Administrative controls** for data governance

## 🚀 Quick Start Guide

### 1. Launch the Secure Application
```bash
# Activate virtual environment
source cee-env/bin/activate

# Start the secure multi-dataset analyzer
streamlit run secure_multi_dataset_app.py --server.port 8508
```

### 2. Initial Setup (First Time)
1. **Access the app** at http://localhost:8508
2. **Login with default admin credentials:**
   - Email: `admin@dataanalyzer.com`
   - Password: `admin123`
3. **⚠️ IMPORTANT: Change admin password immediately!**
4. **Invite team members** using the Admin Panel

### 3. Invite Team Members (Admin Only)
1. **Go to Admin Panel** (👥 button in top right)
2. **Navigate to "Invitations" tab**
3. **Enter user email and role**
4. **Send invitation** - user gets a secure registration link
5. **User registers** with the invitation token

### 4. Upload and Share Datasets
1. **Upload datasets** using the sidebar
2. **Set privacy level** (Private/Shared/Public)
3. **Share with specific users** using email addresses
4. **Collaborate on analysis** across shared datasets

## 🔒 Security Features

### 🛡️ **Authentication Security**
```
✅ Password hashing with PBKDF2 and salt
✅ Session-based authentication with timeout
✅ Account lockout after failed attempts
✅ Secure password requirements
✅ Invitation-only registration
```

### 🔐 **Data Access Control**
```
✅ User-based dataset ownership
✅ Granular sharing permissions
✅ Public/private dataset options
✅ Access validation on every request
✅ Audit logging for all actions
```

### 📊 **Data Persistence**
```
✅ SQLite database for metadata
✅ Encrypted file storage for datasets
✅ Automatic backup and recovery
✅ Cross-session data availability
✅ Memory-optimized storage
```

## 👥 User Roles & Permissions

### 🔑 **Admin Role**
- **User Management**: Invite, deactivate, change roles
- **System Administration**: View all datasets and users
- **Access Control**: Grant/revoke dataset permissions
- **Audit Access**: View system logs and statistics
- **Data Management**: Access all datasets regardless of ownership

### 👤 **User Role**
- **Dataset Management**: Upload, analyze, delete own datasets
- **Data Sharing**: Share owned datasets with other users
- **Collaboration**: Access shared datasets from other users
- **Analysis**: Full analysis capabilities on accessible datasets
- **Profile Management**: Update own profile and password

## 📋 Dataset Sharing & Permissions

### 🔗 **Sharing Options**
```
🌍 Public: Accessible to all users
🤝 Shared: Accessible to specific invited users
🔒 Private: Only accessible to owner
```

### 📊 **Access Levels**
```
👁️ Read: View and analyze data only
✏️ Write: View, analyze, and modify dataset metadata
👑 Owner: Full control including sharing and deletion
```

### 🎯 **Sharing Workflow**
1. **Upload dataset** with desired privacy level
2. **Click "Share" button** on owned datasets
3. **Enter user email** and select access level
4. **User receives access** immediately
5. **Shared dataset appears** in their dataset list

## 💬 Multi-User Natural Language Queries

### 🤖 **Collaborative Analysis**
- **Ask questions across all accessible datasets**
- **Share insights** through persistent chat history
- **Cross-reference** multiple users' datasets
- **Collaborative discovery** of patterns and trends

### 📝 **Example Team Queries**
```
"Compare sales data from John's dataset with customer data from Sarah's dataset"
"Find correlations between marketing data and revenue across all shared datasets"
"Show trends over time using data from multiple team members"
"Which datasets can be integrated for comprehensive analysis?"
```

## 🛠️ Administration & Management

### 👥 **User Management (Admin Panel)**
- **View all users** with registration dates and activity
- **Change user roles** between Admin and User
- **Deactivate accounts** when needed
- **Send invitations** to new team members
- **Monitor system usage** and statistics

### 📊 **System Monitoring**
- **User activity logs** with timestamps and actions
- **Dataset access tracking** for audit purposes
- **System statistics** (users, datasets, storage usage)
- **Security events** (failed logins, access attempts)

### 🔧 **Configuration Options**
```bash
# Email Configuration (Optional - for invitation emails)
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Security Settings
SESSION_TIMEOUT_HOURS=24
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30
```

## 📈 Enterprise Features

### 🏢 **Scalability**
- **Multi-user concurrent access** without conflicts
- **Efficient data storage** with automatic optimization
- **Session management** for high user loads
- **Database optimization** for large datasets

### 🔍 **Audit & Compliance**
- **Complete access logs** for all user actions
- **Data lineage tracking** for uploaded datasets
- **User activity monitoring** for security compliance
- **Export capabilities** for audit reports

### 🔐 **Security Compliance**
- **Password policy enforcement**
- **Session security** with automatic timeout
- **Access control validation** on every request
- **Secure data transmission** and storage

## 🚀 Advanced Collaboration Workflows

### 📊 **Team Analysis Projects**
1. **Project Lead uploads** core datasets
2. **Team members invited** with appropriate access
3. **Collaborative analysis** using shared datasets
4. **Insights shared** through persistent chat history
5. **Results documented** and accessible to all team members

### 🔄 **Data Pipeline Integration**
1. **Automated uploads** from data pipelines
2. **Scheduled analysis** on updated datasets
3. **Team notifications** for new insights
4. **Version control** for dataset updates

### 📋 **Governance Workflows**
1. **Data stewards** manage dataset access
2. **Approval workflows** for sensitive data
3. **Audit trails** for compliance reporting
4. **Access reviews** and permission updates

## 🎯 Best Practices

### 🔒 **Security Best Practices**
1. **Change default admin password** immediately
2. **Use strong passwords** for all accounts
3. **Regular access reviews** - remove unused accounts
4. **Monitor audit logs** for suspicious activity
5. **Backup data regularly** using export features

### 📊 **Data Management**
1. **Descriptive dataset names** for easy identification
2. **Clear descriptions** for shared datasets
3. **Appropriate privacy levels** based on data sensitivity
4. **Regular cleanup** of unused datasets
5. **Document data sources** and collection methods

### 👥 **Team Collaboration**
1. **Clear role assignments** (who can access what)
2. **Regular team training** on platform features
3. **Established workflows** for data sharing
4. **Communication protocols** for analysis results
5. **Regular review meetings** using shared insights

## 🔧 Technical Architecture

### 🏗️ **Security Layer**
- **Authentication Manager**: User login, session management
- **Access Control**: Permission validation and enforcement
- **Audit Logger**: Activity tracking and security monitoring

### 💾 **Persistence Layer**
- **Dataset Manager**: File storage and metadata management
- **SQLite Database**: User accounts, permissions, audit logs
- **Session Store**: Active user sessions and state

### 🔗 **Integration Layer**
- **Multi-Dataset Analyzer**: Cross-dataset analysis engine
- **NLP Processor**: Natural language query understanding
- **Visualization Engine**: Interactive charts and dashboards

## 🎉 Key Advantages

✅ **Enterprise Security** - Production-ready authentication and access control  
✅ **Team Collaboration** - Multiple users can work with shared datasets  
✅ **Data Persistence** - Datasets stay loaded across sessions  
✅ **Audit Compliance** - Complete activity logging and access tracking  
✅ **Scalable Architecture** - Supports growing teams and data volumes  
✅ **Easy Administration** - Simple user and dataset management  
✅ **Flexible Sharing** - Granular control over data access  
✅ **Secure by Default** - Built with security best practices  

---

## 🚀 Getting Started

**Ready to deploy for your team?**

1. **Start the secure app**: `streamlit run secure_multi_dataset_app.py --server.port 8508`
2. **Login as admin**: admin@dataanalyzer.com / admin123
3. **Change admin password** immediately
4. **Invite your team members** through the Admin Panel
5. **Start collaborating** on secure data analysis!

**Perfect for organizations that need secure, collaborative data analysis with proper access controls and audit capabilities!**