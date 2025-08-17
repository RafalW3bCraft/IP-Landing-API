# IP-Landing-API

> **Enterprise-grade Flask web application for advanced IP tracking and visitor analytics**

A cutting-edge web application that captures visitor data in real-time, providing comprehensive geolocation insights while maintaining security and compliance standards. Features a cyberpunk-themed UI with dark interface and green accents, offering both public form submission capabilities and an administrative analytics dashboard.

![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

## ✨ Features

### 🔍 Advanced IP Tracking
- **Real-time geolocation** - Capture 29+ fields of location data per visitor
- **Intelligent IP detection** - Handles proxy headers and forwarded IPs
- **Fallback mechanisms** - Graceful degradation when APIs are rate-limited
- **Local development support** - Works on localhost with intelligent fallbacks

### 📊 Visitor Analytics Dashboard
- **Comprehensive visitor logs** - Track every visitor with detailed metadata
- **Location-based insights** - Geographic distribution of visitors
- **Real-time statistics** - Live visitor counts and form submissions
- **Searchable admin interface** - Filter and explore visitor data

### 🛡️ Enterprise Security
- **Rate limiting** - 10 submissions per hour per IP address
- **Bot detection** - Intelligent user agent analysis
- **Input validation** - Multi-layer form and data validation
- **Security headers** - X-Frame-Options, CSP, XSS protection
- **Session management** - Secure HTTP-only cookies

### 🚀 Performance & Reliability
- **Health monitoring** - Multi-service health checks
- **Error handling** - Comprehensive error management with logging
- **Database optimization** - Indexed queries and pagination
- **API resilience** - Timeout handling and connection pooling

## 🛠️ Technology Stack

- **Backend**: Flask 3.1.0 (Python)
- **Database**: PostgreSQL with psycopg2
- **Frontend**: HTML5/CSS3 with Jinja2 templating
- **APIs**: ipapi.co for geolocation, httpbin.org for testing
- **Security**: Custom validation utilities and security headers

## 📦 Quick Start

### For Local Development (VS Code)

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd ip-landing-api
   ```

2. **Install PostgreSQL**:
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql && brew services start postgresql
   
   # Windows - Download from postgresql.org
   ```

3. **Create database**:
   ```sql
   sudo -u postgres psql
   CREATE DATABASE ip_landing_api;
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE ip_landing_api TO your_username;
   \q
   ```

4. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

6. **Run the application**:
   ```bash
   python app.py
   ```

7. **Visit** `http://localhost:5000`

> 📖 **Detailed Setup Guide**: See `VS_CODE_SETUP.md` for comprehensive local development instructions.

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/ip_landing_api
PGHOST=localhost
PGPORT=5432
PGDATABASE=ip_landing_api
PGUSER=your_username
PGPASSWORD=your_password

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-change-in-production

# API Configuration
EXTERNAL_API_URL=http://httpbin.org/post
LOCATION_API_TIMEOUT=10

# Rate Limiting
VISITOR_LOG_COOLDOWN_MINUTES=5
MAX_FORM_SUBMISSIONS_PER_IP_PER_HOUR=10

# Performance
MAX_VISITOR_LOGS_DISPLAY=100
```

## 📊 API Endpoints

### Public Endpoints

- `GET /` - Main landing page with form
- `POST /submit` - Form submission endpoint
- `GET /health` - Application health check
- `GET /robots.txt` - Search engine directives

### Admin Endpoints

- `GET /admin/visitors` - Visitor analytics dashboard
- `GET /admin/visitor/<id>` - Individual visitor details
- `GET /api/visitor-stats` - JSON visitor statistics

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2025-08-17T10:26:26.788335",
  "checks": {
    "database": {
      "status": "healthy",
      "total_logs": 16
    },
    "external_api": {
      "status": "healthy"
    },
    "location_api": {
      "status": "degraded",
      "status_code": 429
    }
  }
}
```

## 📊 Database Schema

The application creates the following table structure:

```sql
CREATE TABLE visitor_logs (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    country VARCHAR(100),
    country_code VARCHAR(5),
    city VARCHAR(100),
    region VARCHAR(100),
    postal_code VARCHAR(20),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    timezone VARCHAR(50),
    calling_code VARCHAR(10),
    currency VARCHAR(10),
    languages VARCHAR(100),
    asn VARCHAR(20),
    org VARCHAR(200),
    user_agent TEXT,
    form_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Additional location fields...
);
```

## 🔍 Monitoring & Analytics

### Visitor Statistics

- **Total Visits**: Count of all page visits
- **Unique Visitors**: Distinct IP addresses
- **Form Submissions**: Successful form completions
- **Geographic Distribution**: Visitor locations on world map
- **Real-time Activity**: Live visitor tracking

### Health Monitoring

The application continuously monitors:

- Database connectivity and performance
- External API availability
- Location service status
- Error rates and response times

## 🛠️ Development

### Project Structure

```
ip-landing-api/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── utils.py              # Utility functions
├── logging_config.py     # Logging configuration
├── requirements.txt      # Python dependencies
├── static/
│   └── style.css        # Cyberpunk-themed styles
├── templates/
│   ├── index.html       # Main landing page
│   ├── admin_visitors.html  # Admin dashboard
│   └── visitor_detail.html # Individual visitor view
├── .env.example         # Environment template
├── VS_CODE_SETUP.md     # Local development guide
└── README.md           # This file
```

### Key Components

- **Flask Application** (`app.py`): Main web server with routing
- **Configuration** (`config.py`): Environment-based settings
- **Utilities** (`utils.py`): IP validation, data cleaning, bot detection
- **Database Layer**: PostgreSQL with intelligent connection handling
- **Security Layer**: Rate limiting, validation, and headers


### Manual Deployment

For production deployments on other platforms:

1. **Set up PostgreSQL** database
2. **Configure environment** variables for production
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Use WSGI server**: gunicorn, uWSGI, or similar
5. **Set up reverse proxy**: nginx or Apache
6. **Enable HTTPS**: SSL/TLS certificates

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors**:
- Ensure PostgreSQL is running
- Check DATABASE_URL format
- Verify database credentials

**Location API Rate Limiting**:
- Application handles this gracefully
- Uses fallback data for localhost
- Continues tracking without location data

**Form Submission Errors**:
- Check rate limiting (10 per hour per IP)
- Verify form validation requirements
- Review bot detection logs

### Debug Mode

Enable detailed logging:

```bash
export FLASK_DEBUG=1
export FLASK_ENV=development
python app.py
```

### Health Checks

Monitor application status:
- Visit `/health` for system status
- Check logs for error details
- Use admin dashboard for visitor insights

## 📈 Performance

### Optimization Features

- **Database Indexing**: Optimized queries for visitor logs
- **Pagination**: Efficient handling of large datasets
- **Connection Pooling**: Database connection management
- **Caching**: Strategic caching of location data
- **Rate Limiting**: Prevents resource abuse

### Scalability

The application is designed for:
- **Concurrent Users**: Handles multiple simultaneous visitors
- **Large Datasets**: Efficient pagination and querying
- **API Resilience**: Graceful handling of external API failures
- **Resource Management**: Intelligent connection and memory management

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review the VS Code setup guide
3. Examine the health check endpoint
4. Check application logs for errors


---

**Made by RafalW3bCraft**