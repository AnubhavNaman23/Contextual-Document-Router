# 🚀 Quick Start Guide

## Contextual Document Router v2.0

Welcome to the Contextual Document Router! This guide will help you get started quickly.

---

## 📋 Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- 4GB RAM minimum
- 2GB free disk space

## ⚡ Quick Installation

### Option 1: Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd contextual-document-router

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the application
# API: http://localhost:8000
# Web UI: http://localhost:3000
```

---

## 🎯 Quick Usage

### 1. Start the API Server

```bash
python api.py
```

The API will be available at `http://localhost:8000`

### 2. Start the Web UI

```bash
streamlit run app_ui.py
```

The Web UI will open automatically in your browser.

### 3. Process a Document (CLI)

```bash
python main.py --input_file sample_email.txt
```

### 4. Process via API

```bash
curl -X POST "http://localhost:8000/classify" \
  -F "file=@your_document.pdf"
```

---

## 📁 Project Structure

```
.
├── main.py              # Main application entry point
├── api.py               # FastAPI REST API
├── app_ui.py            # Enhanced Streamlit Web UI
├── classifier.py        # Intent classification engine
├── email_parser.py      # Email processing logic
├── format_detector.py   # Format detection
├── config.py            # Configuration management
├── logger.py            # Advanced logging system
├── analytics.py         # Analytics and reporting
├── monitoring.py        # System monitoring
├── database.py          # Database integration
├── test_suite.py        # Comprehensive tests
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container config
└── docker-compose.yml   # Docker Compose setup
```

---

## 🎨 Features

### ✅ Document Processing
- Email (.txt, .eml)
- JSON (.json)
- PDF (.pdf)

### ✅ Classification Categories
- 📢 Complaint
- 💰 Invoice
- 📋 Regulation
- ⚠️ Fraud Risk
- 💼 RFQ (Request for Quotation)

### ✅ System Features
- Real-time processing
- Advanced analytics
- System monitoring
- Error tracking
- Audit logging
- Database persistence

---

## 🧪 Running Tests

```bash
# Run all tests
python test_suite.py

# Run with pytest
pytest test_suite.py -v

# Run with coverage
pytest test_suite.py --cov=. --cov-report=html
```

---

## 📊 Viewing Analytics

### Generate Analytics Report

```python
from analytics import AnalyticsEngine, ReportGenerator

# Create engine
engine = AnalyticsEngine()

# Generate report
report = engine.generate_report(output_format='json')
print(report)

# Export to CSV
engine.export_to_csv('analytics_export.csv')
```

### View in Web UI

1. Start the Web UI: `streamlit run app_ui.py`
2. Navigate to the Dashboard tab
3. View real-time statistics and charts

---

## 🔧 Configuration

Edit `config.json` to customize system behavior:

```json
{
  "api_port": 8000,
  "max_upload_size": 10485760,
  "confidence_threshold": 0.7,
  "log_level": "INFO",
  "enable_metrics": true
}
```

Or use environment variables:

```bash
export API_PORT=8000
export LOG_LEVEL=DEBUG
export DEBUG=true
```

---

## 📈 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### View Metrics

```bash
curl http://localhost:8000/metrics
```

### Prometheus Integration

Metrics are available in Prometheus format at:
`http://localhost:9090/metrics`

---

## 🐛 Troubleshooting

### Issue: Port already in use

```bash
# Change port in config.json or use environment variable
export API_PORT=8001
python api.py
```

### Issue: Module not found

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Permission denied on uploads

```bash
# Create uploads directory with correct permissions
mkdir uploads
chmod 755 uploads
```

---

## 📝 Example Documents

Sample documents are included in the `sample_data.json` and `sample_email.txt` files.

### Process Sample Email

```bash
python main.py --input_file sample_email.txt
```

### Process Sample JSON

```bash
python main.py --input_file sample_data.json
```

---

## 🔐 Security Notes

- API key authentication is disabled by default
- Enable in production by setting `enable_auth: true` in config
- Use environment variables for sensitive data
- Never commit credentials to version control

---

## 🤝 Getting Help

- Check the full README.md for detailed documentation
- Review error logs in `logs/app.log`
- Check system metrics for performance issues
- Run tests to verify installation

---

## 🎓 Next Steps

1. ✅ Complete the Quick Start above
2. 📚 Read the full [README.md](README.md)
3. 🧪 Run the test suite
4. 🎨 Explore the Web UI
5. 📊 View analytics and reports
6. 🔧 Customize configuration
7. 🚀 Deploy to production

---

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the logs

---

**Happy Processing! 🎉**
