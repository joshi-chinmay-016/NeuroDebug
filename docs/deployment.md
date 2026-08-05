# Deployment Documentation

## Overview

NeuroDebug is designed for easy deployment across various platforms. This guide covers local development, containerized deployment, and production deployment strategies.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (for local development without Docker)

## Local Development

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Seed database with subscription plans
python scripts/seed_database.py

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

## Docker Deployment

### Using Docker Compose

The easiest way to run NeuroDebug is with Docker Compose:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Service Configuration

The `docker-compose.yml` includes:

- **PostgreSQL**: Database service
- **Backend**: FastAPI application
- **Frontend**: React application with nginx

### Environment Variables

Copy and configure environment files:

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

## Production Deployment

### Database Setup

#### PostgreSQL

```bash
# Create database
createdb neurodebug

# Run migrations
cd backend
alembic upgrade head

# Seed data
python scripts/seed_database.py
```

#### Connection String

Set the `DATABASE_URL` environment variable:

```
postgresql+asyncpg://user:password@host:port/database
```

### Backend Deployment

#### Environment Variables

Required environment variables for production:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Groq API
GROQ_API_KEY=your_api_key
GROQ_MODEL=llama-3.1-8b-instant

# Session
SESSION_EXPIRY_HOURS=24

# Usage Limits
DEFAULT_GUEST_LIMIT=3
DEFAULT_FREE_LIMIT=5
DEFAULT_PRO_LIMIT=20

# Logging
LOG_LEVEL=INFO
```

#### Running with Gunicorn

```bash
cd backend

# Install production dependencies
pip install gunicorn uvloop

# Run with Gunicorn
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

#### Running with Uvicorn

```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### Frontend Deployment

#### Build Process

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Preview build
npm run preview
```

#### Static Hosting

The `dist/` folder contains the production build. Deploy to:

- **Vercel**: `vercel deploy`
- **Netlify**: `netlify deploy --prod`
- **AWS S3 + CloudFront**: Upload dist/ to S3
- **nginx**: Configure nginx to serve static files

#### nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/neurodebug/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

## Cloud Deployment

### Render

#### Backend

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables
4. Deploy

#### Frontend

1. Create a new Static Site on Render
2. Connect your GitHub repository
3. Set build command: `npm run build`
4. Set publish directory: `dist`
5. Deploy

### AWS

#### Using ECS

```yaml
# docker-compose.aws.yml
version: '3.8'

services:
  backend:
    image: neurodebug-backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GROQ_API_KEY=${GROQ_API_KEY}
    ports:
      - "8000:8000"

  frontend:
    image: neurodebug-frontend:latest
    ports:
      - "80:80"
```

#### Using Lambda

Package the backend for AWS Lambda:

```bash
pip install zappa
zappa init
zappa deploy production
```

### DigitalOcean

#### App Platform

1. Create a new App
2. Add backend service (Python)
3. Add frontend service (Node.js)
4. Add PostgreSQL service
5. Configure environment variables
6. Deploy

## Monitoring

### Health Checks

Backend health endpoint:

```bash
curl https://your-api.com/health
```

Response:

```json
{
  "status": "healthy",
  "service": "NeuroDebug API",
  "version": "1.0.0"
}
```

### Logging

Backend logs are structured JSON:

```json
{
  "level": "INFO",
  "message": "Debug request received",
  "request_id": "abc123",
  "code_length": 150,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Metrics

Key metrics to monitor:

- Request rate
- Error rate
- Response time
- Database connection pool
- Memory usage
- CPU usage

## Security

### SSL/TLS

Always use HTTPS in production:

- Let's Encrypt (free)
- AWS Certificate Manager
- Cloudflare SSL

### Environment Variables

Never commit secrets to Git:

- Use environment variables
- Use secret management services
- Rotate keys regularly

### Firewall

Restrict database access:

- Allow only application servers
- Use VPCs/security groups
- Enable SSL for database connections

## Backup and Recovery

### Database Backups

```bash
# Backup
pg_dump neurodebug > backup.sql

# Restore
psql neurodebug < backup.sql
```

### Automated Backups

Set up automated backups:

- AWS RDS automated backups
- DigitalOcean managed backups
- Custom cron jobs

## Scaling

### Horizontal Scaling

- Use load balancer (nginx, HAProxy, AWS ALB)
- Deploy multiple backend instances
- Use database read replicas
- Implement caching layer

### Vertical Scaling

- Increase server resources
- Optimize database queries
- Add database indexes
- Tune connection pool size

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U neurodebug -d neurodebug -h localhost

# Check logs
tail -f /var/log/postgresql/postgresql-16-main.log
```

### Backend Issues

```bash
# Check logs
docker-compose logs backend

# Restart service
docker-compose restart backend

# Check database migrations
alembic current
alembic history
```

### Frontend Issues

```bash
# Clear cache
rm -rf node_modules dist
npm install
npm run build

# Check environment variables
cat .env
```

## Maintenance

### Database Maintenance

```sql
-- Vacuum database
VACUUM ANALYZE;

-- Reindex
REINDEX DATABASE neurodebug;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Log Rotation

Set up log rotation:

```bash
# /etc/logrotate.d/neurodebug
/var/log/neurodebug/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

## Performance Tuning

### Database Tuning

```sql
-- Increase work_mem
SET work_mem = '256MB';

-- Increase shared_buffers
SET shared_buffers = '256MB';

-- Increase effective_cache_size
SET effective_cache_size = '1GB';
```

### Application Tuning

- Adjust database pool size
- Enable query caching
- Optimize N+1 queries
- Add database indexes
- Use connection pooling

## CI/CD

### GitHub Actions

The `.github/workflows/ci.yml` includes:

- Backend linting and testing
- Frontend linting and building
- Database service for tests
- Automated deployment (future)

### Manual Deployment

```bash
# Backend
git pull origin main
pip install -r requirements.txt
alembic upgrade head
systemctl restart neurodebug-backend

# Frontend
git pull origin main
npm install
npm run build
systemctl restart nginx
```
