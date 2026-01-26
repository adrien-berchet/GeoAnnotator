# Database Backup Troubleshooting

This guide helps resolve common issues with the automated database backup system.

## Error: "Control plane request failed"

### Symptoms

```
Database backup failed: Failed to create backup: pg_dump failed:
pg_dump: error: connection to server at "<DB_NAME>" (<DB_IP>), port 5432 failed:
ERROR: Control plane request failed
```

### Cause

This error is specific to **Neon.tech** and other managed PostgreSQL services that use **connection pooling**. The issue occurs when `pg_dump` tries to connect through a connection pooler instead of a direct connection.

### Why pg_dump Needs Direct Connection

- **Connection poolers** (like PgBouncer or Neon's pooler) are designed for short-lived web requests
- **pg_dump** requires full PostgreSQL protocol access, including system catalog queries
- Poolers don't support all PostgreSQL commands needed by pg_dump

### Solution 1: Use Direct Connection URL (Recommended)

Set the `BACKUP_DATABASE_URL` environment variable with Neon's **direct connection URL**.

#### For Neon.tech:

1. Go to [Neon Console](https://console.neon.tech/)
2. Select your project → **Connection Details**
3. Toggle from **"Pooled connection"** to **"Direct connection"**
4. Copy the connection string (looks like):
   ```
   postgresql://user:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-xxxxx
   ```

5. Add this to your Celery Beat and Celery Worker services on Render:
   ```bash
   BACKUP_DATABASE_URL=postgresql://user:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-xxxxx
   ```

**Key Differences**:
- **Pooled URL**: `@ep-xxxxx-pooler.region.aws.neon.tech` ❌ (won't work with pg_dump)
- **Direct URL**: `@ep-xxxxx.region.aws.neon.tech` + `options=endpoint%3Dep-xxxxx` ✅ (works with pg_dump)

#### For Render Services:

1. Navigate to **Dashboard** → **geoannotator-celery-beat** → **Environment**
2. Add new variable:
   - **Key**: `BACKUP_DATABASE_URL`
   - **Value**: (paste direct connection URL from Neon)
3. Click **"Save Changes"**
4. Repeat for **geoannotator-celery-worker** service

The backup command will automatically use `BACKUP_DATABASE_URL` if available, otherwise fall back to `DATABASE_URL`.

### Solution 2: Modify DATABASE_URL (Not Recommended)

If you replace `DATABASE_URL` with the direct connection URL, it will work for backups but **may impact application performance** because:
- Direct connections don't benefit from connection pooling
- Limited connection slots on free Neon tier
- Higher latency for web requests

**Only use this if you can't set a separate `BACKUP_DATABASE_URL`**.

## Error: "pg_dump not found"

### Symptoms

```
CommandError: pg_dump not found. Please install postgresql-client: apt-get install postgresql-client
```

### Solution

Install PostgreSQL client tools on your server:

#### On Render.com:

Add to your `Dockerfile`:
```dockerfile
RUN apt-get update && apt-get install -y postgresql-client
```

#### On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y postgresql-client
```

#### On Alpine Linux:

```bash
apk add --no-cache postgresql-client
```

## Error: "AWS_STORAGE_BUCKET_NAME not configured"

### Symptoms

```
CommandError: AWS_STORAGE_BUCKET_NAME not configured. Please set it in your environment.
```

### Solution

Configure S3 or S3-compatible storage (MinIO, Backblaze B2, etc.):

```bash
# Required
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=geoannotator-backups

# Optional (for non-AWS S3 services)
AWS_S3_ENDPOINT_URL=https://s3.your-provider.com
AWS_S3_REGION_NAME=us-east-1
```

### Alternative: Disable Backups

If you don't need automated backups, disable the scheduled task in [config/celery.py](../backend/config/celery.py):

```python
# Comment out the backup task
app.conf.beat_schedule = {
    # "backup-database-weekly": {
    #     "task": "apps.core.tasks.backup_database_task",
    #     "schedule": crontab(day_of_week=0, hour=3, minute=0),
    # },
}
```

## Testing Backups

### Test Manually

Run the backup command manually to verify configuration:

```bash
# Dry run (doesn't create actual backup)
python manage.py backup_database --dry-run --verbose

# Real backup
python manage.py backup_database --verbose
```

### Test via Celery

Trigger the backup task from Django shell:

```python
from apps.core.tasks import backup_database_task
result = backup_database_task.delay()
print(result.get())  # Wait for completion
```

### Check Celery Logs

On Render, check the **Celery Beat** logs to see when backups are scheduled:

```
[INFO/Beat] Scheduler: Starting...
[INFO/Beat] DatabaseScheduler: Schedule changed.
```

Check **Celery Worker** logs to see backup execution:

```
[INFO/ForkPoolWorker-1] Task apps.core.tasks.backup_database_task[...] succeeded
```

## Backup Schedule

The backup is scheduled to run **weekly on Sunday at 3:00 AM UTC**.

Configuration in [config/celery.py](../backend/config/celery.py):

```python
app.conf.beat_schedule = {
    "backup-database-weekly": {
        "task": "apps.core.tasks.backup_database_task",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
        "options": {"expires": 3600},  # Task expires after 1 hour
    },
}
```

To change the schedule, modify the `crontab` parameters:
- `day_of_week`: 0-6 (0=Sunday, 6=Saturday)
- `hour`: 0-23 (UTC timezone)
- `minute`: 0-59

## Backup Retention

By default, backups older than **90 days** are automatically deleted.

To change retention:

```bash
# Keep 30 days
python manage.py backup_database --retention-days=30

# Keep 1 year
python manage.py backup_database --retention-days=365

# Skip cleanup (keep all backups)
python manage.py backup_database --skip-cleanup
```

## Verifying Backup Integrity

### List Backups in S3

Using AWS CLI:

```bash
aws s3 ls s3://your-bucket-name/backups/database/
```

### Download and Test Restore

```bash
# Download backup
aws s3 cp s3://your-bucket/backups/database/backup_geoannotator_20250126_030000.sql.gz .

# Decompress
gunzip backup_geoannotator_20250126_030000.sql.gz

# Test restore (to a test database)
psql -U postgres -d test_db -f backup_geoannotator_20250126_030000.sql
```

## Support

If issues persist:

1. Check [Celery logs](./render-logs-guide.md) on Render
2. Verify all environment variables are set correctly
3. Test `pg_dump` connection manually:
   ```bash
   pg_dump "$BACKUP_DATABASE_URL" --version
   ```
4. Check Neon database is accessible:
   ```bash
   psql "$BACKUP_DATABASE_URL" -c "SELECT version();"
   ```

## Related Documentation

- [Deployment Guide - Render + Neon](./deployment-render-neon.md)
- [Celery Redis Setup](./celery-redis-setup.md)
- [Render Logs Guide](./render-logs-guide.md)
