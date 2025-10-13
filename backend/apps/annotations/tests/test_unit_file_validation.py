"""
Unit tests for file MIME type validation.

Tests the FileUploadService validation logic for various file types.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.annotations.services import FileUploadService


class TestFileUploadValidation:
    """Test file upload validation."""

    def test_validate_image_jpeg(self):
        """Test JPEG image validation passes."""
        file = SimpleUploadedFile(
            "test.jpg",
            b"fake jpeg content",
            content_type="image/jpeg"
        )

        result = FileUploadService.validate_file(file, 'image')

        assert result['valid'] is True
        assert result['mime_type'] == 'image/jpeg'
        assert result['file_size'] == len(b"fake jpeg content")

    def test_validate_image_png(self):
        """Test PNG image validation passes."""
        file = SimpleUploadedFile(
            "test.png",
            b"fake png content",
            content_type="image/png"
        )

        result = FileUploadService.validate_file(file, 'image')

        assert result['valid'] is True
        assert result['mime_type'] == 'image/png'

    def test_validate_image_gif(self):
        """Test GIF image validation passes."""
        file = SimpleUploadedFile(
            "test.gif",
            b"fake gif content",
            content_type="image/gif"
        )

        result = FileUploadService.validate_file(file, 'image')

        assert result['valid'] is True
        assert result['mime_type'] == 'image/gif'

    def test_validate_image_webp(self):
        """Test WebP image validation passes."""
        file = SimpleUploadedFile(
            "test.webp",
            b"fake webp content",
            content_type="image/webp"
        )

        result = FileUploadService.validate_file(file, 'image')

        assert result['valid'] is True
        assert result['mime_type'] == 'image/webp'

    def test_validate_document_pdf(self):
        """Test PDF document validation passes."""
        file = SimpleUploadedFile(
            "test.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )

        result = FileUploadService.validate_file(file, 'document')

        assert result['valid'] is True
        assert result['mime_type'] == 'application/pdf'

    def test_validate_document_docx(self):
        """Test DOCX document validation passes."""
        file = SimpleUploadedFile(
            "test.docx",
            b"fake docx content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        result = FileUploadService.validate_file(file, 'document')

        assert result['valid'] is True
        assert result['mime_type'] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_validate_document_txt(self):
        """Test TXT document validation passes."""
        file = SimpleUploadedFile(
            "test.txt",
            b"fake text content",
            content_type="text/plain"
        )

        result = FileUploadService.validate_file(file, 'document')

        assert result['valid'] is True
        assert result['mime_type'] == 'text/plain'

    def test_validate_document_csv(self):
        """Test CSV document validation passes."""
        file = SimpleUploadedFile(
            "test.csv",
            b"fake csv content",
            content_type="text/csv"
        )

        result = FileUploadService.validate_file(file, 'document')

        assert result['valid'] is True
        assert result['mime_type'] == 'text/csv'

    def test_validate_image_wrong_type(self):
        """Test image validation fails for non-image."""
        file = SimpleUploadedFile(
            "test.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )

        result = FileUploadService.validate_file(file, 'image')

        assert result['valid'] is False
        assert 'Invalid image type' in result['error']

    def test_validate_document_wrong_type(self):
        """Test document validation fails for non-document."""
        file = SimpleUploadedFile(
            "test.jpg",
            b"fake jpeg content",
            content_type="image/jpeg"
        )

        result = FileUploadService.validate_file(file, 'document')

        assert result['valid'] is False
        assert 'Invalid document type' in result['error']

    def test_validate_file_too_large(self):
        """Test file size limit validation."""
        # Create a file larger than 1GB
        large_size = FileUploadService.MAX_FILE_SIZE + 1

        file = SimpleUploadedFile(
            "large.jpg",
            b"x",
            content_type="image/jpeg"
        )
        file.size = large_size

        result = FileUploadService.validate_file(file, 'image')

        assert result['valid'] is False
        assert 'exceeds maximum' in result['error']

    def test_validate_disallowed_executable(self):
        """Test executable files are rejected when content_type is set."""
        # Use a non-standard extension so mimetypes.guess_type returns None
        # This will force using content_type
        file = SimpleUploadedFile(
            "test.unknown_exe",
            b"fake executable",
            content_type="application/x-executable"
        )

        result = FileUploadService.validate_file(file, 'file')

        assert result['valid'] is False
        assert 'not allowed' in result['error']

    def test_validate_disallowed_script(self):
        """Test script files are rejected when content_type is set."""
        # Use a non-standard extension so mimetypes.guess_type returns None
        file = SimpleUploadedFile(
            "test.unknown_sh",
            b"#!/bin/bash",
            content_type="application/x-sh"
        )

        result = FileUploadService.validate_file(file, 'file')

        assert result['valid'] is False
        assert 'not allowed' in result['error']

    def test_validate_disallowed_javascript(self):
        """Test JavaScript files are rejected when content_type is set."""
        # Use a non-standard extension so mimetypes.guess_type returns None
        file = SimpleUploadedFile(
            "test.unknown_js",
            b"console.log('test');",
            content_type="application/javascript"
        )

        result = FileUploadService.validate_file(file, 'file')

        assert result['valid'] is False
        assert 'not allowed' in result['error']

    def test_validate_generic_file_type(self):
        """Test generic file type allows most files."""
        file = SimpleUploadedFile(
            "test.zip",
            b"fake zip content",
            content_type="application/zip"
        )

        result = FileUploadService.validate_file(file, 'file')

        assert result['valid'] is True
        assert result['mime_type'] == 'application/zip'

    def test_can_preview_image(self):
        """Test image types are previewable."""
        assert FileUploadService.can_preview('image/jpeg') is True
        assert FileUploadService.can_preview('image/png') is True
        assert FileUploadService.can_preview('image/gif') is True
        assert FileUploadService.can_preview('image/webp') is True

    def test_can_preview_pdf(self):
        """Test PDF is previewable."""
        assert FileUploadService.can_preview('application/pdf') is True

    def test_can_preview_non_previewable(self):
        """Test non-previewable types."""
        assert FileUploadService.can_preview('application/zip') is False
        assert FileUploadService.can_preview('text/plain') is False
        assert FileUploadService.can_preview('application/msword') is False

    def test_validate_mime_type_from_filename(self):
        """Test MIME type detection from filename when content_type is missing."""
        file = SimpleUploadedFile(
            "test.jpg",
            b"fake content"
        )
        # Clear content_type to force detection from filename
        file.content_type = None

        result = FileUploadService.validate_file(file, 'image')

        # Should still detect MIME type from extension
        assert result['valid'] is True
        assert 'image' in result['mime_type']

    def test_validate_file_size_edge_case_exact_limit(self):
        """Test file at exact size limit is allowed."""
        file = SimpleUploadedFile(
            "exact.jpg",
            b"x",
            content_type="image/jpeg"
        )
        file.size = FileUploadService.MAX_FILE_SIZE

        result = FileUploadService.validate_file(file, 'image')

        assert result['valid'] is True

    def test_validate_file_zero_size(self):
        """Test zero-size file is allowed (validation doesn't reject it)."""
        file = SimpleUploadedFile(
            "empty.jpg",
            b"",
            content_type="image/jpeg"
        )

        result = FileUploadService.validate_file(file, 'image')

        assert result['valid'] is True
        assert result['file_size'] == 0

    def test_validate_all_allowed_image_types(self):
        """Test all allowed image MIME types."""
        allowed_types = FileUploadService.ALLOWED_IMAGE_TYPES

        for mime_type in allowed_types:
            file = SimpleUploadedFile(
                f"test.{mime_type.split('/')[1]}",
                b"fake content",
                content_type=mime_type
            )

            result = FileUploadService.validate_file(file, 'image')

            assert result['valid'] is True, f"Failed for {mime_type}"
            assert result['mime_type'] == mime_type

    def test_validate_all_allowed_document_types(self):
        """Test all allowed document MIME types."""
        allowed_types = FileUploadService.ALLOWED_DOCUMENT_TYPES

        for mime_type in allowed_types:
            extension = mime_type.split('/')[-1].replace('+', '')
            file = SimpleUploadedFile(
                f"test.{extension}",
                b"fake content",
                content_type=mime_type
            )

            result = FileUploadService.validate_file(file, 'document')

            assert result['valid'] is True, f"Failed for {mime_type}"
            assert result['mime_type'] == mime_type

    def test_validate_all_disallowed_types(self):
        """Test all disallowed MIME types are rejected."""
        disallowed_types = FileUploadService.DISALLOWED_TYPES

        for mime_type in disallowed_types:
            file = SimpleUploadedFile(
                f"test.{mime_type.split('/')[-1]}",
                b"fake content",
                content_type=mime_type
            )

            result = FileUploadService.validate_file(file, 'file')

            assert result['valid'] is False, f"Should reject {mime_type}"
            assert 'not allowed' in result['error']
