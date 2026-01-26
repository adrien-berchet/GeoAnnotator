"""
Django management command: backup_database

Creates compressed PostgreSQL database backups and uploads them to S3.

Usage:
    python manage.py backup_database [options]

Options:
    --dry-run: Show what would be done without actually creating backup
    --verbose: Show detailed information during backup
    --retention-days: Number of days to keep backups (default: 90)
    --skip-cleanup: Skip cleanup of old backups

Scheduled Execution:
    Run this command weekly via Celery Beat (configured in config/celery.py)

Requirements:
    - postgresql-client (pg_dump) installed on the system
    - boto3 for S3 uploads
    - AWS credentials configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    - S3 bucket configured (AWS_STORAGE_BUCKET_NAME)

Important for Neon.tech and managed databases:
    If using Neon.tech or other managed PostgreSQL with connection pooling,
    set BACKUP_DATABASE_URL environment variable with the DIRECT connection URL
    (not the pooled connection URL). The pooler URL will cause "Control plane
    request failed" errors with pg_dump.

    Example:
        BACKUP_DATABASE_URL=postgresql://user:pass@ep-xxx.region.aws.neon.tech/db?sslmode=require&options=endpoint%3Dep-xxx

    If BACKUP_DATABASE_URL is not set, DATABASE_URL will be used instead.
"""

import gzip
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from datetime import timedelta
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to backup PostgreSQL database to S3.
    """

    help = "Create compressed PostgreSQL backup and upload to S3"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually creating backup",
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed information during backup process",
        )

        parser.add_argument(
            "--retention-days",
            type=int,
            default=90,
            help="Number of days to keep backups (default: 90)",
        )

        parser.add_argument(
            "--skip-cleanup",
            action="store_true",
            help="Skip cleanup of old backups",
        )

    def handle(self, *args, **options):
        """
        Execute the backup command.

        Args:
            options: Command options (dry_run, verbose, retention_days, skip_cleanup)
        """
        self.dry_run = options.get("dry_run", False)
        self.verbose = options.get("verbose", False)
        self.retention_days = options.get("retention_days", 90)
        self.skip_cleanup = options.get("skip_cleanup", False)

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE("PostgreSQL Database Backup"))
        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(f"Timestamp: {datetime.now().isoformat()}")
        self.stdout.write(f"Retention: {self.retention_days} days")

        if self.dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN MODE] No actual backup will be created"))

        try:
            # Step 1: Verify prerequisites
            self._verify_prerequisites()

            # Step 2: Get database configuration
            db_config = self._get_database_config()
            self._log_config(db_config)

            # Step 3: Create backup
            if not self.dry_run:
                backup_file = self._create_backup(db_config)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Backup created: {os.path.basename(backup_file)}")
                )
                self.stdout.write(f"  Size: {self._format_size(os.path.getsize(backup_file))}")

                # Step 4: Upload to S3
                s3_key = self._upload_to_s3(backup_file)
                self.stdout.write(self.style.SUCCESS(f"✓ Uploaded to S3: {s3_key}"))

                # Step 5: Cleanup temporary file
                os.remove(backup_file)
                self._log(f"Cleaned up temporary file: {backup_file}")

            # Step 6: Cleanup old backups
            if not self.skip_cleanup:
                deleted_count = self._cleanup_old_backups()
                if deleted_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Cleaned up {deleted_count} old backup(s)")
                    )
            else:
                self.stdout.write("Skipping cleanup of old backups")

            self.stdout.write(self.style.SUCCESS("\n✓ Backup completed successfully!"))

        except CommandError as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Backup failed: {e}"))
            raise
        except Exception as e:
            logger.exception("Unexpected error during backup")
            self.stdout.write(self.style.ERROR(f"\n✗ Unexpected error: {e}"))
            raise CommandError(f"Backup failed: {e}") from e

    def _verify_prerequisites(self):
        """Verify that required tools and configuration are available."""
        self._log("Verifying prerequisites...")

        # Check pg_dump
        try:
            result = subprocess.run(
                ["pg_dump", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            pg_version = result.stdout.strip()
            self._log(f"✓ {pg_version}")
        except FileNotFoundError:
            raise CommandError(
                "pg_dump not found. Please install postgresql-client: "
                "apt-get install postgresql-client"
            ) from None
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Error checking pg_dump: {e}") from e

        # Check S3 configuration
        if not hasattr(settings, "AWS_STORAGE_BUCKET_NAME") or not settings.AWS_STORAGE_BUCKET_NAME:
            raise CommandError(
                "AWS_STORAGE_BUCKET_NAME not configured. Please set it in your environment."
            )

        if not hasattr(settings, "AWS_ACCESS_KEY_ID") or not settings.AWS_ACCESS_KEY_ID:
            raise CommandError(
                "AWS_ACCESS_KEY_ID not configured. Please set it in your environment."
            )

        if not hasattr(settings, "AWS_SECRET_ACCESS_KEY") or not settings.AWS_SECRET_ACCESS_KEY:
            raise CommandError(
                "AWS_SECRET_ACCESS_KEY not configured. Please set it in your environment."
            )

        self._log("✓ S3 configuration found")

    def _get_database_config(self):
        """Extract database configuration from Django settings."""
        db_settings = settings.DATABASES["default"]

        # Use BACKUP_DATABASE_URL if available (direct connection for pg_dump)
        # This is needed for Neon.tech and other managed databases that use connection pooling
        # The pooler URL won't work with pg_dump, so we need the direct connection URL
        if "BACKUP_DATABASE_URL" in os.environ:
            database_url = os.environ["BACKUP_DATABASE_URL"]
            parsed = urlparse(database_url)

            return {
                "host": parsed.hostname,
                "port": parsed.port or 5432,
                "name": parsed.path.lstrip("/"),
                "user": parsed.username,
                "password": parsed.password,
                "url": database_url,  # Keep for pg_dump
            }

        # Handle DATABASE_URL if present (Neon, Heroku, etc.)
        if "DATABASE_URL" in os.environ:
            database_url = os.environ["DATABASE_URL"]
            parsed = urlparse(database_url)

            return {
                "host": parsed.hostname,
                "port": parsed.port or 5432,
                "name": parsed.path.lstrip("/"),
                "user": parsed.username,
                "password": parsed.password,
                "url": database_url,  # Keep for pg_dump
            }

        # Manual configuration
        return {
            "host": db_settings.get("HOST", "localhost"),
            "port": db_settings.get("PORT", 5432),
            "name": db_settings.get("NAME"),
            "user": db_settings.get("USER"),
            "password": db_settings.get("PASSWORD"),
        }

    def _log_config(self, db_config):
        """Log database configuration (sanitized)."""
        self._log(f"Database: {db_config['name']}")
        self._log(f"Host: {db_config['host']}")
        self._log(f"Port: {db_config['port']}")
        self._log(f"User: {db_config['user']}")

    def _create_backup(self, db_config):
        """
        Create a compressed PostgreSQL backup using pg_dump.

        Args:
            db_config: Database configuration dictionary

        Returns:
            str: Path to the created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{db_config['name']}_{timestamp}.sql.gz"

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="db_backup_")
        backup_path = os.path.join(temp_dir, backup_filename)

        self.stdout.write("Creating backup...")
        self._log(f"Backup file: {backup_path}")

        try:
            # Prepare pg_dump command
            # Use DATABASE_URL if available (simpler for managed databases)
            if "url" in db_config:
                cmd = ["pg_dump", db_config["url"]]
            else:
                cmd = [
                    "pg_dump",
                    "-h",
                    db_config["host"],
                    "-p",
                    str(db_config["port"]),
                    "-U",
                    db_config["user"],
                    "-d",
                    db_config["name"],
                    "--no-password",  # Use PGPASSWORD env var
                ]

            # Add common options
            cmd.extend(
                [
                    "--format=plain",  # Plain SQL format
                    "--no-owner",  # Don't include ownership commands
                    "--no-acl",  # Don't include access control commands
                    "--clean",  # Include DROP commands
                    "--if-exists",  # Use IF EXISTS with DROP
                ]
            )

            # Set environment for pg_dump
            env = os.environ.copy()
            if "url" not in db_config and db_config.get("password"):
                env["PGPASSWORD"] = db_config["password"]

            # Ensure SSL is required for managed databases (e.g., Neon)
            # This is required even when using individual connection parameters
            env["PGSSLMODE"] = "require"

            # Run pg_dump and compress on-the-fly
            self._log(f"Running: {' '.join(cmd[:-1])} [password hidden]")

            with gzip.open(backup_path, "wb") as gz_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                )

                # Stream output to gzip file
                for chunk in iter(lambda: process.stdout.read(8192), b""):
                    gz_file.write(chunk)

                # Wait for completion and check return code
                stderr_output = process.stderr.read().decode()
                return_code = process.wait()

                if return_code != 0:
                    raise CommandError(f"pg_dump failed: {stderr_output}")

                if stderr_output and self.verbose:
                    self.stdout.write(f"pg_dump warnings: {stderr_output}")

            return backup_path

        except Exception as e:
            # Cleanup on error
            if os.path.exists(backup_path):
                os.remove(backup_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise CommandError(f"Failed to create backup: {e}") from e

    def _upload_to_s3(self, backup_file):
        """
        Upload backup file to S3.

        Args:
            backup_file: Path to the backup file

        Returns:
            str: S3 key of the uploaded file
        """
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        s3_key = f"backups/database/{os.path.basename(backup_file)}"

        self.stdout.write(f"Uploading to S3: s3://{bucket_name}/{s3_key}")

        try:
            # Initialize S3 client
            s3_config = {
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                "region_name": getattr(settings, "AWS_S3_REGION_NAME", None),
            }

            # Add endpoint_url for MinIO or S3-compatible storage (local development)
            endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
            if endpoint_url:
                s3_config["endpoint_url"] = endpoint_url
                self._log(f"Using S3-compatible endpoint: {endpoint_url}")

            s3_client = boto3.client("s3", **s3_config)

            # Upload file
            file_size = os.path.getsize(backup_file)
            self._log(f"Uploading {self._format_size(file_size)}...")

            # Prepare upload arguments
            extra_args = {
                "Metadata": {
                    "backup-type": "database",
                    "created-at": datetime.now().isoformat(),
                    "database": connection.settings_dict.get("NAME", "unknown"),
                },
            }

            # Add AWS-specific features only for real S3 (not MinIO)
            if not endpoint_url:  # Using AWS S3
                extra_args["ServerSideEncryption"] = "AES256"  # Encrypt at rest
                extra_args["StorageClass"] = "STANDARD_IA"  # Infrequent Access (cheaper)
                self._log("Using AWS S3 storage optimizations (encryption, STANDARD_IA)")

            s3_client.upload_file(
                backup_file,
                bucket_name,
                s3_key,
                ExtraArgs=extra_args,
            )

            self._log("✓ Upload completed")
            return s3_key

        except ClientError as e:
            raise CommandError(f"Failed to upload to S3: {e}") from e

    def _cleanup_old_backups(self):
        """
        Delete backups older than retention period from S3.

        Returns:
            int: Number of backups deleted
        """
        if self.dry_run:
            self.stdout.write("[DRY RUN] Would cleanup old backups")
            return 0

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        prefix = "backups/database/"
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        self._log(f"Cleaning up backups older than {cutoff_date.date()}")

        try:
            # Initialize S3 client with same config as upload
            s3_config = {
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                "region_name": getattr(settings, "AWS_S3_REGION_NAME", None),
            }

            # Add endpoint_url for MinIO or S3-compatible storage
            endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
            if endpoint_url:
                s3_config["endpoint_url"] = endpoint_url

            s3_client = boto3.client("s3", **s3_config)

            # List all backups
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

            if "Contents" not in response:
                self._log("No backups found in S3")
                return 0

            deleted_count = 0
            for obj in response["Contents"]:
                # Check if backup is older than retention period
                if obj["LastModified"].replace(tzinfo=None) < cutoff_date:
                    key = obj["Key"]
                    size = obj["Size"]

                    if self.verbose:
                        self.stdout.write(
                            f"  Deleting: {key} "
                            f"(Modified: {obj['LastModified'].date()}, "
                            f"Size: {self._format_size(size)})"
                        )

                    s3_client.delete_object(Bucket=bucket_name, Key=key)
                    deleted_count += 1

            return deleted_count

        except ClientError as e:
            self.stdout.write(self.style.WARNING(f"Warning: Failed to cleanup old backups: {e}"))
            return 0

    def _log(self, message):
        """Log verbose messages."""
        if self.verbose:
            self.stdout.write(f"  {message}")

    def _format_size(self, bytes_size):
        """
        Format file size for display.

        Args:
            bytes_size: Size in bytes

        Returns:
            str: Formatted size (e.g., "1.5 MB")
        """
        if bytes_size == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(bytes_size)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"
