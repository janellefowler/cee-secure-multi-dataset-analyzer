# Content Effectiveness Engine (CEE)

A secure, automated analytics platform that connects data across Highspot, Amazon Learn, SIM, and Quick Suite to track content effectiveness and business outcomes.

## 🎯 Purpose

CEE automates the manual analysis currently requiring 660 hours annually by:
- Tracking Seller and Sales Manager interactions with Private Pricing content
- Correlating interactions with business outcomes (SIM volumes, win rates)
- Identifying content gaps and improvement opportunities
- Providing natural language query capabilities for data insights

## 🔒 Security Features

- **User Authentication**: Secure login system with bcrypt password hashing
- **Access Control**: Only authorized users can access datasets and dashboard
- **Session Management**: Secure cookie-based sessions with configurable expiry
- **Environment Variables**: Sensitive credentials stored in .env files

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or create the project directory
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual credentials
# - AWS credentials for QuickSight access
# - OpenAI API key for natural language processing
# - QuickSight dataset IDs
```

### 3. Authentication Setup

```bash
# Run the authentication setup script
python setup_auth.py

# Follow the prompts to:
# - Add authorized users
# - Set secure passwords
# - Configure cookie settings
```

### 4. Launch the Application

```bash
# Start the Streamlit application
streamlit run app.py

# The app will open in your browser at http://localhost:8501
```

## 📊 Features

### Dashboard
- **Executive Overview**: Key metrics and performance indicators
- **Visual Analytics**: Interactive charts and graphs
- **Real-time Insights**: Automated analysis of content effectiveness

### Natural Language Queries
Ask questions like:
- "Show me sellers who are accredited and visit Highspot frequently - how do their deal cycles compare?"
- "What's the correlation between Highspot usage and win rates?"
- "Compare performance when both seller and sales manager are accredited"
- "What content gaps exist in Private Pricing materials?"

### Detailed Analytics
- **Highspot Effectiveness**: Content discovery success rates
- **Deal Cycle Correlation**: Usage patterns vs. sales performance
- **Manager Impact**: Sales manager accreditation effects
- **Content Gap Analysis**: Identification of missing or ineffective content

### Data Management
- **Secure Data Refresh**: Automated pulls from QuickSight
- **Data Quality Monitoring**: Missing data detection and reporting
- **Export Capabilities**: Download analysis results

## 🔧 Configuration

### AWS QuickSight Setup
1. Ensure your AWS credentials have QuickSight access
2. Obtain dataset IDs from your QuickSight dashboards
3. Configure the dataset IDs in your .env file

### OpenAI Integration (Optional)
- Add your OpenAI API key for enhanced natural language processing
- Without OpenAI, the system will use fallback response generation

### User Management
- Use `setup_auth.py` to manage user accounts
- Users must be pre-authorized to access the system
- Passwords are securely hashed using bcrypt

## 📁 Project Structure

```
content-effectiveness-engine/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── config.yaml           # Authentication configuration
├── .env.example          # Environment variables template
├── setup_auth.py         # User authentication setup
├── src/
│   ├── __init__.py
│   ├── data_connector.py  # QuickSight data integration
│   ├── analytics_engine.py # Core analytics and statistics
│   └── nlp_processor.py   # Natural language query processing
└── README.md
```

## 🔍 Analytics Capabilities

### Statistical Analysis
- Correlation analysis between content usage and business outcomes
- Statistical significance testing for performance differences
- Segmentation analysis by accreditation status
- Trend analysis over time

### Key Metrics Tracked
- Content discovery success rates
- Deal cycle lengths
- Win rates by seller characteristics
- Time spent on content platforms
- Content gap identification

### Business Insights
- Impact of seller/manager accreditation on performance
- Effectiveness of different content categories
- Identification of high-performing seller profiles
- Content optimization recommendations

## 🛡️ Security Best Practices

1. **Environment Variables**: Never commit .env files to version control
2. **Password Security**: All passwords are hashed using bcrypt
3. **Session Security**: Configurable session timeouts and secure cookies
4. **Access Control**: User-based access restrictions
5. **Data Privacy**: No sensitive data stored in logs or temporary files

## 🚨 Troubleshooting

### Common Issues

**Authentication Problems**:
- Run `python setup_auth.py` to reset user credentials
- Check that usernames and passwords are correctly configured

**Data Loading Issues**:
- Verify AWS credentials in .env file
- Ensure QuickSight dataset IDs are correct
- Check AWS permissions for QuickSight access

**Natural Language Queries Not Working**:
- Verify OpenAI API key in .env file
- Check internet connectivity
- System will fall back to basic responses without OpenAI

### Getting Help
1. Check the application logs in the Streamlit interface
2. Verify all environment variables are properly set
3. Ensure all required Python packages are installed

## 📈 Future Enhancements

- Real-time data streaming from QuickSight
- Advanced machine learning models for predictive analytics
- Integration with additional data sources
- Mobile-responsive interface
- Automated report generation and distribution

## 🤝 Support

For technical support or feature requests, contact the CXA-C team or refer to the internal documentation portal.