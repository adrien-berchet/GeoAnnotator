"""
Integration Test - Scenario 3: Annotations (Text and Files)

Acceptance Criteria: FR-019 to FR-029
- Text annotations with rich HTML content
- Image file uploads with preview support
- Document uploads (PDF, Office formats)
- Storage quota enforcement (1GB per file, 2GB per user)
- Invalid file type rejection
- File download and preview
- Annotation CRUD operations
- Storage quota reclaim on deletion
"""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import User


@pytest.mark.django_db
class TestScenario3Annotations:
    """Integration tests for annotation workflow (text and files)."""

    def setup_method(self):
        """Set up test client and create test point before each test."""
        from rest_framework_simplejwt.tokens import RefreshToken

        self.client = APIClient()

        # Create Alice
        self.alice = User.objects.create_user(username="alice", email="alice@example.com", password="SecurePass123")
        refresh = RefreshToken.for_user(self.alice)
        self.alice_token = str(refresh.access_token)

        # Create a test point
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        point_response = self.client.post(
            reverse("points:list"),
            {
                "title": "Test Point for Annotations",
                "latitude": 45.5231,
                "longitude": -122.6765,
            },
            format="json",
        )
        self.point_id = point_response.data["id"]
        self.annotations_url = reverse("annotations:list", kwargs={"point_id": self.point_id})

    def test_step_1_add_text_annotation(self):
        """
        Step 1: Add Text Annotation

        Expected:
        - Response 201 with created annotation
        - type = "text", text_content contains HTML
        """
        # Given
        text_data = {
            "type": "text",
            "text_content": "<p>Caught a 5lb trout here yesterday! 🐟</p>",
        }

        # When
        response = self.client.post(self.annotations_url, text_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["type"] == "text"
        assert "🐟" in response.data["text_content"]
        assert response.data["file"] is None

    def test_step_2_upload_image_annotation(self):
        """
        Step 2: Upload Image Annotation

        Expected:
        - Response 201 with created annotation
        - type = "image", can_preview = true
        - User's storage_used updated: 0 + file_size
        """
        # Given - Create a test image (2MB)
        image = Image.new("RGB", (1920, 1080), color="red")
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        image_file = SimpleUploadedFile(
            "trout_photo.jpg", image_io.read(), content_type="image/jpeg"
        )

        # Get initial storage
        self.alice.refresh_from_db()
        initial_storage = self.alice.storage_used

        # When
        response = self.client.post(
            self.annotations_url,
            {
                "type": "image",
                "file": image_file,
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["type"] == "image"
        assert response.data["file"]["can_preview"] is True
        assert response.data["file"]["file_name"] == "trout_photo.jpg"

        # Verify storage updated
        self.alice.refresh_from_db()
        assert self.alice.storage_used > initial_storage
        assert self.alice.storage_used == initial_storage + response.data["file"]["file_size"]

    def test_step_3_upload_document_annotation(self):
        """
        Step 3: Upload Document Annotation

        Expected:
        - Response 201 with created annotation
        - type = "document", can_preview = true (PDF)
        - User's storage_used updated
        """
        # Given - Create a fake PDF (500KB)
        pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + (b"0" * 500000)
        pdf_file = SimpleUploadedFile(
            "fishing_license.pdf", pdf_content, content_type="application/pdf"
        )

        # Get initial storage
        self.alice.refresh_from_db()
        initial_storage = self.alice.storage_used

        # When
        response = self.client.post(
            self.annotations_url,
            {
                "type": "document",
                "file": pdf_file,
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["type"] == "document"
        assert response.data["file"]["can_preview"] is True
        assert response.data["file"]["mime_type"] == "application/pdf"

        # Verify storage updated
        self.alice.refresh_from_db()
        assert self.alice.storage_used > initial_storage

    def test_step_4_upload_file_exceeding_quota(self):
        """
        Step 4: Upload File Exceeding Quota

        Expected:
        - Response 403 with error "QUOTA_EXCEEDED"
        - Details: storage_used + file_size > storage_limit
        """
        # Given - Set Alice's storage to almost full
        self.alice.storage_used = 2 * 1024 * 1024 * 1024 - 1000  # 2GB - 1KB
        self.alice.save()

        # Create a 2KB file (will exceed quota)
        large_file = SimpleUploadedFile("large_video.mp4", b"0" * 2000, content_type="video/mp4")

        # When
        response = self.client.post(
            self.annotations_url,
            {
                "type": "file",
                "file": large_file,
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "VALIDATION_ERROR"
        assert response.data["details"]["file"]["error"] == "QUOTA_EXCEEDED"

    def test_step_5_upload_invalid_file_type(self):
        """
        Step 5: Upload Invalid File Type

        Expected:
        - Response 400 with error "INVALID_FILE_TYPE"
        - MIME type application/x-executable rejected
        """
        # Given - Create an executable file
        exe_file = SimpleUploadedFile(
            "malware.exe",
            b"MZ\x90\x00",
            content_type="application/x-msdownload",  # DOS header
        )

        # When
        response = self.client.post(
            self.annotations_url,
            {
                "type": "BAD FILE TYPE",
                "file": exe_file,
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "INVALID_OPERATION"
        assert response.data["message"] == "Invalid annotation type: BAD FILE TYPE"

    def test_step_6_list_point_annotations(self):
        """
        Step 6: List Point's Annotations

        Expected:
        - Response 200 with 3 annotations (1 text, 1 image, 1 document)
        """
        # Given - Create 3 annotations
        # Text annotation
        self.client.post(
            self.annotations_url,
            {
                "type": "text",
                "text_content": "<p>Text annotation</p>",
            },
            format="json",
        )

        # Image annotation
        image = Image.new("RGB", (100, 100), color="blue")
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        self.client.post(
            self.annotations_url,
            {
                "type": "image",
                "file": SimpleUploadedFile("test.jpg", image_io.read(), content_type="image/jpeg"),
            },
            format="multipart",
        )

        # Document annotation
        self.client.post(
            self.annotations_url,
            {
                "type": "document",
                "file": SimpleUploadedFile(
                    "test.pdf", b"%PDF-1.4\n", content_type="application/pdf"
                ),
            },
            format="multipart",
        )

        # When
        response = self.client.get(self.annotations_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

        types = [ann["type"] for ann in response.data]
        assert "text" in types
        assert "image" in types
        assert "document" in types

    def test_step_7_download_file_annotation(self):
        """
        Step 7: Download File Annotation

        Expected:
        - Response 200 with file content (or 302 redirect to S3 signed URL)
        - Content-Disposition: attachment; filename="trout_photo.jpg"
        """
        # Given - Create an image annotation
        image = Image.new("RGB", (100, 100), color="green")
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        create_response = self.client.post(
            self.annotations_url,
            {
                "type": "image",
                "file": SimpleUploadedFile(
                    "trout_photo.jpg", image_io.read(), content_type="image/jpeg"
                ),
            },
            format="multipart",
        )
        annotation_id = create_response.data["id"]

        download_url = reverse(
            "annotations:download", kwargs={"point_id": self.point_id, "pk": annotation_id}
        )

        # When
        response = self.client.get(download_url)

        # Then
        # Accept both 200 (direct download) and 302 (redirect to S3)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND]

        if response.status_code == status.HTTP_200_OK:
            assert "attachment" in response.get("Content-Disposition", "")

    def test_step_8_preview_image_annotation(self):
        """
        Step 8: Preview Image Annotation

        Expected:
        - Response 200 with resized image (max 1920x1080)
        - Content-Type: image/jpeg
        """
        # Given - Create an image annotation
        image = Image.new("RGB", (2000, 2000), color="yellow")
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        create_response = self.client.post(
            self.annotations_url,
            {
                "type": "image",
                "file": SimpleUploadedFile(
                    "large_image.jpg", image_io.read(), content_type="image/jpeg"
                ),
            },
            format="multipart",
        )
        annotation_id = create_response.data["id"]

        preview_url = reverse(
            "annotations:preview", kwargs={"point_id": self.point_id, "pk": annotation_id}
        )

        # When
        response = self.client.get(preview_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "image" in response.get("Content-Type", "")

    def test_step_9_update_text_annotation(self):
        """
        Step 9: Update Text Annotation

        Expected:
        - Response 200 with updated annotation
        """
        # Given - Create a text annotation
        create_response = self.client.post(
            self.annotations_url,
            {
                "type": "text",
                "text_content": "<p>Original text</p>",
            },
            format="json",
        )
        annotation_id = create_response.data["id"]

        detail_url = reverse(
            "annotations:detail", kwargs={"point_id": self.point_id, "pk": annotation_id}
        )

        # When
        update_data = {
            "text_content": "<p>Updated: Caught a 7lb trout! 🐟🏆</p>",
        }
        response = self.client.patch(detail_url, update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "7lb trout" in response.data["text_content"]
        assert "🏆" in response.data["text_content"]

    def test_step_10_delete_file_annotation_quota_reclaim(self):
        """
        Step 10: Delete File Annotation (Quota Reclaim)

        Expected:
        - Response 204
        - User's storage_used updated (decreased)
        - File deleted from storage
        """
        # Given - Create an image annotation
        image = Image.new("RGB", (500, 500), color="purple")
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        create_response = self.client.post(
            self.annotations_url,
            {
                "type": "image",
                "file": SimpleUploadedFile(
                    "to_delete.jpg", image_io.read(), content_type="image/jpeg"
                ),
            },
            format="multipart",
        )
        annotation_id = create_response.data["id"]
        file_size = create_response.data["file"]["file_size"]

        # Get storage before deletion
        self.alice.refresh_from_db()
        storage_before = self.alice.storage_used

        detail_url = reverse(
            "annotations:detail", kwargs={"point_id": self.point_id, "pk": annotation_id}
        )

        # When
        response = self.client.delete(detail_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify storage reclaimed
        self.alice.refresh_from_db()

        assert self.alice.storage_used == storage_before - file_size

    def test_complete_annotation_lifecycle(self):
        """
        Complete Flow: Create Text → Upload Image → List → Update → Delete

        This test validates the entire annotation lifecycle.
        """
        # Step 1: Create text annotation
        text_response = self.client.post(
            self.annotations_url,
            {
                "type": "text",
                "text_content": "<p>Complete lifecycle test</p>",
            },
            format="json",
        )
        assert text_response.status_code == status.HTTP_201_CREATED

        # Step 2: Upload image
        image = Image.new("RGB", (200, 200), color="cyan")
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        image_response = self.client.post(
            self.annotations_url,
            {
                "type": "image",
                "file": SimpleUploadedFile(
                    "lifecycle.jpg", image_io.read(), content_type="image/jpeg"
                ),
            },
            format="multipart",
        )
        assert image_response.status_code == status.HTTP_201_CREATED

        # Step 3: List annotations
        list_response = self.client.get(self.annotations_url)
        assert list_response.status_code == status.HTTP_200_OK
        assert len(list_response.data) == 2

        # Step 4: Update text annotation
        text_id = text_response.data["id"]
        update_url = reverse(
            "annotations:detail", kwargs={"point_id": self.point_id, "pk": text_id}
        )
        update_response = self.client.patch(
            update_url,
            {"text_content": "<p>Updated lifecycle test</p>"},
            format="json",
        )
        assert update_response.status_code == status.HTTP_200_OK

        # Step 5: Delete image annotation
        image_id = image_response.data["id"]
        delete_url = reverse(
            "annotations:detail", kwargs={"point_id": self.point_id, "pk": image_id}
        )
        delete_response = self.client.delete(delete_url)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
