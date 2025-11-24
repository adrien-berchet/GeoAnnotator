# Monitoring & Observability

This document describes the monitoring and observability features implemented in GeoAnnotator.

## Overview

GeoAnnotator includes comprehensive monitoring capabilities for production environments:

- **Error Tracking**: Sentry integration for automatic error reporting
- **Health Checks**: HTTP endpoints for container orchestration and load balancer health checks
- **Metrics**: Application metrics endpoint for monitoring key statistics
- **Request Tracing**: Unique request IDs for distributed tracing and debugging
- **Structured Logging**: Logger integration with Sentry for error correlation

## Features

### 1. Sentry Error Tracking

**What is Sentry?**
Sentry is an error tracking and performance monitoring platform that automatically captures errors and exceptions from both backend and frontend applications.

**Benefits:**
- Automatic error capture and stack traces
- Performance monitoring and slow query detection
- User session replay for debugging
- Real-time alerts for critical errors
- Free tier available: 5,000 errors/month

**Setup:**

1. **Create a Sentry account** (free): https://sentry.io/
2. **Create two projects** in Sentry:
   - One for the Django backend
   - One for the React frontend
3. **Get your DSN** from each project's settings
4. **Configure environment variables** in `.env`:

```bash
# Backend Sentry
SENTRY_DSN=https://your-backend-dsn@sentry.io/your-project-id
SENTRY_ENVIRONMENT=production  # or development, staging
SENTRY_TRACES_SAMPLE_RATE=0.1  # Capture 10% of transactions

# Frontend Sentry
VITE_SENTRY_DSN=https://your-frontend-dsn@sentry.io/your-project-id
VITE_SENTRY_ENVIRONMENT=production
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
```

**What gets tracked:**
- **Backend**: All uncaught exceptions, database errors, Celery task failures
- **Frontend**: JavaScript errors, unhandled promise rejections, API errors
- **Performance**: Slow database queries, API response times, page load times
- **Context**: User info, request data, breadcrumbs leading to errors

**Privacy:**
- Authorization headers are automatically stripped
- No PII (personally identifiable information) is sent by default
- Email addresses and sensitive data are filtered

### 2. Health Check Endpoint

**Endpoint:** `GET /api/v1/system/health/`

**Purpose:** Container orchestration (Docker, Kubernetes) and load balancers use this endpoint to determine if the application is healthy.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": {
    "healthy": true,
    "message": "Database connection successful"
  },
  "redis": {
    "healthy": true,
    "message": "Redis connection successful"
  }
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "database": {
    "healthy": false,
    "message": "Database error: connection refused"
  },
  "redis": {
    "healthy": true,
    "message": "Redis connection successful"
  }
}
```

**Checks performed:**
- Database connectivity (PostgreSQL)
- Redis connectivity (if configured)
- Returns 503 if any critical service is down

**Docker Compose health check example:**
```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/system/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Kubernetes liveness probe example:**
```yaml
livenessProbe:
  httpGet:
    path: /api/v1/system/health/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

### 3. Metrics Endpoint

**Endpoint:** `GET /api/v1/system/metrics/`

**Authentication:** Requires admin user authentication

**Purpose:** Provides application metrics for monitoring dashboards (Grafana, Datadog, etc.)

**Response:**
```json
{
  "points_count": 1523,
  "users_count": 87,
  "annotations_count": 4521,
  "database_healthy": true
}
```

**Use cases:**
- Monitor application growth over time
- Track user engagement
- Set up alerts for abnormal patterns
- Create monitoring dashboards

**Prometheus scraping example:**
```yaml
scrape_configs:
  - job_name: 'geoannotator'
    metrics_path: '/api/v1/system/metrics/'
    basic_auth:
      username: admin
      password: ${ADMIN_PASSWORD}
    static_configs:
      - targets: ['backend:8000']
```

### 4. Request ID Middleware

**What it does:**
- Adds a unique ID to every HTTP request
- Includes request ID in all log messages
- Returns request ID in response headers as `X-Request-ID`

**Benefits:**
- Trace a single request through all log messages
- Debug issues by correlating frontend and backend logs
- Support distributed tracing across microservices

**Usage:**

When making API requests, include the request ID from a previous response:
```javascript
// Frontend automatically includes X-Request-ID from previous requests
fetch('/api/points/', {
  headers: {
    'X-Request-ID': previousRequestId  // Optional, for correlation
  }
})
```

**In logs:**
```
[2025-01-15 10:23:45] INFO [request_id=abc-123] User authenticated: user@example.com
[2025-01-15 10:23:45] INFO [request_id=abc-123] Fetching GPS points for user: user@example.com
[2025-01-15 10:23:46] INFO [request_id=abc-123] Returned 42 GPS points
```

### 5. Structured Logging

**Frontend Logger:**

The frontend logger (`src/utils/logger.ts`) provides environment-aware logging:

```typescript
import { logger } from '@/utils/logger';

// Development only
logger.debug('User clicked button', { buttonId: 'submit' });
logger.info('Map initialized');

// Always shown
logger.warn('API response slow', { duration: 5000 });

// Always shown + sent to Sentry in production
logger.error('Failed to load points', error);
```

**Backend Logger:**

Use Python's standard logging with request ID context:

```python
import logging

logger = logging.getLogger(__name__)

def my_view(request):
    # Request ID automatically included in logs
    logger.info('Processing request')
    logger.error('Something went wrong', exc_info=True)
```

## Monitoring Best Practices

### 1. Set up alerts in Sentry
- **Critical**: Database connection failures, authentication errors
- **Warning**: API response times > 2s, high error rates
- **Info**: New releases deployed

### 2. Monitor key metrics
- User growth rate
- Storage usage trends
- API response times
- Error rates by endpoint

### 3. Use request IDs for debugging
When a user reports an issue:
1. Ask them to check the browser Network tab
2. Find the `X-Request-ID` header from the failing request
3. Search logs for that request ID to see the full trace

### 4. Regular log reviews
- Weekly: Review Sentry issues, prioritize fixes
- Monthly: Analyze performance trends, optimize slow queries
- Quarterly: Review and update alert thresholds

## Cost Optimization

### Sentry Free Tier Limits
- **Errors**: 5,000 per month
- **Performance transactions**: 10,000 per month
- **Replay sessions**: 50 per month

### Stay within limits:
1. **Adjust sample rates** in production:
   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.05  # 5% of transactions
   ```

2. **Filter noisy errors** in Sentry UI:
   - Ignore 404 errors
   - Ignore known third-party script errors
   - Ignore network timeout errors in unstable networks

3. **Use selective error capture**:
   ```python
   # Only capture errors for critical operations
   try:
       critical_operation()
   except Exception as e:
       sentry_sdk.capture_exception(e)
   ```

## Troubleshooting

### Sentry not receiving errors

**Check configuration:**
```bash
# Backend
python manage.py shell
>>> import os
>>> os.environ.get('SENTRY_DSN')

# Frontend
console.log(import.meta.env.VITE_SENTRY_DSN)
```

**Check console output:**
```bash
# Backend logs should show:
# No "Sentry initialized" message means DSN not configured

# Frontend console should show:
# "Sentry DSN not configured - error tracking disabled"
# or
# "Sentry initialized for environment: production"
```

### Health check returning 503

**Check individual service health:**
```bash
curl http://localhost:8000/api/v1/system/health/
```

Look at the specific service that's unhealthy:
- **Database**: Check PostgreSQL is running
- **Redis**: Check Redis container is running (optional for basic functionality)

### Request IDs not appearing in logs

**Check middleware is enabled:**
```python
# config/settings/base.py
MIDDLEWARE = [
    # ...
    'apps.core.middleware.RequestIDMiddleware',  # Should be present
    # ...
]
```

## Further Reading

- [Sentry Documentation](https://docs.sentry.io/)
- [Django Health Checks](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [Request ID Pattern](https://www.honeybadger.io/blog/request-id/)
- [Observability Best Practices](https://sre.google/sre-book/monitoring-distributed-systems/)
