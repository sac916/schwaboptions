# Deployment Guide - SchwaOptions Analytics

## 🚀 **Quick Start Deployment**

### **Phase 3 Setup with Historical Data Collection**
```bash
# 1. Clone and navigate to project
cd /home/gmitch/schwaboptions

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API credentials
cp .env.sample .env
# Edit .env with your Schwab API credentials
nano .env

# 5. PHASE 3: Setup historical data collection
# Create historical data directories
mkdir -p data/historical/daily_options_snapshots
mkdir -p data/historical/unusual_activity
mkdir -p data/historical/market_summary

# 6. PHASE 3: Start daily data collection (recommended)
python collect_daily_data.py

# 7. Run application with integrated authentication
python dash_app.py

# 8. Open browser and authenticate
# Navigate to: http://127.0.0.1:8051
# Click "Login" when prompted for seamless OAuth
```

---

## 🏗️ **Production Deployment Options**

### **Option 1: Cloud Deployment (Recommended)**

#### **Heroku Deployment**
```bash
# 1. Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# 2. Login and create app
heroku login
heroku create schwab-options-analytics

# 3. Configure environment variables
heroku config:set API_KEY=your_schwab_api_key
heroku config:set API_SECRET=your_schwab_api_secret

# 4. Create Procfile
echo "web: python dash_app.py" > Procfile

# 5. Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# 6. Open application
heroku open
```

#### **DigitalOcean App Platform**
```yaml
# app.yaml
name: schwab-options-analytics
services:
- name: web
  source_dir: /
  github:
    repo: your-username/schwab-options-analytics
    branch: main
  run_command: python dash_app.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: API_KEY
    value: your_schwab_api_key
    type: SECRET
  - key: API_SECRET  
    value: your_schwab_api_secret
    type: SECRET
```

#### **AWS EC2 Deployment**
```bash
# 1. Launch EC2 instance (t3.medium recommended)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# 4. Clone repository
git clone https://github.com/your-username/schwab-options-analytics.git
cd schwab-options-analytics

# 5. Setup application
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Configure environment
nano .env
# Add your API credentials

# 7. Create systemd service
sudo nano /etc/systemd/system/schwab-options.service

# 8. Configure nginx reverse proxy
sudo nano /etc/nginx/sites-available/schwab-options

# 9. Start services
sudo systemctl enable schwab-options
sudo systemctl start schwab-options
sudo systemctl restart nginx
```

### **Option 2: Docker Deployment**

#### **Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8051

# Set environment variables
ENV PYTHONPATH=/app

# Run application
CMD ["python", "dash_app.py"]
```

#### **Phase 3 Docker Compose**
```yaml
version: '3.8'
services:
  schwab-options:
    build: .
    ports:
      - "8051:8051"
    environment:
      - API_KEY=${API_KEY}
      - API_SECRET=${API_SECRET}
      - HISTORICAL_DATA_PATH=/app/data/historical
      - DAILY_COLLECTION_ENABLED=true
    volumes:
      - ./logs:/app/logs
      - ./data/historical:/app/data/historical  # Phase 3: Historical data persistence
      - schwab_tokens:/app/.tokens  # Phase 3: Token storage
    restart: unless-stopped

  # Phase 3: Data collection service
  data-collector:
    build: .
    environment:
      - API_KEY=${API_KEY}
      - API_SECRET=${API_SECRET}
      - HISTORICAL_DATA_PATH=/app/data/historical
    volumes:
      - ./data/historical:/app/data/historical
      - schwab_tokens:/app/.tokens
    command: python collect_daily_data.py
    depends_on:
      - schwab-options
    restart: "no"  # Run once daily via cron or scheduler

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
  schwab_tokens:  # Phase 3: Persistent token storage
```

#### **Deploy with Docker**
```bash
# 1. Build image
docker build -t schwab-options-analytics .

# 2. Run container
docker run -d \
  --name schwab-options \
  -p 8051:8051 \
  -e API_KEY=your_api_key \
  -e API_SECRET=your_api_secret \
  schwab-options-analytics

# 3. Or use docker-compose
docker-compose up -d
```

---

## ⚙️ **Configuration Management**

### **Environment Variables**
```bash
# Required API Credentials
API_KEY=your_schwab_api_key
API_SECRET=your_schwab_api_secret

# Optional Application Settings
APP_HOST=0.0.0.0                    # Host interface
APP_PORT=8051                       # Application port
DEBUG_MODE=False                    # Debug mode (False for production)

# Phase 3: Historical Data Settings
HISTORICAL_DATA_PATH=./data/historical  # Historical data storage path
DAILY_COLLECTION_ENABLED=True            # Enable automated daily collection
DAILY_COLLECTION_TIME=16:30             # Collection time (after market close)
DATA_RETENTION_DAYS=365                 # Days to retain historical data

# Optional Performance Settings
CACHE_TIMEOUT=300                   # Cache timeout in seconds
MAX_WORKERS=4                       # Number of worker processes
REQUEST_TIMEOUT=30                  # API request timeout
```

### **Configuration Files**

#### **Production Config** (`config_prod.py`)
```python
import os

# Production settings
DEBUG_MODE = False
APP_HOST = "0.0.0.0"
APP_PORT = int(os.getenv("PORT", 8051))

# Enhanced security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# Performance settings
CACHE_TIMEOUT = 300
MAX_WORKERS = 4
REQUEST_TIMEOUT = 30

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "/app/logs/schwab_options.log"
```

---

## 🔒 **Security Considerations**

### **API Security**
```python
# Secure credential management
import os
from cryptography.fernet import Fernet

class SecureConfig:
    def __init__(self):
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        self.cipher = Fernet(self.encryption_key)
    
    def get_api_key(self):
        encrypted_key = os.getenv("ENCRYPTED_API_KEY")
        return self.cipher.decrypt(encrypted_key).decode()
```

### **Application Security**
- **HTTPS Only** - Force SSL/TLS encryption
- **Environment Variables** - Never commit credentials to code
- **Input Validation** - Sanitize all user inputs
- **Rate Limiting** - Prevent abuse and API overuse
- **CORS Configuration** - Restrict cross-origin requests

### **Network Security**
```nginx
# nginx security headers
server {
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000";
    add_header Content-Security-Policy "default-src 'self'";
}
```

---

## 📊 **Performance Optimization**

### **Application Performance**
```python
# config.py optimizations
PERFORMANCE_CONFIG = {
    # Caching
    "CACHE_ENABLED": True,
    "CACHE_TIMEOUT": 300,  # 5 minutes
    "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379"),
    
    # Processing
    "MAX_CONCURRENT_REQUESTS": 10,
    "WORKER_TIMEOUT": 30,
    "MEMORY_LIMIT": "512MB",
    
    # UI Optimization  
    "LAZY_LOADING": True,
    "COMPRESSION": True,
    "MINIFICATION": True
}
```

### **Database Optimization** (Future)
```python
# PostgreSQL for historical data
DATABASE_CONFIG = {
    "ENGINE": "postgresql",
    "HOST": os.getenv("DB_HOST", "localhost"),
    "PORT": 5432,
    "NAME": "schwab_options",
    "USER": os.getenv("DB_USER"),
    "PASSWORD": os.getenv("DB_PASSWORD"),
    "POOL_SIZE": 20,
    "MAX_OVERFLOW": 30
}
```

### **CDN Integration**
```python
# Static asset optimization
STATIC_CONFIG = {
    "CDN_ENABLED": True,
    "CDN_URL": "https://cdn.your-domain.com",
    "ASSET_VERSIONING": True,
    "GZIP_COMPRESSION": True,
    "CACHE_HEADERS": {
        "Cache-Control": "public, max-age=31536000",
        "Expires": "1 year"
    }
}
```

---

## 📈 **Monitoring & Logging**

### **Application Monitoring**
```python
# monitoring.py
import logging
import psutil
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        
    def get_system_metrics(self):
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "uptime": datetime.now() - self.start_time
        }
    
    def log_api_call(self, endpoint, duration, success):
        logging.info(f"API Call: {endpoint}, Duration: {duration}ms, Success: {success}")
```

### **Logging Configuration**
```python
# logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/schwab_options.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
```

### **Health Checks**
```python
# health.py
from flask import Flask, jsonify
import requests

health_app = Flask(__name__)

@health_app.route("/health")
def health_check():
    try:
        # Check API connectivity
        api_status = check_schwab_api()
        
        # Check system resources
        system_status = check_system_resources()
        
        # Check application status
        app_status = check_application_status()
        
        return jsonify({
            "status": "healthy" if all([api_status, system_status, app_status]) else "unhealthy",
            "api": api_status,
            "system": system_status,
            "application": app_status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

---

## 🔧 **Maintenance & Updates**

### **Automated Backups**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup configuration
cp .env $BACKUP_DIR/env_$DATE.backup

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Backup custom modules
tar -czf $BACKUP_DIR/modules_$DATE.tar.gz modules/

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

### **Update Deployment**
```bash
#!/bin/bash
# deploy_update.sh

# 1. Pull latest changes
git pull origin main

# 2. Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 3. Run tests
python -m pytest tests/ -v

# 4. Backup current version
./backup.sh

# 5. Restart application
if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
    docker-compose down
    docker-compose up -d --build
elif [ "$DEPLOYMENT_TYPE" = "systemd" ]; then
    sudo systemctl restart schwab-options
elif [ "$DEPLOYMENT_TYPE" = "heroku" ]; then
    git push heroku main
fi

# 6. Verify deployment
curl -f http://localhost:8051/health || echo "Health check failed"

echo "Deployment completed successfully"
```

### **Rollback Procedure**
```bash
#!/bin/bash
# rollback.sh

# 1. Get previous version
PREV_COMMIT=$(git log --oneline -n 2 | tail -1 | cut -d' ' -f1)

# 2. Rollback code
git checkout $PREV_COMMIT

# 3. Restore dependencies
pip install -r requirements.txt

# 4. Restart services
sudo systemctl restart schwab-options

# 5. Verify rollback
curl -f http://localhost:8051/health

echo "Rollback to $PREV_COMMIT completed"
```

---

## 🌐 **Domain & SSL Setup**

### **Domain Configuration**
```nginx
# /etc/nginx/sites-available/schwab-options.com
server {
    listen 80;
    server_name schwab-options.com www.schwab-options.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name schwab-options.com www.schwab-options.com;
    
    ssl_certificate /etc/letsencrypt/live/schwab-options.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/schwab-options.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8051;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **SSL Certificate (Let's Encrypt)**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d schwab-options.com -d www.schwab-options.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment**:
- [ ] API credentials configured and tested
- [ ] All dependencies installed and versions locked
- [ ] Environment variables properly set
- [ ] Security headers and HTTPS configured
- [ ] Performance optimizations applied
- [ ] Monitoring and logging enabled

### **Post-Deployment**:
- [ ] Health check endpoint responding
- [ ] All 11 modules loading and functional (Phase 3)
- [ ] API connectivity verified
- [ ] Seamless authentication working
- [ ] Historical data collection operational
- [ ] Live/Historical toggle functional in all modules
- [ ] Performance benchmarks met
- [ ] Error logging working correctly
- [ ] Backup procedures tested

### **Production Readiness**:
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Rollback procedure tested
- [ ] Monitoring alerts configured
- [ ] Support procedures documented

---

## 🆘 **Troubleshooting**

### **Common Deployment Issues**:

#### **Port Binding Errors**:
```bash
# Issue: "Address already in use"
# Solution: Change port or kill existing process
sudo lsof -i :8051
sudo kill -9 <PID>
```

#### **Permission Errors**:
```bash
# Issue: Permission denied errors
# Solution: Fix file permissions
chmod +x dash_app.py
chown -R $USER:$USER /app
```

#### **Memory Issues**:
```bash
# Issue: Out of memory errors
# Solution: Increase instance size or optimize code
# Monitor memory usage:
htop
# Add swap if needed:
sudo fallocate -l 2G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### **API Connection Issues**:
```python
# Issue: API authentication failures
# Solution: Verify credentials and network connectivity
import requests
response = requests.get("https://api.schwabapi.com/v1/")
print(response.status_code)  # Should be 200 or authentication challenge
```

---

## 📞 **Support & Maintenance**

### **Support Channels**:
- **GitHub Issues**: Technical problems and bug reports
- **Documentation**: Comprehensive guides and troubleshooting
- **Email Support**: Direct support for critical issues

### **Maintenance Schedule**:
- **Daily**: Automated health checks and log monitoring
- **Weekly**: Performance review and optimization
- **Monthly**: Security updates and dependency upgrades
- **Quarterly**: Full system audit and capacity planning

### **Emergency Procedures**:
- **Service Down**: Automatic restart and notification
- **API Failure**: Fallback to cached data with user notification
- **Security Breach**: Immediate shutdown and investigation protocol
- **Data Corruption**: Restore from backup and integrity verification

---

**📅 Last Updated**: September 16, 2025
**🚀 Current Version**: ✅ **Phase 3 Complete** - Historical Analysis System
**🔧 Deployment Status**: Production-Ready with 11 Advanced Modules
**📊 Monitoring**: Health checks and logging active

---

## 🎉 **Phase 3 Deployment Features**

### **Enhanced Authentication Setup**:
- ✅ **Seamless Web-Based OAuth** - No terminal complexity required
- ✅ **Integrated Authentication Modal** - Built into main application
- ✅ **Real-time Status Monitoring** - Live auth status with expiry warnings
- ✅ **Automatic Token Management** - Handles refresh and re-authentication

### **Historical Data Collection System**:
```bash
# Phase 3: Automated Data Collection Setup

# 1. Initialize historical data collection
python collect_daily_data.py --setup

# 2. Test data collection for specific symbols
python collect_daily_data.py --symbols SPY,QQQ,AAPL

# 3. Setup automated daily collection (cron)
crontab -e
# Add: 30 16 * * 1-5 cd /path/to/schwaboptions && python collect_daily_data.py

# 4. Verify historical data availability
python test_historical_flow.py
```

### **Advanced Module Capabilities**:
- ✅ **11 Professional Modules** - Complete trading platform functionality
- ✅ **Live/Historical Toggle** - Smart mode switching in all modules
- ✅ **Time-Series Controls** - 1D, 3D, 1W, 2W analysis periods
- ✅ **Pattern Recognition** - Whale activity, sweep patterns, position builds
- ✅ **Multi-Day Analysis** - ConvexValue + Unusual Whales style analysis

### **Production Deployment Enhancements**:
```bash
# Phase 3 Production Setup

# 1. Deploy with historical data support
docker run -d \
  --name schwab-options \
  -p 8051:8051 \
  -v /data/historical:/app/data/historical \
  -e API_KEY=your_api_key \
  -e API_SECRET=your_api_secret \
  -e HISTORICAL_DATA_PATH=/app/data/historical \
  schwab-options-analytics

# 2. Setup automated data collection service
sudo tee /etc/systemd/system/schwab-data-collector.service > /dev/null <<EOF
[Unit]
Description=SchwaOptions Historical Data Collector
After=network.target

[Service]
Type=oneshot
User=schwab
WorkingDirectory=/opt/schwab-options
ExecStart=/opt/schwab-options/venv/bin/python collect_daily_data.py
EnvironmentFile=/opt/schwab-options/.env

[Install]
WantedBy=multi-user.target
EOF

# 3. Setup daily collection timer
sudo tee /etc/systemd/system/schwab-data-collector.timer > /dev/null <<EOF
[Unit]
Description=Run SchwaOptions Data Collection Daily
Requires=schwab-data-collector.service

[Timer]
OnCalendar=Mon-Fri *-*-* 16:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# 4. Enable and start services
sudo systemctl enable schwab-data-collector.timer
sudo systemctl start schwab-data-collector.timer
```

### **Backup & Recovery for Historical Data**:
```bash
# Enhanced backup script for Phase 3
#!/bin/bash
# backup_phase3.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
HISTORICAL_DATA_DIR="./data/historical"

# Backup historical data
tar -czf $BACKUP_DIR/historical_data_$DATE.tar.gz $HISTORICAL_DATA_DIR

# Backup configuration with historical settings
cp .env $BACKUP_DIR/env_phase3_$DATE.backup

# Backup enhanced modules
tar -czf $BACKUP_DIR/modules_phase3_$DATE.tar.gz modules/ data/enhanced_schwab_client.py data/historical_collector.py

echo "Phase 3 backup completed: $DATE"
echo "Historical data backed up from: $HISTORICAL_DATA_DIR"
```