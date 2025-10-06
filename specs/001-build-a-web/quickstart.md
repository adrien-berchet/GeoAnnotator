# Quickstart Guide: Test Scenarios

**Created**: 2025-10-06
**Purpose**: Integration test scenarios and acceptance criteria for GeoAnnotator

---

## Overview

This document provides step-by-step test scenarios that demonstrate the complete functionality of GeoAnnotator. These scenarios map directly to the acceptance criteria in the specification and serve as the foundation for integration tests.

---

## Test Environment Setup

### Prerequisites
- PostgreSQL 15+ with PostGIS extension installed
- Python 3.11+ with Django 4.2+
- Node.js 18+ with npm/yarn
- SMTP server for email testing (or Mailhog for local dev)
- S3-compatible storage (MinIO for local dev) or local filesystem

### Database Setup
```bash
# Create database with PostGIS
createdb geoannotator_test
psql geoannotator_test -c "CREATE EXTENSION postgis;"

# Run migrations
python manage.py migrate
```

### Test Data
```bash
# Create test users
python manage.py createsuperuser --email admin@example.com
python manage.py create_test_users  # Creates alice@example.com, bob@example.com
```

---

## Scenario 1: User Registration and Authentication

**Acceptance Criteria**: FR-001 to FR-004 (User registration, login, profile, storage quota)

### Steps:

1. **Register New User**
   ```bash
   POST /api/v1/auth/register
   {
     "email": "alice@example.com",
     "password": "SecurePass123"
   }
   ```
   **Expected**:
   - Response 201 with JWT tokens (access + refresh)
   - User created with 2GB default storage quota
   - storage_used = 0, storage_limit = 2147483648

2. **Login with Valid Credentials**
   ```bash
   POST /api/v1/auth/login
   {
     "email": "alice@example.com",
     "password": "SecurePass123"
   }
   ```
   **Expected**:
   - Response 200 with JWT tokens
   - access token valid 1 hour, refresh token valid 7 days

3. **Get User Profile**
   ```bash
   GET /api/v1/auth/me
   Authorization: Bearer <access_token>
   ```
   **Expected**:
   - Response 200 with user profile
   - storage_percentage = (0 / 2147483648) * 100 = 0.0

4. **Refresh Access Token**
   ```bash
   POST /api/v1/auth/refresh
   {
     "refresh": "<refresh_token>"
   }
   ```
   **Expected**:
   - Response 200 with new access token

5. **Login with Invalid Credentials**
   ```bash
   POST /api/v1/auth/login
   {
     "email": "alice@example.com",
     "password": "WrongPassword"
   }
   ```
   **Expected**:
   - Response 401 with error "INVALID_CREDENTIALS"

---

## Scenario 2: GPS Point Creation and Management

**Acceptance Criteria**: FR-005 to FR-018 (Point CRUD, tagging, public/private)

### Steps:

1. **Create Private GPS Point**
   ```bash
   POST /api/v1/points
   Authorization: Bearer <alice_token>
   {
     "title": "My Secret Fishing Spot",
     "description": "<p>Great trout fishing 🎣</p>",
     "latitude": 45.5231,
     "longitude": -122.6765,
     "tags": ["fishing", "river"],
     "is_public": false
   }
   ```
   **Expected**:
   - Response 201 with created point
   - owner = alice@example.com
   - permission = "owner"
   - tags array contains 2 tags (auto-created if not exist)

2. **Create Public GPS Point**
   ```bash
   POST /api/v1/points
   Authorization: Bearer <alice_token>
   {
     "title": "Portland Japanese Garden",
     "description": "<p>Beautiful zen garden 🌸</p>",
     "latitude": 45.5195,
     "longitude": -122.7095,
     "tags": ["garden", "public"],
     "is_public": true
   }
   ```
   **Expected**:
   - Response 201 with created point
   - is_public = true

3. **List Alice's Points**
   ```bash
   GET /api/v1/points?visibility=owned
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with 2 points
   - Both owned by alice@example.com

4. **Search Points by Bounding Box**
   ```bash
   GET /api/v1/points?bbox=-122.8,45.4,-122.6,45.6
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with points within bounding box
   - Only includes owned, shared, or public points

5. **Filter Points by Tag**
   ```bash
   GET /api/v1/points?tags=fishing
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with 1 point (My Secret Fishing Spot)

6. **Full-Text Search**
   ```bash
   GET /api/v1/points?search=garden
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with 1 point (Portland Japanese Garden)

7. **Update GPS Point**
   ```bash
   PUT /api/v1/points/{point_id}
   Authorization: Bearer <alice_token>
   {
     "title": "My Updated Fishing Spot",
     "tags": ["fishing", "river", "trout"]
   }
   ```
   **Expected**:
   - Response 200 with updated point
   - editing_lock acquired automatically
   - tags array now has 3 tags

8. **Delete GPS Point (Move to Trash)**
   ```bash
   DELETE /api/v1/points/{point_id}
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 204
   - Point moved to trash (30-day retention)

---

## Scenario 3: Annotations (Text and Files)

**Acceptance Criteria**: FR-019 to FR-029 (Annotations, file uploads, quota)

### Steps:

1. **Add Text Annotation**
   ```bash
   POST /api/v1/points/{point_id}/annotations
   Authorization: Bearer <alice_token>
   Content-Type: application/json
   {
     "type": "text",
     "text_content": "<p>Caught a 5lb trout here yesterday! 🐟</p>"
   }
   ```
   **Expected**:
   - Response 201 with created annotation
   - type = "text", text_content contains HTML

2. **Upload Image Annotation**
   ```bash
   POST /api/v1/points/{point_id}/annotations
   Authorization: Bearer <alice_token>
   Content-Type: multipart/form-data

   type: image
   file: trout_photo.jpg (2MB)
   ```
   **Expected**:
   - Response 201 with created annotation
   - type = "image", can_preview = true
   - User's storage_used updated: 0 + 2097152 = 2097152 bytes

3. **Upload Document Annotation**
   ```bash
   POST /api/v1/points/{point_id}/annotations
   Authorization: Bearer <alice_token>
   Content-Type: multipart/form-data

   type: document
   file: fishing_license.pdf (500KB)
   ```
   **Expected**:
   - Response 201 with created annotation
   - type = "document", can_preview = true (PDF)
   - User's storage_used updated: 2097152 + 512000 = 2609152 bytes

4. **Upload File Exceeding Quota**
   ```bash
   POST /api/v1/points/{point_id}/annotations
   Authorization: Bearer <alice_token>
   Content-Type: multipart/form-data

   type: file
   file: large_video.mp4 (2.5GB)
   ```
   **Expected**:
   - Response 403 with error "QUOTA_EXCEEDED"
   - Details: storage_used + file_size > storage_limit

5. **Upload Invalid File Type**
   ```bash
   POST /api/v1/points/{point_id}/annotations
   Authorization: Bearer <alice_token>
   Content-Type: multipart/form-data

   type: file
   file: malware.exe (1KB)
   ```
   **Expected**:
   - Response 400 with error "INVALID_FILE_TYPE"
   - MIME type application/x-executable rejected

6. **List Point's Annotations**
   ```bash
   GET /api/v1/points/{point_id}/annotations
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with 3 annotations (1 text, 1 image, 1 document)

7. **Download File Annotation**
   ```bash
   GET /api/v1/annotations/{annotation_id}/download
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with file content (or 302 redirect to S3 signed URL)
   - Content-Disposition: attachment; filename="trout_photo.jpg"

8. **Preview Image Annotation**
   ```bash
   GET /api/v1/annotations/{annotation_id}/preview
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with resized image (max 1920x1080)
   - Content-Type: image/jpeg

9. **Update Text Annotation**
   ```bash
   PUT /api/v1/points/{point_id}/annotations/{annotation_id}
   Authorization: Bearer <alice_token>
   {
     "text_content": "<p>Updated: Caught a 7lb trout! 🐟🏆</p>"
   }
   ```
   **Expected**:
   - Response 200 with updated annotation

10. **Delete File Annotation (Quota Reclaim)**
    ```bash
    DELETE /api/v1/points/{point_id}/annotations/{image_annotation_id}
    Authorization: Bearer <alice_token>
    ```
    **Expected**:
    - Response 204
    - User's storage_used updated: 2609152 - 2097152 = 512000 bytes
    - File deleted from storage

---

## Scenario 4: Sharing and Permissions

**Acceptance Criteria**: FR-030 to FR-045 (Sharing, permissions, invitations)

### Steps:

1. **Share Point with View Permission**
   ```bash
   POST /api/v1/points/{point_id}/shares
   Authorization: Bearer <alice_token>
   {
     "recipient_email": "bob@example.com",
     "permission_level": "view"
   }
   ```
   **Expected**:
   - Response 201 with created share
   - Invitation email sent to bob@example.com with acceptance link
   - invitation_status = "pending", invitation_token generated

2. **Accept Share Invitation**
   ```bash
   POST /api/v1/shares/accept/{invitation_token}
   Authorization: Bearer <bob_token>
   ```
   **Expected**:
   - Response 200 with accepted share
   - accepted_at timestamp set, recipient_user = bob@example.com
   - invitation_status = "accepted"

3. **Bob Views Shared Point**
   ```bash
   GET /api/v1/points/{point_id}
   Authorization: Bearer <bob_token>
   ```
   **Expected**:
   - Response 200 with point details
   - permission = "view" (Bob cannot edit)

4. **Bob Attempts to Edit Shared Point (Denied)**
   ```bash
   PUT /api/v1/points/{point_id}
   Authorization: Bearer <bob_token>
   {
     "title": "Bob's Update"
   }
   ```
   **Expected**:
   - Response 403 with error "ACCESS_DENIED"
   - message: "No edit permission for this point"

5. **Alice Updates Share to Edit Permission**
   ```bash
   PATCH /api/v1/shares/{share_id}
   Authorization: Bearer <alice_token>
   {
     "permission_level": "edit"
   }
   ```
   **Expected**:
   - Response 200 with updated share
   - permission_level = "edit"

6. **Bob Edits Shared Point (Allowed)**
   ```bash
   PUT /api/v1/points/{point_id}
   Authorization: Bearer <bob_token>
   {
     "title": "Bob's Fishing Spot Too"
   }
   ```
   **Expected**:
   - Response 200 with updated point
   - editing_lock acquired by bob@example.com

7. **Alice Attempts to Edit While Bob Holds Lock**
   ```bash
   PUT /api/v1/points/{point_id}
   Authorization: Bearer <alice_token>
   {
     "title": "Alice's Update"
   }
   ```
   **Expected**:
   - Response 409 with error "POINT_LOCKED"
   - Details: locked_by = bob@example.com, lock_expires_at shown

8. **Bob Releases Lock**
   ```bash
   DELETE /api/v1/points/{point_id}/lock
   Authorization: Bearer <bob_token>
   ```
   **Expected**:
   - Response 204
   - Lock released

9. **Alice Upgrades Bob to Transfer Permission**
   ```bash
   PATCH /api/v1/shares/{share_id}
   Authorization: Bearer <alice_token>
   {
     "permission_level": "transfer"
   }
   ```
   **Expected**:
   - Response 200 with updated share
   - permission_level = "transfer"

10. **Bob Shares Point with Charlie**
    ```bash
    POST /api/v1/points/{point_id}/shares
    Authorization: Bearer <bob_token>
    {
      "recipient_email": "charlie@example.com",
      "permission_level": "view"
    }
    ```
    **Expected**:
    - Response 201 with created share
    - owner = alice@example.com (original owner tracked)

11. **Alice Revokes Bob's Share (Cascade)**
    ```bash
    DELETE /api/v1/shares/{bob_share_id}
    Authorization: Bearer <alice_token>
    ```
    **Expected**:
    - Response 204
    - Bob's share deleted, Charlie's share also deleted (cascade)

12. **Share Point with Non-Registered Email**
    ```bash
    POST /api/v1/points/{point_id}/shares
    Authorization: Bearer <alice_token>
    {
      "recipient_email": "newuser@example.com",
      "permission_level": "view"
    }
    ```
    **Expected**:
    - Response 201 with created share
    - recipient_user = null, invitation sent to newuser@example.com

---

## Scenario 5: Import/Export

**Acceptance Criteria**: FR-046 to FR-055 (Import/export, multi-format support)

### Steps:

1. **Export Points as GeoJSON**
   ```bash
   POST /api/v1/export
   Authorization: Bearer <alice_token>
   {
     "format": "geojson",
     "include_annotations": false
   }
   ```
   **Expected**:
   - Response 200 with GeoJSON FeatureCollection
   - Content-Disposition: attachment; filename="geoannotator_export_20250106_143000.geojson"

2. **Export Specific Points as GPX**
   ```bash
   POST /api/v1/export
   Authorization: Bearer <alice_token>
   {
     "format": "gpx",
     "point_ids": ["{point1_id}", "{point2_id}"]
   }
   ```
   **Expected**:
   - Response 200 with GPX XML file
   - Contains only specified points

3. **Export Full Bundle as ZIP**
   ```bash
   POST /api/v1/export
   Authorization: Bearer <alice_token>
   {
     "format": "zip"
   }
   ```
   **Expected**:
   - Response 200 with ZIP archive
   - Contains: points.geojson + annotations/ directory with all files

4. **Import GeoJSON File**
   ```bash
   POST /api/v1/import
   Authorization: Bearer <alice_token>
   Content-Type: multipart/form-data

   format: geojson
   file: exported_points.geojson
   merge_strategy: create_new
   ```
   **Expected**:
   - Response 200 with import result
   - total_points = N, imported_points = N, skipped_points = 0, failed_points = 0

5. **Import CSV with Validation Errors**
   ```bash
   POST /api/v1/import
   Authorization: Bearer <alice_token>
   Content-Type: multipart/form-data

   format: csv
   file: points_with_errors.csv
   merge_strategy: skip
   ```
   CSV Content:
   ```
   latitude,longitude,title,description,tags
   45.5231,-122.6765,"Valid Point","Description","tag1|tag2"
   99.0000,-122.6765,"Invalid Lat","Bad coordinates","tag3"
   45.5195,,"Missing Lon","No longitude",
   ```
   **Expected**:
   - Response 200 with import result
   - total_points = 3, imported_points = 1, failed_points = 2
   - errors array contains:
     - {line_number: 2, error: "INVALID_COORDINATES", message: "Latitude out of range"}
     - {line_number: 3, error: "MISSING_LONGITUDE", message: "Longitude required"}

6. **Import with Duplicate Detection**
   ```bash
   POST /api/v1/import
   Authorization: Bearer <alice_token>
   Content-Type: multipart/form-data

   format: geojson
   file: duplicate_points.geojson
   merge_strategy: skip
   ```
   **Expected**:
   - Response 200 with import result
   - skipped_points > 0 (duplicates at same coordinates)

---

## Scenario 6: Trash and Restoration

**Acceptance Criteria**: FR-056 to FR-062 (Trash, 30-day retention, restoration)

### Steps:

1. **Delete Point (Move to Trash)**
   ```bash
   DELETE /api/v1/points/{point_id}
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 204
   - Trash entry created with permanent_deletion_at = deleted_at + 30 days
   - All shares set is_active = false

2. **List Trashed Points**
   ```bash
   GET /api/v1/trash
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with trash items
   - days_remaining = 30 (for newly deleted point)

3. **Restore Point from Trash**
   ```bash
   POST /api/v1/trash/{point_id}/restore
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with restored point
   - Trash entry deleted, shares reactivated (is_active = true)

4. **Permanently Delete Point**
   ```bash
   DELETE /api/v1/trash/{point_id}/permanent
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 204
   - Point, annotations, shares permanently deleted
   - User's storage_used updated (reclaim all annotation file sizes)

5. **Empty Entire Trash**
   ```bash
   DELETE /api/v1/trash/empty
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with {deleted_count: N}
   - All trashed points permanently deleted

6. **Attempt to Restore Expired Point (>30 days)**
   ```bash
   # (Manually set deleted_at to 31 days ago in database)
   POST /api/v1/trash/{expired_point_id}/restore
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 410 with error "PERMANENTLY_DELETED"

---

## Scenario 7: Public Point Browsing

**Acceptance Criteria**: FR-063 to FR-068 (Public points, anonymous browsing)

### Steps:

1. **Alice Creates Public Point**
   ```bash
   POST /api/v1/points
   Authorization: Bearer <alice_token>
   {
     "title": "Public Trail",
     "latitude": 45.5000,
     "longitude": -122.7000,
     "is_public": true
   }
   ```
   **Expected**:
   - Response 201 with created point
   - is_public = true

2. **Bob Browses Public Points**
   ```bash
   GET /api/v1/points?visibility=public
   Authorization: Bearer <bob_token>
   ```
   **Expected**:
   - Response 200 with public points
   - Includes Alice's public point, excludes her private points

3. **Bob Views Public Point Details**
   ```bash
   GET /api/v1/points/{public_point_id}
   Authorization: Bearer <bob_token>
   ```
   **Expected**:
   - Response 200 with point details
   - permission = "view" (Bob cannot edit public points he doesn't own)

4. **Bob Cannot Edit Public Point**
   ```bash
   PUT /api/v1/points/{public_point_id}
   Authorization: Bearer <bob_token>
   {
     "title": "Bob's Update"
   }
   ```
   **Expected**:
   - Response 403 with error "ACCESS_DENIED"

5. **Anonymous User Browses Public Points (if implemented)**
   ```bash
   GET /api/v1/points?visibility=public
   # No Authorization header
   ```
   **Expected**:
   - Response 200 with public points (if anonymous access enabled)
   - OR Response 401 (if authentication required)

---

## Scenario 8: Editing Locks and Concurrency

**Acceptance Criteria**: FR-069 to FR-073 (Editing locks, auto-release)

### Steps:

1. **Alice Acquires Lock**
   ```bash
   POST /api/v1/points/{point_id}/lock
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 200 with editing_lock
   - acquired_at = now, expires_at = now + 15 minutes

2. **Bob Attempts to Acquire Lock (Conflict)**
   ```bash
   POST /api/v1/points/{point_id}/lock
   Authorization: Bearer <bob_token>
   ```
   **Expected**:
   - Response 409 with error "POINT_LOCKED"
   - Details: locked_by = alice@example.com

3. **Alice Edits Point (Auto-Refresh Lock)**
   ```bash
   PUT /api/v1/points/{point_id}
   Authorization: Bearer <alice_token>
   {
     "title": "Updated Title"
   }
   ```
   **Expected**:
   - Response 200 with updated point
   - editing_lock.acquired_at refreshed to now

4. **Wait 15 Minutes (Lock Expires)**
   ```bash
   # Simulate 15 minutes passing (or manually update acquired_at in DB)
   POST /api/v1/points/{point_id}/lock
   Authorization: Bearer <bob_token>
   ```
   **Expected**:
   - Response 200 with new lock acquired by Bob
   - Alice's expired lock auto-released

5. **Alice Manually Releases Lock**
   ```bash
   DELETE /api/v1/points/{point_id}/lock
   Authorization: Bearer <alice_token>
   ```
   **Expected**:
   - Response 204
   - editing_lock = null

---

## Performance Verification

### Load Testing Scenarios

1. **Map Viewport Query Performance**
   ```bash
   # Query 1000 points in viewport
   GET /api/v1/points?bbox=-123.0,45.0,-122.0,46.0
   ```
   **Expected**:
   - p95 response time < 200ms
   - Uses PostGIS spatial index

2. **Point Clustering Performance**
   ```bash
   # Cluster 10,000 points
   GET /api/v1/points?bbox=-180,-90,180,90&cluster=true
   ```
   **Expected**:
   - p95 response time < 500ms
   - Uses PostGIS ST_ClusterKMeans or client-side Leaflet clustering

3. **File Upload Performance**
   ```bash
   # Upload 100MB file
   POST /api/v1/points/{point_id}/annotations
   Content-Type: multipart/form-data
   file: large_image.tiff (100MB)
   ```
   **Expected**:
   - Upload completes within 30s on 10Mbps connection
   - Progress tracking via chunked upload

4. **Export Performance**
   ```bash
   # Export 5,000 points as GeoJSON
   POST /api/v1/export
   {
     "format": "geojson"
   }
   ```
   **Expected**:
   - Export completes within 10s
   - Uses streaming response for large datasets

---

## Next Steps

After completing these test scenarios:

1. **Automate Tests**: Convert scenarios to pytest integration tests
2. **CI/CD Integration**: Run tests on every commit (GitHub Actions)
3. **Performance Monitoring**: Track response times with application monitoring (e.g., Sentry)
4. **Load Testing**: Use Locust or k6 to simulate 100+ concurrent users
5. **End-to-End Tests**: Convert scenarios to Playwright E2E tests

---

**Ready for Phase 2**: Generate tasks.md with TDD-ordered implementation tasks.
