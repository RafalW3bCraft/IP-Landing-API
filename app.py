"""
IP-Landing-API with UI - Flask Web Application
Author: RafalW3bCraft
License: MIT License

This project is a Flask-based IP-Landing-API with a cyberpunk-themed UI 
for submitting data to external APIs and displaying responses.
"""

from flask import Flask, render_template, request, jsonify, session
import requests
import psycopg2
import os
from datetime import datetime, timedelta
import json
import re
from dotenv import load_dotenv
from config import Config, DevelopmentConfig, ProductionConfig
from utils import (
    validate_ip_address, is_private_ip, sanitize_user_agent,
    validate_email_format, clean_form_data, detect_bot_user_agent,
    get_country_flag_emoji
)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Flask based on environment
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

API_URL = app.config['EXTERNAL_API_URL']

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Rate limiting function for form submissions
def check_form_submission_rate_limit(ip_address):
    """Check if IP has exceeded form submission rate limit"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        max_submissions = app.config['MAX_FORM_SUBMISSIONS_PER_IP_PER_HOUR']
        cursor.execute("""
            SELECT COUNT(*) FROM visitor_logs 
            WHERE ip_address = %s 
            AND form_data IS NOT NULL 
            AND timestamp > NOW() - INTERVAL '1 hour'
        """, (ip_address,))
        
        result = cursor.fetchone()
        submission_count = result[0] if result else 0
        
        cursor.close()
        conn.close()
        
        return submission_count >= max_submissions
    except Exception as e:
        print(f"Error checking rate limit: {e}")
        return False  # Allow submission if check fails

# Database connection with VS Code compatibility and improved error handling
def get_db_connection():
    try:
        # Try using DATABASE_URL first (Replit/production)
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            return psycopg2.connect(db_url)
        else:
            # Fallback for local development (VS Code)
            conn = psycopg2.connect(
                host=os.environ.get('PGHOST', 'localhost'),
                port=os.environ.get('PGPORT', '5432'),
                database=os.environ.get('PGDATABASE', 'ip_landing_api'),
                user=os.environ.get('PGUSER', 'postgres'),
                password=os.environ.get('PGPASSWORD', '')
            )
            return conn
    except Exception as e:
        error_msg = f"Database connection error: {e}"
        print(error_msg)
        
        # For VS Code development, provide helpful error message
        if "Connection refused" in str(e):
            print("\n" + "="*60)
            print("VS CODE SETUP REQUIRED:")
            print("1. Install PostgreSQL on your system")
            print("2. Create database: CREATE DATABASE ip_landing_api;")
            print("3. Configure .env file with your database credentials")
            print("4. See VS_CODE_SETUP.md for detailed instructions")
            print("="*60 + "\n")
        
        raise

# Function to get client IP address
def get_client_ip(request):
    # Check for X-Forwarded-For header (common in proxy setups)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fallback to remote_addr
    return request.remote_addr

# Function to get location data from IP with improved error handling
def get_location_data(ip_address):
    if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
        # Return local/localhost data structure
        return {
            'country_name': 'Local',
            'country_code': 'LOCAL',
            'city': 'Localhost',
            'region': 'Local',
            'postal': '00000',
            'latitude': 0.0,
            'longitude': 0.0,
            'timezone': 'UTC',
            'currency': 'USD',
            'languages': 'en',
            'org': 'Local Network',
            'asn': 'AS0000',
            'hostname': 'localhost'
        }
    
    try:
        # Using ipapi.co service with the specified format
        response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Check for API rate limiting or error responses
            if 'error' in data:
                print(f"Location API error for {ip_address}: {data.get('reason', 'Unknown')}")
                return None
            return data
        elif response.status_code == 429:
            print(f"Location API rate limited for {ip_address}")
        else:
            print(f"Location API returned status {response.status_code} for {ip_address}")
    except requests.exceptions.Timeout:
        print(f"Location API timeout for {ip_address}")
    except requests.exceptions.RequestException as e:
        print(f"Location API request error for {ip_address}: {e}")
    except Exception as e:
        print(f"Unexpected error getting location data for {ip_address}: {e}")
    return None

# Function to log visitor data with improved error handling and performance
def log_visitor(ip_address, location_data, user_agent, form_data=None):
    if not ip_address:
        print("Warning: Attempted to log visitor without IP address")
        return
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if this IP was already logged recently to avoid spam
        cooldown_minutes = app.config['VISITOR_LOG_COOLDOWN_MINUTES']
        cursor.execute("""
            SELECT COUNT(*) FROM visitor_logs 
            WHERE ip_address = %s AND timestamp > NOW() - INTERVAL '%s minutes'
            AND form_data IS NULL
        """, (ip_address, cooldown_minutes))
        
        result = cursor.fetchone()
        recent_visits = result[0] if result else 0
        
        # Skip logging if this is a duplicate visit without form data
        if recent_visits > 0 and form_data is None:
            cursor.close()
            conn.close()
            return
        
        cursor.execute("""
            INSERT INTO visitor_logs (ip_address, country, country_code, city, region, 
                                    postal_code, latitude, longitude, timezone, calling_code,
                                    currency, languages, asn, org, user_agent, form_data, timestamp,
                                    network, version, country_code_iso3, country_capital, country_tld,
                                    continent_code, in_eu, utc_offset, currency_name, country_area,
                                    country_population, hostname)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ip_address,
            location_data.get('country_name') if location_data else None,
            location_data.get('country_code') if location_data else None,
            location_data.get('city') if location_data else None,
            location_data.get('region') if location_data else None,
            location_data.get('postal') if location_data else None,
            float(location_data.get('latitude')) if location_data and location_data.get('latitude') else None,
            float(location_data.get('longitude')) if location_data and location_data.get('longitude') else None,
            location_data.get('timezone') if location_data else None,
            location_data.get('country_calling_code') if location_data else None,
            location_data.get('currency') if location_data else None,
            location_data.get('languages') if location_data else None,
            location_data.get('asn') if location_data else None,
            location_data.get('org') if location_data else None,
            user_agent[:500] if user_agent else None,  # Truncate very long user agents
            json.dumps(form_data) if form_data else None,
            datetime.now(),
            location_data.get('network') if location_data else None,
            location_data.get('version') if location_data else None,
            location_data.get('country_code_iso3') if location_data else None,
            location_data.get('country_capital') if location_data else None,
            location_data.get('country_tld') if location_data else None,
            location_data.get('continent_code') if location_data else None,
            location_data.get('in_eu') if location_data else None,
            location_data.get('utc_offset') if location_data else None,
            location_data.get('currency_name') if location_data else None,
            int(location_data.get('country_area')) if location_data and location_data.get('country_area') else None,
            int(location_data.get('country_population')) if location_data and location_data.get('country_population') else None,
            location_data.get('hostname') if location_data else None
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as db_error:
        print(f"Database error logging visitor: {db_error}")
    except Exception as e:
        print(f"Error logging visitor: {e}")

# Initialize database tables
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitor_logs (
                id SERIAL PRIMARY KEY,
                ip_address VARCHAR(45),
                country VARCHAR(100),
                country_code VARCHAR(5),
                city VARCHAR(100),
                region VARCHAR(100),
                postal_code VARCHAR(20),
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                timezone VARCHAR(50),
                calling_code VARCHAR(10),
                currency VARCHAR(5),
                languages TEXT,
                asn VARCHAR(20),
                org TEXT,
                user_agent TEXT,
                form_data JSONB,
                timestamp TIMESTAMP,
                network VARCHAR(100),
                version VARCHAR(10),
                country_code_iso3 VARCHAR(3),
                country_capital VARCHAR(100),
                country_tld VARCHAR(10),
                continent_code VARCHAR(2),
                in_eu BOOLEAN,
                utc_offset VARCHAR(10),
                currency_name VARCHAR(50),
                country_area BIGINT,
                country_population BIGINT,
                hostname VARCHAR(255)
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Initialize database on startup (only if database connection works)
try:
    init_db()
except Exception as e:
    print(f"Failed to initialize database: {e}")
    print("Application will continue but database features may not work")

@app.route('/')
def home():
    # Track visitor on page load
    ip_address = get_client_ip(request)
    user_agent = request.headers.get('User-Agent', '')
    location_data = get_location_data(ip_address)
    
    # Log the visit
    log_visitor(ip_address, location_data, user_agent)
    
    return render_template('index.html')

@app.route('/api/get', methods=['GET'])
def get_api():
    try:
        response = requests.get("https://jsonplaceholder.typicode.com/posts/1", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": f"External API returned status {response.status_code}"}), response.status_code
    except requests.exceptions.Timeout:
        return jsonify({"error": "External API request timed out"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"External API request failed: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/post', methods=['POST'])
def post_api():
    try:
        # Get data from request (form or JSON)
        if request.is_json:
            data = request.get_json()
        else:
            data = dict(request.form)
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Send to external API with timeout
        response = requests.post(API_URL, json=data, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": f"External API returned status {response.status_code}"}), response.status_code
    
    except requests.exceptions.Timeout:
        return jsonify({"error": "External API request timed out"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"External API request failed: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/submit', methods=['POST'])
def submit():
    # Get form data with validation
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()
    
    # Track visitor with form submission
    ip_address = get_client_ip(request)
    
    # Rate limiting check
    if check_form_submission_rate_limit(ip_address):
        return render_template(
            "index.html",
            errors=["Too many form submissions. Please try again later."],
            form_data={"name": name, "email": email, "message": message}
        ), 429
    
    # Enhanced input validation with config values
    errors = []
    
    # Validate name
    if not name or len(name) < app.config['MIN_NAME_LENGTH']:
        errors.append(f"Name must be at least {app.config['MIN_NAME_LENGTH']} characters long")
    elif len(name) > app.config['MAX_NAME_LENGTH']:
        errors.append(f"Name must be less than {app.config['MAX_NAME_LENGTH']} characters")
    elif not name.replace(' ', '').replace('-', '').replace("'", '').replace('.', '').isalpha():
        errors.append("Name contains invalid characters")
    
    # Enhanced email validation using utility function
    if not email:
        errors.append("Email address is required")
    elif not validate_email_format(email):
        errors.append("Please provide a valid email address")
    elif len(email) > app.config['MAX_EMAIL_LENGTH']:
        errors.append(f"Email must be less than {app.config['MAX_EMAIL_LENGTH']} characters")
    
    # Validate message
    if message and len(message) > app.config['MAX_MESSAGE_LENGTH']:
        errors.append(f"Message must be less than {app.config['MAX_MESSAGE_LENGTH']} characters")
    
    # Enhanced spam detection
    spam_keywords = ['click here', 'buy now', 'free money', 'win now', 'urgent', 'limited time', 'act now']
    combined_text = (name + ' ' + email + ' ' + message).lower()
    if any(keyword in combined_text for keyword in spam_keywords):
        errors.append("Message contains suspicious content")
    
    # Check for repeated characters (potential spam)
    if any(char * 5 in combined_text for char in 'abcdefghijklmnopqrstuvwxyz0123456789'):
        errors.append("Message contains suspicious patterns")
    
    if errors:
        return render_template(
            "index.html",
            errors=errors,
            form_data={"name": name, "email": email, "message": message}
        ), 400

    # Get additional tracking data with validation
    user_agent = sanitize_user_agent(request.headers.get('User-Agent', ''))
    location_data = get_location_data(ip_address)
    form_data = clean_form_data({"name": name, "email": email, "message": message})
    
    # Add bot detection flag
    is_bot = detect_bot_user_agent(user_agent)
    if is_bot:
        form_data["bot_detected"] = True
    
    # Log the form submission
    log_visitor(ip_address, location_data, user_agent, form_data)

    # Send data to an external API with enhanced error handling
    payload = {"name": name, "email": email, "message": message, "ip": ip_address, "timestamp": datetime.now().isoformat()}
    try:
        api_response = requests.post(API_URL, json=payload, timeout=app.config['LOCATION_API_TIMEOUT'])
        if api_response.status_code == 200:
            api_data = api_response.json()
        else:
            api_data = {"error": f"External API returned status {api_response.status_code}", "status_code": api_response.status_code}
    except requests.exceptions.Timeout:
        api_data = {"error": "External API request timed out", "timeout": True}
    except requests.exceptions.ConnectionError:
        api_data = {"error": "Failed to connect to external API", "connection_error": True}
    except requests.exceptions.RequestException as e:
        api_data = {"error": f"External API request failed: {str(e)}", "request_error": True}
    except Exception as e:
        api_data = {"error": f"Unexpected error: {str(e)}", "unexpected": True}

    return render_template(
        "index.html",
        api_response=api_data,
        submitted_data=payload,
        success_message="Form submitted successfully!"
    )

# Admin route to view visitor logs
@app.route('/admin/visitors')
def admin_visitors():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 100)  # Maximum 100 per page
    offset = (page - 1) * per_page
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM visitor_logs WHERE city IS NOT NULL AND country IS NOT NULL")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT id, ip_address, country, country_code, city, region, postal_code,
                   latitude, longitude, timezone, calling_code, currency, languages,
                   asn, org, user_agent, form_data, timestamp, network, version,
                   country_code_iso3, country_capital, country_tld, continent_code,
                   in_eu, utc_offset, currency_name, country_area, country_population, hostname
            FROM visitor_logs 
            WHERE city IS NOT NULL AND country IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        visitors = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert to list of dictionaries for easier template rendering
        visitor_list = []
        for visitor in visitors:
            visitor_list.append({
                'id': visitor[0],
                'ip_address': visitor[1],
                'country': visitor[2],
                'country_code': visitor[3],
                'city': visitor[4],
                'region': visitor[5],
                'postal_code': visitor[6],
                'latitude': visitor[7],
                'longitude': visitor[8],
                'timezone': visitor[9],
                'calling_code': visitor[10],
                'currency': visitor[11],
                'languages': visitor[12],
                'asn': visitor[13],
                'org': visitor[14],
                'user_agent': visitor[15],
                'form_data': visitor[16],
                'timestamp': visitor[17],
                'network': visitor[18],
                'version': visitor[19],
                'country_code_iso3': visitor[20],
                'country_capital': visitor[21],
                'country_tld': visitor[22],
                'continent_code': visitor[23],
                'in_eu': visitor[24],
                'utc_offset': visitor[25],
                'currency_name': visitor[26],
                'country_area': visitor[27],
                'country_population': visitor[28],
                'hostname': visitor[29]
            })
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'pages': (total_count + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': page < (total_count + per_page - 1) // per_page
        }
        
        return render_template('admin_visitors.html', visitors=visitor_list, pagination=pagination)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API route to get visitor stats
@app.route('/api/visitor-stats')
def visitor_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total visitors
        cursor.execute("SELECT COUNT(*) FROM visitor_logs")
        total_result = cursor.fetchone()
        total_visitors = total_result[0] if total_result else 0
        
        # Get unique visitors
        cursor.execute("SELECT COUNT(DISTINCT ip_address) FROM visitor_logs")
        unique_result = cursor.fetchone()
        unique_visitors = unique_result[0] if unique_result else 0
        
        # Get top countries
        cursor.execute("""
            SELECT country, COUNT(*) as count 
            FROM visitor_logs 
            WHERE country IS NOT NULL 
            GROUP BY country 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_countries = cursor.fetchall()
        
        # Get form submissions
        cursor.execute("SELECT COUNT(*) FROM visitor_logs WHERE form_data IS NOT NULL")
        form_result = cursor.fetchone()
        form_submissions = form_result[0] if form_result else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total_visitors': total_visitors,
            'unique_visitors': unique_visitors,
            'form_submissions': form_submissions,
            'top_countries': [{'country': c[0], 'count': c[1]} for c in top_countries]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to view detailed visitor information
@app.route('/admin/visitor/<int:visitor_id>')
def visitor_detail(visitor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, ip_address, country, country_code, city, region, postal_code,
                   latitude, longitude, timezone, calling_code, currency, languages,
                   asn, org, user_agent, form_data, timestamp, network, version,
                   country_code_iso3, country_capital, country_tld, continent_code,
                   in_eu, utc_offset, currency_name, country_area, country_population, hostname
            FROM visitor_logs WHERE id = %s
        """, (visitor_id,))
        
        visitor = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not visitor:
            return "Visitor not found", 404
            
        # Convert to dictionary for template
        visitor_data = {
            'id': visitor[0],
            'ip_address': visitor[1],
            'country': visitor[2],
            'country_code': visitor[3],
            'city': visitor[4],
            'region': visitor[5],
            'postal_code': visitor[6],
            'latitude': visitor[7],
            'longitude': visitor[8],
            'timezone': visitor[9],
            'calling_code': visitor[10],
            'currency': visitor[11],
            'languages': visitor[12],
            'asn': visitor[13],
            'org': visitor[14],
            'user_agent': visitor[15],
            'form_data': visitor[16],
            'timestamp': visitor[17],
            'network': visitor[18],
            'version': visitor[19],
            'country_code_iso3': visitor[20],
            'country_capital': visitor[21],
            'country_tld': visitor[22],
            'continent_code': visitor[23],
            'in_eu': visitor[24],
            'utc_offset': visitor[25],
            'currency_name': visitor[26],
            'country_area': visitor[27],
            'country_population': visitor[28],
            'hostname': visitor[29]
        }
        
        return render_template('visitor_detail.html', visitor=visitor_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to refresh location data for existing visitors
@app.route('/admin/refresh-locations')
def refresh_locations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get visitors without location data
        cursor.execute("""
            SELECT id, ip_address FROM visitor_logs 
            WHERE (country IS NULL OR country = '') 
            AND ip_address != '127.0.0.1'
            LIMIT 20
        """)
        
        visitors_to_update = cursor.fetchall()
        updated_count = 0
        
        for visitor_id, ip_address in visitors_to_update:
            location_data = get_location_data(ip_address)
            if location_data:
                cursor.execute("""
                    UPDATE visitor_logs SET 
                        country = %s, country_code = %s, city = %s, region = %s,
                        postal_code = %s, latitude = %s, longitude = %s, timezone = %s,
                        calling_code = %s, currency = %s, languages = %s, asn = %s, org = %s,
                        network = %s, version = %s, country_code_iso3 = %s, country_capital = %s,
                        country_tld = %s, continent_code = %s, in_eu = %s, utc_offset = %s,
                        currency_name = %s, country_area = %s, country_population = %s, hostname = %s
                    WHERE id = %s
                """, (
                    location_data.get('country_name'),
                    location_data.get('country_code'),
                    location_data.get('city'),
                    location_data.get('region'),
                    location_data.get('postal'),
                    location_data.get('latitude'),
                    location_data.get('longitude'),
                    location_data.get('timezone'),
                    location_data.get('country_calling_code'),
                    location_data.get('currency'),
                    location_data.get('languages'),
                    location_data.get('asn'),
                    location_data.get('org'),
                    location_data.get('network'),
                    location_data.get('version'),
                    location_data.get('country_code_iso3'),
                    location_data.get('country_capital'),
                    location_data.get('country_tld'),
                    location_data.get('continent_code'),
                    location_data.get('in_eu'),
                    location_data.get('utc_offset'),
                    location_data.get('currency_name'),
                    location_data.get('country_area'),
                    location_data.get('country_population'),
                    location_data.get('hostname'),
                    visitor_id
                ))
                updated_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': f'Successfully updated location data for {updated_count} visitors',
            'updated_count': updated_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Additional security and performance routes
@app.route('/robots.txt')
def robots_txt():
    return """User-agent: *
Disallow: /admin/
Disallow: /api/
Allow: /
""", 200, {'Content-Type': 'text/plain'}

@app.route('/health')
def health_check():
    """Comprehensive health check endpoint for monitoring"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Database connectivity check
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) FROM visitor_logs")
        total_logs = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        health_data["checks"]["database"] = {"status": "healthy", "total_logs": total_logs}
    except Exception as e:
        health_data["status"] = "unhealthy"
        health_data["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
    
    # External API connectivity check
    try:
        response = requests.get("https://httpbin.org/status/200", timeout=5)
        if response.status_code == 200:
            health_data["checks"]["external_api"] = {"status": "healthy"}
        else:
            health_data["checks"]["external_api"] = {"status": "degraded", "status_code": response.status_code}
    except Exception as e:
        health_data["checks"]["external_api"] = {"status": "unhealthy", "error": str(e)}
    
    # Location API check
    try:
        response = requests.get("https://ipapi.co/json/", timeout=5)
        if response.status_code == 200:
            health_data["checks"]["location_api"] = {"status": "healthy"}
        else:
            health_data["checks"]["location_api"] = {"status": "degraded", "status_code": response.status_code}
    except Exception as e:
        health_data["checks"]["location_api"] = {"status": "unhealthy", "error": str(e)}
    
    status_code = 200 if health_data["status"] == "healthy" else 503
    return jsonify(health_data), status_code

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429

# Database maintenance routes
@app.route('/admin/stats/daily')
def daily_stats():
    """Get daily visitor statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT visit_date, total_visits, unique_visitors, form_submissions, with_location
            FROM visitor_summary
            ORDER BY visit_date DESC
            LIMIT 30
        """)
        
        stats = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            "daily_stats": [
                {
                    "date": stat[0].isoformat() if stat[0] else None,
                    "total_visits": stat[1],
                    "unique_visitors": stat[2], 
                    "form_submissions": stat[3],
                    "with_location": stat[4]
                } for stat in stats
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/cleanup/old-visits')
def cleanup_old_visits():
    """Clean up visits older than 90 days (keep form submissions)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM visitor_logs 
            WHERE timestamp < NOW() - INTERVAL '90 days'
            AND form_data IS NULL
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": f"Cleaned up {deleted_count} old visitor logs",
            "deleted_count": deleted_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
