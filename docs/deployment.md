# GeoAnnotator Deployment Guide

This guide covers deploying GeoAnnotator to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Celery & Redis Setup](#celery--redis-setup)
5. [Docker Deployment](#docker-deployment)
6. [Manual Deployment](#manual-deployment)
7. [Environment Variables](#environment-variables)
8. [Security Checklist](#security-checklist)
9. [Monitoring & Logging](#monitoring--logging)
10. [Backup & Restore](#backup--restore)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4 GB
- Storage: 20 GB SSD
- OS: Ubuntu 20.04+ / Debian 11+ / RHEL 8+

**Recommended** (for 1000+ users):
- CPU: 4+ cores
- RAM: 8+ GB
- Storage: 100+ GB SSD
- OS: Ubuntu 22.04 LTS

### Software Requirements

- Docker 20.10+ and Docker Compose 2.0+ **OR**
- Python 3.11+
- PostgreSQL 15+ with PostGIS 3.4+
- Node.js 20+
- Nginx 1.18+ (for manual deployment)

### Domain & SSL

- Domain name (e.g., `geoannotator.example.com`)
- SSL certificate (Let's Encrypt recommended)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/geoannotator.git
cd geoannotator
```

### 2. Create Environment File

```bash
cp .env.example .env
nano .env
```

**Critical Settings**:

```env
# Django
DEBUG=False
SECRET_KEY=<generate-random-secret-key>
ALLOWED_HOSTS=geoannotator.example.com,www.geoannotator.example.com

# Database
DB_PASSWORD=<strong-database-password>

# Storage
MINIO_ROOT_USER=<minio-admin-username>
MINIO_ROOT_PASSWORD=<strong-minio-password>

# Frontend
VITE_API_URL=https://geoannotator.example.com/api/v1

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=<email-password>
```

**Generate SECRET_KEY**:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Database Configuration

### Option 1: Docker (Included)

PostgreSQL with PostGIS is included in `docker-compose.yml`. No additional setup needed.

### Option 2: Managed Database (AWS RDS, DigitalOcean, etc.)

1. **Create PostgreSQL 15+ database** with PostGIS extension
2. **Enable PostGIS**:
   ```sql
   CREATE EXTENSION postgis;
   ```
3. **Update DATABASE_URL** in `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/database
   ```

### Option 3: Manual PostgreSQL Installation

**Ubuntu/Debian**:

```bash
# Install PostgreSQL and PostGIS
sudo apt update
sudo apt install postgresql-15 postgresql-15-postgis-3 postgis

# Create database and user
sudo -u postgres psql

CREATE DATABASE geoannotator;
CREATE USER geoannotator WITH PASSWORD 'your_password';
ALTER ROLE geoannotator SET client_encoding TO 'utf8';
ALTER ROLE geoannotator SET default_transaction_isolation TO 'read committed';
ALTER ROLE geoannotator SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE geoannotator TO geoannotator;

\c geoannotator
CREATE EXTENSION postgis;
\q
```

**Configure PostgreSQL** (`/etc/postgresql/15/main/postgresql.conf`):

```conf
listen_addresses = 'localhost'  # Or specific IP for remote access
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
```

**Restart PostgreSQL**:

```bash
sudo systemctl restart postgresql
```

---

## Celery & Redis Setup

GeoAnnotator utilise Celery pour l'envoi asynchrone d'emails et les tâches planifiées (nettoyage des tokens, suppression des comptes).

**⚠️ Important** : Sans Redis et Celery, les emails seront envoyés de manière synchrone (bloquante) et peuvent causer des timeouts en production.

Pour une configuration complète de Celery et Redis, consultez la [documentation dédiée](./celery-redis-setup.md).

**Configuration rapide avec Docker** : Redis et Celery sont déjà inclus dans `docker-compose.yml`. Aucune configuration supplémentaire n'est nécessaire.

**Configuration manuelle** :
1. Installer Redis : `sudo apt install redis-server`
2. Configurer les variables d'environnement :
   ```env
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```
3. Démarrer les workers :
   ```bash
   celery -A config worker --loglevel=info
   celery -A config beat --loglevel=info
   ```

Voir [celery-redis-setup.md](./celery-redis-setup.md) pour plus de détails.

---

## Docker Deployment

### Production Deployment with Docker

**1. Build and Start Services**:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

**2. Run Migrations**:

```bash
docker-compose exec backend python manage.py migrate
```

**3. Create Superuser**:

```bash
docker-compose exec backend python manage.py createsuperuser
```

**4. Collect Static Files**:

```bash
docker-compose exec backend python manage.py collectstatic --noinput
```

**5. Setup MinIO Bucket**:

Access MinIO console at `http://your-server:9001`:
- Login with `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`
- Create bucket named `geoannotator`
- Set bucket policy to public (for file downloads)

**6. Configure Nginx Reverse Proxy** (see [Nginx Configuration](#nginx-reverse-proxy))

---

## Manual Deployment

### Backend Deployment

**1. Install System Dependencies**:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip \
  gcc g++ libpq-dev gdal-bin libgdal-dev libgeos-dev libproj-dev
```

**2. Create Virtual Environment**:

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
```

**3. Install Python Dependencies**:

```bash
pip install --upgrade pip
pip install -r requirements/production.txt
```

**4. Configure Django Settings**:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
```

**5. Run Migrations**:

```bash
python manage.py migrate
```

**6. Create Superuser**:

```bash
python manage.py createsuperuser
```

**7. Collect Static Files**:

```bash
python manage.py collectstatic --noinput
```

**8. Start Gunicorn**:

```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 60 \
  --access-logfile /var/log/geoannotator/access.log \
  --error-logfile /var/log/geoannotator/error.log \
  --daemon
```

**9. Setup Systemd Service** (recommended):

Create `/etc/systemd/system/geoannotator.service`:

```ini
[Unit]
Description=GeoAnnotator Django Backend
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/geoannotator/backend
Environment="PATH=/path/to/geoannotator/backend/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
EnvironmentFile=/path/to/geoannotator/.env
ExecStart=/path/to/geoannotator/backend/venv/bin/gunicorn \
  config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 60

[Install]
WantedBy=multi-user.target
```

**Enable and Start**:

```bash
sudo systemctl enable geoannotator
sudo systemctl start geoannotator
sudo systemctl status geoannotator
```

### Frontend Deployment

**1. Build Frontend**:

```bash
cd frontend
npm ci
VITE_API_URL=https://geoannotator.example.com/api/v1 npm run build
```

**2. Copy Build Files**:

```bash
sudo cp -r dist/* /var/www/geoannotator/
```

**3. Configure Nginx** (see [Nginx Configuration](#nginx-reverse-proxy))

---

## Nginx Reverse Proxy

### SSL with Let's Encrypt

**Install Certbot**:

```bash
sudo apt install certbot python3-certbot-nginx
```

**Obtain Certificate**:

```bash
sudo certbot --nginx -d geoannotator.example.com -d www.geoannotator.example.com
```

### Nginx Configuration

Create `/etc/nginx/sites-available/geoannotator`:

```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name geoannotator.example.com www.geoannotator.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name geoannotator.example.com www.geoannotator.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/geoannotator.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/geoannotator.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend (React)
    root /var/www/geoannotator;
    index index.html;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Frontend SPA Routing
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    # Static Assets Caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;

        # File upload size limit (1GB)
        client_max_body_size 1G;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static Files
    location /static/ {
        alias /path/to/geoannotator/backend/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media Files
    location /media/ {
        alias /path/to/geoannotator/backend/media/;
        expires 30d;
        add_header Cache-Control "public";
    }
}
```

**Enable Site**:

```bash
sudo ln -s /etc/nginx/sites-available/geoannotator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Debug mode (False in production) | `False` |
| `SECRET_KEY` | Django secret key | `<random-50-char-string>` |
| `ALLOWED_HOSTS` | Allowed hostnames | `geoannotator.com,www.geoannotator.com` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `DB_PASSWORD` | Database password | `<strong-password>` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SETTINGS_MODULE` | Settings module | `config.settings.production` |
| `EMAIL_BACKEND` | Email backend | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USE_TLS` | Use TLS | `True` |
| `AWS_ACCESS_KEY_ID` | S3/MinIO access key | - |
| `AWS_SECRET_ACCESS_KEY` | S3/MinIO secret key | - |
| `AWS_STORAGE_BUCKET_NAME` | S3/MinIO bucket | `geoannotator` |
| `CORS_ALLOWED_ORIGINS` | CORS origins | `https://geoannotator.com` |

---

## Security Checklist

### Pre-Deployment

- [ ] Set `DEBUG=False` in production
- [ ] Generate strong, unique `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with actual domain(s)
- [ ] Use strong database password
- [ ] Enable SSL/TLS (HTTPS)
- [ ] Configure CORS properly
- [ ] Change default MinIO credentials
- [ ] Set up email backend (not console)
- [ ] Review Django security settings

### Post-Deployment

- [ ] Enable firewall (UFW, iptables)
- [ ] Restrict database access to localhost
- [ ] Configure fail2ban for SSH
- [ ] Set up regular database backups
- [ ] Enable logging and monitoring
- [ ] Test SSL configuration (SSL Labs)
- [ ] Scan for vulnerabilities
- [ ] Document admin credentials securely

### Recommended Django Security Settings

In `config/settings/production.py`:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'
```

---

## Monitoring & Logging

### Application Logs

**Django Logs** (`/var/log/geoannotator/`):
- `django.log`: Application logs
- `access.log`: HTTP access logs
- `error.log`: Error logs

**Log Rotation** (`/etc/logrotate.d/geoannotator`):

```
/var/log/geoannotator/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload geoannotator > /dev/null 2>&1 || true
    endscript
}
```

### Monitoring Tools

**Option 1: Prometheus + Grafana**
- Install `django-prometheus`
- Configure metrics endpoint
- Visualize with Grafana dashboards

**Option 2: Sentry** (Error Tracking)
```bash
pip install sentry-sdk
```

In `settings/production.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
)
```

**Option 3: Uptime Monitoring**
- UptimeRobot
- Pingdom
- StatusCake

---

## Backup & Restore

### Automated Daily Backups

**Backup Script** (`/usr/local/bin/backup-geoannotator.sh`):

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/geoannotator"
DATE=$(date +%Y%m%d-%H%M%S)

# Database backup
docker-compose exec -T db pg_dump -U geoannotator geoannotator | gzip > "$BACKUP_DIR/db-$DATE.sql.gz"

# Media files backup
tar -czf "$BACKUP_DIR/media-$DATE.tar.gz" /path/to/media

# Delete backups older than 30 days
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Cron Job** (daily at 2 AM):

```bash
0 2 * * * /usr/local/bin/backup-geoannotator.sh >> /var/log/geoannotator/backup.log 2>&1
```

### Restore from Backup

**Database Restore**:

```bash
gunzip -c /var/backups/geoannotator/db-20250101-020000.sql.gz | \
  docker-compose exec -T db psql -U geoannotator geoannotator
```

**Media Files Restore**:

```bash
tar -xzf /var/backups/geoannotator/media-20250101-020000.tar.gz -C /path/to/restore
```

---

## Scheduled Tasks

### Trash Cleanup (Daily)

**Add to Crontab** (user running Docker/Django):

```bash
# Docker deployment
0 2 * * * cd /path/to/geoannotator && docker-compose exec -T backend python manage.py cleanup_trash >> /var/log/geoannotator/cleanup.log 2>&1

# Manual deployment
0 2 * * * cd /path/to/geoannotator/backend && /path/to/venv/bin/python manage.py cleanup_trash >> /var/log/geoannotator/cleanup.log 2>&1
```

### Database Optimization (Weekly)

```bash
0 3 * * 0 docker-compose exec -T db vacuumdb -U geoannotator geoannotator
```

---

## Troubleshooting

### Common Issues

**1. 502 Bad Gateway**

**Cause**: Backend not running or Nginx misconfigured

**Solution**:
```bash
# Check backend status
sudo systemctl status geoannotator
# Or for Docker
docker-compose ps

# Check Nginx config
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log
docker-compose logs backend
```

**2. Database Connection Errors**

**Cause**: PostgreSQL not running or wrong credentials

**Solution**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U geoannotator -d geoannotator

# Verify DATABASE_URL in .env
```

**3. 413 Payload Too Large**

**Cause**: File upload exceeds Nginx limit

**Solution**: Increase `client_max_body_size` in Nginx config:
```nginx
client_max_body_size 1G;
```

**4. Static Files Not Loading**

**Cause**: Static files not collected or wrong path

**Solution**:
```bash
# Collect static files
python manage.py collectstatic --noinput

# Verify static root in Nginx config
```

**5. CORS Errors**

**Cause**: Frontend and backend on different domains without CORS config

**Solution**: Add frontend domain to `CORS_ALLOWED_ORIGINS` in `.env`

---

## Performance Optimization

### Database Tuning

**PostgreSQL** (`postgresql.conf`):
```conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 100
```

### Caching

**Install Redis**:
```bash
sudo apt install redis-server
```

**Django Cache Settings** (`settings/production.py`):
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### CDN for Static Files

Use AWS CloudFront, Cloudflare, or similar for:
- Static assets (JS, CSS, images)
- Media files
- Faster global delivery

---

## Scaling

### Horizontal Scaling

**Load Balancer + Multiple App Servers**:
- Use Nginx/HAProxy for load balancing
- Run multiple Gunicorn instances
- Share media files via S3/MinIO
- Use managed PostgreSQL (RDS, etc.)

**Example** (3 app servers):
```
[Load Balancer]
    |
    ├── App Server 1 (Gunicorn)
    ├── App Server 2 (Gunicorn)
    └── App Server 3 (Gunicorn)
         |
    [Shared Database]
    [Shared Storage (S3)]
```

### Vertical Scaling

Increase resources:
- CPU: 4 → 8 cores
- RAM: 8 → 16 GB
- Storage: SSD with higher IOPS

---

## Compliance

### GDPR Considerations

- **Data Deletion**: Users can delete their points (moved to trash for 30 days)
- **Data Export**: Users can export their data in multiple formats
- **Data Access**: Users can view all their shared points
- **Privacy Policy**: Add privacy policy page (not included)
- **Cookie Consent**: Add cookie consent banner (not included)

### Backup Retention

- Daily backups: 30 days
- Weekly backups: 12 weeks
- Monthly backups: 12 months

---

## Contact & Support

For deployment issues:
- **GitHub Issues**: https://github.com/yourusername/geoannotator/issues
- **Email**: support@example.com
- **Documentation**: https://docs.geoannotator.com

---

**Last Updated**: 2025-10-06
**Version**: 1.0.0
