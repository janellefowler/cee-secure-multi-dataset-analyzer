# Universal Data Analyzer 📊

A flexible, powerful data analysis tool that can handle any dataset structure and size. Perfect for exploring data with natural language questions.

## 🚀 Features

### 📁 Smart Data Loading
- **Multiple formats**: CSV, Excel (.xlsx/.xls), JSON, Parquet
- **Large file handling**: Automatic chunking and sampling for files with millions of rows
- **Memory optimization**: Intelligent data type optimization to reduce memory usage
- **Flexible parsing**: Handles different encodings, separators, and malformed data

### 💬 Natural Language Queries
- **Ask questions in plain English**: "What's the average sales amount?"
- **Smart suggestions**: Context-aware question recommendations
- **Advanced NLP**: Understands intent and extracts entities from questions
- **Query caching**: Faster responses for repeated questions

### 📊 Comprehensive Analysis
- **Automatic column detection**: Numeric, categorical, date, and text columns
- **Statistical summaries**: Mean, median, correlations, distributions
- **Missing value analysis**: Identify and quantify data gaps
- **Interactive visualizations**: Histograms, scatter plots, correlation heatmaps

### 🔍 Flexible Column Handling
- **Any column names**: Works with any naming convention
- **Semantic understanding**: Infers meaning from column names and data
- **Type inference**: Automatically detects data types and patterns
- **Sample data preview**: Quick overview of data structure

## 🏃‍♂️ Quick Start

### 1. Run the Application
```bash
# Activate virtual environment
source cee-env/bin/activate

# Start the app
streamlit run data_analyzer_app.py --server.port 8506
```

### 2. Upload Your Data
- Click "Choose your data file" in the sidebar
- Supports files up to several GB in size
- For very large files, the app will automatically create a representative sample

### 3. Start Asking Questions
Try these example questions:
- "How many rows are there?"
- "What are the correlations between numeric columns?"
- "Show me the top 10 values in [column_name]"
- "Are there any missing values?"
- "What's the average [column_name]?"

## 📋 Supported Question Types

### Basic Information
- Row/column counts
- Data types and structure
- Missing value analysis
- Column names and summaries

### Statistical Analysis
- Averages, minimums, maximums
- Correlations between variables
- Distributions and ranges
- Unique value counts

### Data Exploration
- Top/bottom values
- Most/least frequent categories
- Comparisons between groups
- Trend analysis over time

### Advanced Queries
- Filtering and segmentation
- Cross-tabulations
- Statistical significance tests
- Pattern recognition

## 🛠️ Technical Architecture

### Core Components

1. **UniversalDataAnalyzer**: Main analysis engine
   - Column type detection
   - Statistical calculations
   - Visualization generation

2. **AdvancedNLPAnalyzer**: Natural language processing
   - Intent classification
   - Entity extraction
   - Query execution
   - Smart suggestions

3. **LargeDatasetHandler**: Big data processing
   - Chunked file reading
   - Memory optimization
   - Sampling strategies
   - Performance monitoring

4. **SmartDataLoader**: Intelligent file loading
   - Format detection
   - Size-based loading strategy
   - Error handling and recovery

### Performance Features

- **Memory optimization**: Automatic data type downcasting
- **Chunked processing**: Handle datasets larger than available RAM
- **Intelligent sampling**: Representative samples from large datasets
- **Query caching**: Avoid recomputing expensive operations
- **Lazy loading**: Load data only when needed

## 📊 Example Use Cases

### Sales Data Analysis
```
Questions you can ask:
- "What's the average deal size by region?"
- "Show me the top 10 sales reps by revenue"
- "How many deals were closed last quarter?"
- "What's the correlation between deal size and sales cycle?"
```

### Customer Analytics
```
Questions you can ask:
- "What are the most common customer segments?"
- "Which products have the highest churn rate?"
- "Show me customer lifetime value distribution"
- "Are there any missing customer contact details?"
```

### Financial Analysis
```
Questions you can ask:
- "What's the monthly revenue trend?"
- "Which expense categories are highest?"
- "Show me profit margins by product line"
- "Are there any anomalies in the transaction data?"
```

## 🔧 Advanced Features

### Large Dataset Handling
- Automatically detects file size and chooses optimal loading strategy
- For files > 100MB: Creates representative samples
- Maintains statistical accuracy while reducing memory usage
- Progress indicators for long-running operations

### Smart Column Mapping
- Recognizes common column patterns (ID, name, date, amount, etc.)
- Handles variations in naming conventions
- Suggests data type corrections
- Identifies potential data quality issues

### Interactive Visualizations
- Automatic chart type selection based on data types
- Correlation heatmaps for numeric data
- Distribution plots and histograms
- Time series analysis for date columns

### Export and Sharing
- Download analysis results
- Export visualizations as images
- Share insights via URL
- Generate automated reports

## 🚀 Getting Started Examples

### Upload Sample Data
The app includes sample sales data to test features:
1. Click "🧪 Load Sample Sales Data" in the sidebar
2. Try asking: "What's the average deal value by region?"
3. Explore the different tabs for visualizations and detailed analysis

### Real Data Analysis
1. Export data from your existing systems (CRM, ERP, etc.)
2. Upload CSV or Excel files
3. Start with basic questions like "How many rows?" 
4. Progress to specific business questions

## 💡 Tips for Best Results

### Question Formatting
- Be specific about column names: "average sales_amount" vs "average amount"
- Use natural language: "Show me the top customers" works better than "SELECT TOP customers"
- Ask follow-up questions to drill down into insights

### Data Preparation
- Clean column names (remove special characters)
- Ensure consistent date formats
- Handle missing values appropriately
- Use descriptive column names when possible

### Performance Optimization
- For very large files, consider pre-filtering data
- Use Parquet format for better performance with large datasets
- Sample data first to test queries before processing full dataset

## 🔍 Troubleshooting

### Common Issues

**File won't load:**
- Check file format is supported (CSV, Excel, JSON, Parquet)
- Ensure file isn't corrupted
- Try with a smaller sample first

**Questions not understood:**
- Use column names exactly as they appear in the data
- Try simpler, more direct questions
- Check the smart suggestions for examples

**Performance issues:**
- Large files are automatically sampled
- Close other browser tabs to free memory
- Consider using Parquet format for better performance

### Error Messages
- "Column not found": Check exact column name spelling
- "Not enough data": File may be too small or empty
- "Memory error": File too large, will automatically sample

## 🎯 Future Enhancements

- **AI-powered insights**: Automatic pattern detection and anomaly identification
- **Advanced visualizations**: Interactive dashboards and custom chart types
- **Data quality scoring**: Automated data quality assessment
- **Integration APIs**: Connect directly to databases and cloud storage
- **Collaborative features**: Share analyses and collaborate on insights
- **Scheduled analysis**: Automated reporting and monitoring

---

**Built with:** Streamlit, Pandas, Plotly, NumPy, and advanced NLP processing

**Perfect for:** Data analysts, business users, researchers, and anyone who needs to quickly understand their data without complex SQL or programming.