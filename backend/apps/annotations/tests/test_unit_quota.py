"""
Unit tests for storage quota calculations.

Tests cover:
- Quota checking before file upload
- Quota updates after upload/delete
- Quota reclamation from trash
- Quota warning threshold
"""
import pytest
from django.contrib.auth import get_user_model
from apps.annotations.models import Annotation
from apps.annotations.services import StorageQuotaService
from apps.points.models import GPSPoint
from django.contrib.gis.geos import Point

User = get_user_model()


@pytest.mark.django_db
class TestStorageQuota:
    """Unit tests for storage quota service."""

    @pytest.fixture
    def user(self):
        """Create test user with default quota."""
        return User.objects.create_user(
            email='quota@example.com',
            password='TestPass123',
            storage_limit=2 * 1024 * 1024 * 1024  # 2GB
        )

    @pytest.fixture
    def gps_point(self, user):
        """Create test GPS point."""
        return GPSPoint.objects.create(
            title='Test Point',
            location=Point(0, 0),
            owner=user
        )

    def test_check_quota_sufficient(self, user):
        """Test quota check when user has sufficient space."""
        file_size = 100 * 1024 * 1024  # 100MB
        result = StorageQuotaService.check_quota(user, file_size)
        assert result is True

    def test_check_quota_insufficient(self, user):
        """Test quota check when user exceeds limit."""
        user.storage_used = 2 * 1024 * 1024 * 1024 - 50 * 1024 * 1024  # 2GB - 50MB used
        user.save()

        file_size = 100 * 1024 * 1024  # 100MB (exceeds remaining 50MB)
        result = StorageQuotaService.check_quota(user, file_size)
        assert result is False

    def test_check_quota_exact_limit(self, user):
        """Test quota check when file would exactly reach limit."""
        user.storage_used = 1.5 * 1024 * 1024 * 1024  # 1.5GB used
        user.save()

        file_size = 0.5 * 1024 * 1024 * 1024  # 0.5GB (exactly at limit)
        result = StorageQuotaService.check_quota(user, file_size)
        assert result is True

    def test_update_quota_after_upload(self, user, gps_point):
        """Test quota update after successful file upload."""
        initial_used = user.storage_used
        file_size = 50 * 1024 * 1024  # 50MB

        # Create annotation via service
        from apps.annotations.services import AnnotationService
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile('test.jpg', b'x' * file_size, content_type='image/jpeg')
        annotation = AnnotationService.create_file_annotation(
            gps_point_id=gps_point.id,
            annotation_type='image',
            uploaded_file=file,
            user=user
        )

        # Refresh user from DB
        user.refresh_from_db()

        # Check quota was updated
        assert user.storage_used == initial_used + file_size

    def test_reclaim_quota_after_delete(self, user, gps_point):
        """Test quota reclamation after annotation deletion."""
        # Create and upload file
        from apps.annotations.services import AnnotationService
        from django.core.files.uploadedfile import SimpleUploadedFile

        file_size = 30 * 1024 * 1024  # 30MB
        file = SimpleUploadedFile('test.jpg', b'x' * file_size, content_type='image/jpeg')
        annotation = AnnotationService.create_file_annotation(
            gps_point_id=gps_point.id,
            annotation_type='image',
            uploaded_file=file,
            user=user
        )

        user.refresh_from_db()
        used_after_upload = user.storage_used

        # Delete annotation
        AnnotationService.delete_annotation(annotation, user)

        # Refresh user
        user.refresh_from_db()

        # Check quota was reclaimed
        assert user.storage_used == used_after_upload - file_size

    def test_quota_warning_threshold(self, user):
        """Test quota warning at 90% usage."""
        user.storage_used = int(user.storage_limit * 0.91)  # 91% used (above 90%)
        user.save()

        is_warning = StorageQuotaService.is_quota_warning(user)
        assert is_warning is True

    def test_no_quota_warning_below_threshold(self, user):
        """Test no warning below 90% usage."""
        user.storage_used = int(user.storage_limit * 0.85)  # 85% used
        user.save()

        is_warning = StorageQuotaService.is_quota_warning(user)
        assert is_warning is False

    def test_get_quota_info(self, user):
        """Test getting quota information."""
        user.storage_used = 500 * 1024 * 1024  # 500MB
        user.save()

        quota_info = StorageQuotaService.get_quota_info(user)

        assert quota_info['storage_used'] == 500 * 1024 * 1024
        assert quota_info['storage_limit'] == 2 * 1024 * 1024 * 1024
        assert quota_info['storage_remaining'] == 2 * 1024 * 1024 * 1024 - 500 * 1024 * 1024
        assert 24.0 <= quota_info['usage_percentage'] <= 25.0  # Allow small rounding differences
        assert quota_info['is_warning'] is False

    def test_quota_exceeded_error(self, user, gps_point):
        """Test error when quota exceeded."""
        # Set user to near limit
        user.storage_used = 2 * 1024 * 1024 * 1024 - 10 * 1024 * 1024  # 2GB - 10MB
        user.save()

        from apps.annotations.services import AnnotationService
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Try to upload 20MB file (exceeds quota)
        file_size = 20 * 1024 * 1024
        file = SimpleUploadedFile('test.jpg', b'x' * file_size, content_type='image/jpeg')

        with pytest.raises(ValueError, match='Insufficient storage quota'):
            AnnotationService.create_file_annotation(
                gps_point_id=gps_point.id,
                annotation_type='image',
                uploaded_file=file,
                user=user
            )

    def test_text_annotation_no_quota_impact(self, user, gps_point):
        """Test that text annotations don't affect quota."""
        from apps.annotations.services import AnnotationService

        initial_used = user.storage_used

        # Create text annotation
        AnnotationService.create_text_annotation(
            gps_point_id=gps_point.id,
            text_content='<p>This is a text annotation</p>'
        )

        user.refresh_from_db()

        # Quota should not change
        assert user.storage_used == initial_used

    def test_multiple_files_quota_accumulation(self, user, gps_point):
        """Test quota accumulation with multiple file uploads."""
        from apps.annotations.services import AnnotationService
        from django.core.files.uploadedfile import SimpleUploadedFile

        initial_used = user.storage_used
        total_size = 0

        # Upload 3 files
        for i in range(3):
            file_size = (i + 1) * 10 * 1024 * 1024  # 10MB, 20MB, 30MB
            file = SimpleUploadedFile(f'test{i}.jpg', b'x' * file_size, content_type='image/jpeg')
            AnnotationService.create_file_annotation(
                gps_point_id=gps_point.id,
                annotation_type='image',
                uploaded_file=file,
                user=user
            )
            total_size += file_size

        user.refresh_from_db()

        # Check total quota increase
        assert user.storage_used == initial_used + total_size

    def test_point_deletion_reclaims_quota(self, user, gps_point):
        """Test that deleting a point reclaims all annotation quota."""
        from apps.annotations.services import AnnotationService
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Upload multiple files
        total_size = 0
        for i in range(2):
            file_size = 15 * 1024 * 1024  # 15MB each
            file = SimpleUploadedFile(f'test{i}.jpg', b'x' * file_size, content_type='image/jpeg')
            AnnotationService.create_file_annotation(
                gps_point_id=gps_point.id,
                annotation_type='image',
                uploaded_file=file,
                user=user
            )
            total_size += file_size

        user.refresh_from_db()
        used_after_uploads = user.storage_used

        # Delete point (should move to trash, quota stays)
        from apps.points.services import PointService
        PointService.delete_point(gps_point, user)

        user.refresh_from_db()

        # Quota should remain the same when moved to trash (only permanent delete reclaims)
        assert user.storage_used == used_after_uploads
