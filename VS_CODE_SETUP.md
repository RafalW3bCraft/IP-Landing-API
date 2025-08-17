# VS Code Local Development Setup

Complete guide for running IP-Landing-API on your local machine with Visual Studio Code.

## Prerequisites

### Required Software

1. **Python 3.11+**
   ```bash
   # Check version
   python --version
   
   # Install Python from python.org if needed
   ```

2. **PostgreSQL Database**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   brew services start postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

3. **Git** (for cloning)
   ```bash
   git --version
   ```

## Step 1: Clone and Setup Project

```bash
# Clone the repository
git clone <your-repo-url>
cd ip-landing-api

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: PostgreSQL Database Setup

### Option A: Local PostgreSQL Installation

1. **Start PostgreSQL service**:
   ```bash
   # Ubuntu/Debian
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   
   # macOS
   brew services start postgresql
   
   # Windows
   # Use pgAdmin or Services panel
   ```

2. **Create database and user**:
   ```bash
   # Connect to PostgreSQL as postgres user
   sudo -u postgres psql
   
   # In PostgreSQL shell:
   CREATE DATABASE ip_landing_api;
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE ip_landing_api TO your_username;
   \q
   ```

### Option B: Docker PostgreSQL (Alternative)

```bash
# Run PostgreSQL in Docker
docker run --name postgres-ip-landing \
  -e POSTGRES_DB=ip_landing_api \
  -e POSTGRES_USER=your_username \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -d postgres:15

# Check if running
docker ps
```

## Step 3: Environment Configuration

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file** with your settings:
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://your_username:your_password@localhost:5432/ip_landing_api
   PGHOST=localhost
   PGPORT=5432
   PGDATABASE=ip_landing_api
   PGUSER=your_username
   PGPASSWORD=your_password
   
   # Flask Configuration
   FLASK_ENV=development
   FLASK_DEBUG=1
   SECRET_KEY=your-development-secret-key
   
   # API Configuration
   EXTERNAL_API_URL=http://httpbin.org/post
   LOCATION_API_TIMEOUT=10
   
   # Rate Limiting
   VISITOR_LOG_COOLDOWN_MINUTES=5
   MAX_FORM_SUBMISSIONS_PER_IP_PER_HOUR=10
   
   # Performance
   MAX_VISITOR_LOGS_DISPLAY=100
   ```

## Step 4: VS Code Configuration

### Recommended Extensions

Install these VS Code extensions:

1. **Python** (ms-python.python)
2. **Python Debugger** (ms-python.debugpy)
3. **PostgreSQL** (ms-ossdata.vscode-postgresql)
4. **Thunder Client** (rangav.vscode-thunder-client) - for API testing
5. **Better Comments** (aaron-bond.better-comments)

### VS Code Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "files.associations": {
        "*.html": "html"
    },
    "emmet.includeLanguages": {
        "jinja-html": "html"
    }
}
```

### Debug Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask App",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/app.py",
            "env": {
                "FLASK_ENV": "development",
                "FLASK_DEBUG": "1"
            },
            "args": [],
            "jinja": true,
            "console": "integratedTerminal"
        }
    ]
}
```

## Step 5: Run the Application

### Method 1: Command Line

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the Flask application
python app.py
```

### Method 2: VS Code Debugger

1. Open VS Code
2. Press `F5` or go to Run → Start Debugging
3. Select "Flask App" configuration
4. Application will start with debugger attached

### Method 3: VS Code Terminal

1. Open VS Code terminal (`Ctrl+``)
2. Ensure virtual environment is activated
3. Run: `python app.py`

## Step 6: Verify Installation

### Access the Application

1. **Main Application**: http://localhost:5000
2. **Health Check**: http://localhost:5000/health
3. **Admin Dashboard**: http://localhost:5000/admin/visitors
4. **API Stats**: http://localhost:5000/api/visitor-stats

### Test Database Connection

```bash
# Test database connectivity
python -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### Test Location API

```bash
# Test external API connectivity
curl -s "https://ipapi.co/8.8.8.8/json/" | head -5
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

**Error**: `connection to server at "localhost", port 5432 failed`

**Solutions**:
1. Check if PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql  # Linux
   brew services list | grep postgres  # macOS
   ```

2. Verify database exists:
   ```bash
   sudo -u postgres psql -l
   ```

3. Check connection parameters in `.env`

#### Permission Denied Errors

**Error**: `FATAL: password authentication failed`

**Solutions**:
1. Verify username/password in `.env`
2. Check PostgreSQL user exists:
   ```bash
   sudo -u postgres psql -c "\du"
   ```

#### Python Virtual Environment Issues

**Error**: `Module not found` or import errors

**Solutions**:
1. Ensure virtual environment is activated:
   ```bash
   which python  # Should point to venv/bin/python
   ```

2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Location API Rate Limiting

**Expected Behavior**: Application handles this gracefully
- Uses fallback data for localhost
- Continues tracking without location data
- Shows degraded status in health check

### Debug Mode

Enable detailed logging:

```bash
export FLASK_DEBUG=1
export FLASK_ENV=development
python app.py
```

### Performance Optimization

For better development experience:

1. **Database Indexing**: Automatically created on first run
2. **Debug Toolbar**: Available in development mode
3. **Auto-reload**: Flask watches for file changes
4. **Error Pages**: Detailed error information in debug mode

## Development Workflow

### Recommended Workflow

1. **Start PostgreSQL**
2. **Activate virtual environment**
3. **Start Flask app** with debugger
4. **Make changes** to code
5. **Test changes** automatically reload
6. **Use health endpoint** to monitor status

### Testing

Run the comprehensive test suite:

```bash
# Basic connectivity test
curl http://localhost:5000/health

# Form submission test
curl -X POST http://localhost:5000/submit \
  -d "name=Test User&email=test@example.com&message=Testing local setup"

# Admin dashboard test
curl http://localhost:5000/admin/visitors
```

### Database Management

Connect to your local database:

```bash
# Command line
psql postgresql://your_username:your_password@localhost:5432/ip_landing_api

# Or using VS Code PostgreSQL extension
# Add connection with your credentials
```

## Production Considerations

When moving to production:

1. **Change SECRET_KEY** to a secure random value
2. **Set FLASK_DEBUG=0**
3. **Use production WSGI server** (gunicorn, uWSGI)
4. **Configure reverse proxy** (nginx, Apache)
5. **Enable HTTPS** and set SESSION_COOKIE_SECURE=true
6. **Set up monitoring** and logging
7. **Configure backup** for PostgreSQL

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Verify all prerequisites are installed
3. Check application logs for error details
4. Test database connectivity independently
5. Ensure all environment variables are set correctly

The application includes comprehensive error handling and will provide helpful error messages for common setup issues.