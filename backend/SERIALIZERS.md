# GeoAnnotator Serializers Documentation

**Phase 3.4 Completed**: 2025-10-07
**Total Serializers**: 28 classes across 6 apps
**Total Lines of Code**: 1,330

---

## Overview

Django REST Framework serializers for all GeoAnnotator models. These serializers handle:
- JSON serialization/deserialization
- Input validation
- Business logic (permissions, quotas, file handling)
- OpenAPI contract compliance

---

## Authentication App (5 serializers)

**File**: `apps/authentication/serializers.py`

### UserSerializer
- **Purpose**: User profile with storage quota
- **Fields**: id, email, date_joined, storage_used, storage_limit, storage_percentage
- **OpenAPI**: Matches `User` schema

### RegisterSerializer
- **Purpose**: User registration with password validation
- **Validation**: Min 8 chars, uppercase, lowercase, numbers required
- **Creates**: User with 2GB default quota
- **OpenAPI**: Matches `RegisterRequest` schema

### LoginSerializer
- **Purpose**: Email/password authentication
- **Validation**: Authenticates user, checks active status
- **Returns**: User object (for token generation)
- **OpenAPI**: Matches `LoginRequest` schema

### TokenSerializer
- **Purpose**: JWT token response
- **Fields**: access (1h validity), refresh (7d validity), user profile
- **Method**: `get_tokens_for_user(user)` - generates JWT tokens
- **OpenAPI**: Matches `TokenResponse` schema

### RefreshTokenSerializer
- **Purpose**: Refresh token validation
- **Validation**: Checks token validity and expiration
- **OpenAPI**: Matches `RefreshRequest` schema

---

## Points App (7 serializers)

**File**: `apps/points/serializers.py`

### TagSerializer
- **Purpose**: Simple tag serialization
- **Fields**: id, name, created_at
- **OpenAPI**: Matches `Tag` schema

### UserSummarySerializer
- **Purpose**: Lightweight user reference (for nested relations)
- **Fields**: id, email
- **OpenAPI**: Matches `UserSummary` schema

### EditingLockSerializer
- **Purpose**: Show editing lock status
- **Fields**: locked_by (user), acquired_at, expires_at (calculated +15min)
- **OpenAPI**: Matches `EditingLock` schema

### GPSPointSerializer
- **Purpose**: Full GPS point with all relations
- **Fields**: id, title, description, location (GeoJSON), lat/lon, owner, tags, is_public, editing_lock, permission
- **Special**: Converts PostGIS Point ↔ lat/lon, calculates user permission level
- **OpenAPI**: Matches `GPSPoint` schema

### CreateGPSPointSerializer
- **Purpose**: Create point with auto-tag creation
- **Fields**: title, description, latitude, longitude, tags (names), is_public
- **Logic**: Creates PostGIS Point, auto-creates tags by name
- **OpenAPI**: Matches `CreateGPSPointRequest` schema

### UpdateGPSPointSerializer
- **Purpose**: Partial point updates
- **Fields**: Same as create (all optional)
- **Logic**: Updates location if lat/lon provided, replaces tags if provided
- **OpenAPI**: Matches `UpdateGPSPointRequest` schema

### GPSPointListSerializer
- **Purpose**: Lightweight list view (excludes heavy fields)
- **Fields**: id, title, lat/lon, owner, tags, is_public, timestamps, permission
- **Omits**: description, editing_lock details

---

## Annotations App (4 serializers)

**File**: `apps/annotations/serializers.py`

### AnnotationSerializer
- **Purpose**: Full annotation with polymorphic types
- **Types**: text, image, document, file
- **Fields**: id, gps_point, type, text_content, file, file_name, file_size, mime_type, can_preview, URLs
- **Validation**: Type-specific (text requires text_content, others require file)
- **Quota**: Validates file size (max 1GB) and user storage quota
- **URLs**: Generates download, preview, file URLs
- **OpenAPI**: Matches `Annotation` schema

### CreateTextAnnotationSerializer
- **Purpose**: Create text-only annotation
- **Fields**: gps_point, text_content
- **Logic**: Sets type='text' automatically

### CreateFileAnnotationSerializer
- **Purpose**: Create file annotation (image/document/file)
- **Fields**: gps_point, type, file
- **Validation**: File size (max 1GB), user quota check
- **Logic**: Updates user storage_used on success

### UpdateTextAnnotationSerializer
- **Purpose**: Edit text annotation content
- **Fields**: text_content
- **Validation**: Ensures annotation is type='text'

---

## Sharing App (4 serializers)

**File**: `apps/sharing/serializers.py`

### ShareSerializer
- **Purpose**: Full share details with invitation status
- **Fields**: id, gps_point, owner, recipient_email, recipient_user, permission_level, invitation_token, timestamps, invitation_status
- **Computed**: invitation_status (pending/accepted/expired based on 7-day expiry)
- **OpenAPI**: Matches `Share` schema

### CreateShareSerializer
- **Purpose**: Create share and send invitation
- **Fields**: gps_point, recipient_email, permission_level
- **Validation**: User has transfer permission, no self-share, no duplicates
- **Logic**: Generates invitation token, sets owner (original point owner)
- **TODO**: Send invitation email
- **OpenAPI**: Matches `CreateShareRequest` schema

### UpdateShareSerializer
- **Purpose**: Update permission level only
- **Fields**: permission_level
- **Validation**: User has transfer permission
- **OpenAPI**: Matches `UpdateShareRequest` schema

### AcceptShareSerializer
- **Purpose**: Accept invitation by token
- **Fields**: invitation_token
- **Validation**: Token exists, not expired (7 days), not already accepted
- **Logic**: Links share to user, sets accepted_at
- **OpenAPI**: Matches `AcceptShareRequest` schema

---

## Trash App (4 serializers)

**File**: `apps/trash/serializers.py`

### TrashSerializer
- **Purpose**: Trash item with deletion info
- **Fields**: id, gps_point, deleted_by, deleted_at, permanent_deletion_at, days_remaining, is_expired
- **OpenAPI**: Matches `Trash` schema

### RestoreTrashSerializer
- **Purpose**: Restore point from trash
- **Validation**: Not expired (<30 days), user is owner or deleter
- **Logic**: Calls `trash.restore()` - deletes trash entry, reactivates shares
- **OpenAPI**: Matches `RestoreTrashRequest` schema

### DeletePermanentlySerializer
- **Purpose**: Permanently delete point
- **Validation**: User is point owner
- **Logic**: Deletes point (cascades to annotations, shares, trash), reclaims quota

### EmptyTrashSerializer
- **Purpose**: Empty all trash for user
- **Logic**: Deletes all trashed points owned by user
- **Returns**: {"deleted_count": N}

---

## Export/Import App (4 serializers)

**File**: `apps/export_import/serializers.py`

### ExportRequestSerializer
- **Purpose**: Export parameters validation
- **Fields**: format (geojson/gpx/kml/csv/zip), point_ids (filter), include_annotations
- **Validation**: Format supported, point IDs exist and user has access
- **OpenAPI**: Matches `ExportRequest` schema

### ImportRequestSerializer
- **Purpose**: Import file validation
- **Fields**: format (geojson/gpx/kml/csv), file (upload), merge_strategy (create_new/skip/replace)
- **Validation**: Format supported, file size (max 100MB), extension matches format
- **OpenAPI**: Matches `ImportRequest` schema

### ImportResultSerializer
- **Purpose**: Import result summary
- **Fields**: total_points, imported_points, skipped_points, failed_points, errors (list)
- **OpenAPI**: Matches `ImportResult` schema

### ImportErrorSerializer
- **Purpose**: Individual import error
- **Fields**: line_number, error (code), message
- **OpenAPI**: Matches `ImportError` schema

---

## Key Features Implemented

### 1. **PostGIS Integration**
- Latitude/Longitude → PostGIS Point conversion
- GeoJSON format output
- Spatial validation (-90≤lat≤90, -180≤lon≤180)

### 2. **Storage Quota Management**
- File size validation (max 1GB per file)
- User quota check before upload
- Quota reclaim on file deletion

### 3. **Permission System**
- Dynamic permission calculation (owner/transfer/edit/view)
- Permission validation for shares and updates
- Cascade permission checks

### 4. **Invitation System**
- UUID token generation
- 7-day expiry validation
- Email-based invitations (TODO: email service)

### 5. **Polymorphic Annotations**
- Type-specific validation (text vs file)
- MIME type detection
- Preview URL generation for supported types

### 6. **Import Validation**
- Multi-format support (GeoJSON, GPX, KML, CSV)
- File size limits
- Extension validation

---

## OpenAPI Compliance

All serializers match their respective OpenAPI contract schemas:
- ✅ Authentication: `auth.yaml` (User, RegisterRequest, LoginRequest, TokenResponse, RefreshRequest)
- ✅ Points: `points.yaml` (GPSPoint, Tag, CreateGPSPointRequest, UpdateGPSPointRequest, EditingLock)
- ✅ Annotations: `annotations.yaml` (Annotation, CreateTextAnnotationRequest, CreateFileAnnotationRequest)
- ✅ Sharing: `sharing.yaml` (Share, CreateShareRequest, UpdateShareRequest, AcceptShareRequest)
- ✅ Trash: (Trash, RestoreTrashRequest)
- ✅ Export/Import: `export-import.yaml` (ExportRequest, ImportRequest, ImportResult, ImportError)

---

## Next Phase: Services (T052-T059)

The serializers are ready, but they reference services that need to be implemented:

1. **JWT Service**: Token generation and validation
2. **Editing Lock Service**: Acquire/release locks, auto-expiry (15min)
3. **Storage Quota Service**: Update quota on upload/delete
4. **Permission Service**: Check view/edit/transfer, cascade revoke
5. **Email Service**: Send invitation emails
6. **File Service**: Validate MIME types, resize images, generate thumbnails
7. **Export Service**: Generate GeoJSON, GPX, KML, CSV, ZIP files
8. **Import Service**: Parse formats, apply merge strategies

These services will be implemented in **Phase 3.5**.
