# GeoAnnotator API Documentation

**Version**: 1.0.0
**Base URL**: `/api/v1`
**Authentication**: JWT Bearer Token

## Table of Contents

1. [Authentication](#authentication)
2. [GPS Points](#gps-points)
3. [Annotations](#annotations)
4. [Sharing](#sharing)
5. [Export/Import](#exportimport)
6. [Trash](#trash)
7. [Error Codes](#error-codes)

---

## Authentication

All API endpoints (except registration and login) require JWT authentication.

### Register

Create a new user account.

**Endpoint**: `POST /auth/register/`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!"
}
```

**Response** (201 Created):
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "storage_used": 0,
    "storage_limit": 2147483648
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Validation Rules**:
- Email must be valid and unique
- Password minimum 8 characters
- Password must match confirmation

---

### Login

Authenticate and receive JWT tokens.

**Endpoint**: `POST /auth/login/`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "storage_used": 1048576,
    "storage_limit": 2147483648
  }
}
```

**Token Lifetimes**:
- Access token: 1 hour
- Refresh token: 7 days

---

### Refresh Token

Get a new access token using refresh token.

**Endpoint**: `POST /auth/refresh/`

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Logout

Invalidate refresh token (blacklist).

**Endpoint**: `POST /auth/logout/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (205 Reset Content)

---

### Get Profile

Get current user profile.

**Endpoint**: `GET /auth/me/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "storage_used": 1048576,
  "storage_limit": 2147483648,
  "quota_info": {
    "storage_used": 1048576,
    "storage_limit": 2147483648,
    "storage_remaining": 2146435072,
    "usage_percentage": 0.05,
    "is_warning": false
  }
}
```

---

## GPS Points

### List Points

Get all GPS points (owned + shared).

**Endpoint**: `GET /points/`

**Headers**: `Authorization: Bearer <access_token>`

**Query Parameters**:
- `bbox` (optional): Bounding box `min_lon,min_lat,max_lon,max_lat`
- `tags` (optional): Comma-separated tag names
- `search` (optional): Text search in title/description
- `is_public` (optional): `true` or `false`

**Example**: `GET /points/?bbox=-122.5,37.7,-122.3,37.9&tags=hike,photo`

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "title": "Golden Gate Bridge",
    "description": "<p>Beautiful view of the bridge</p>",
    "latitude": 37.8199,
    "longitude": -122.4783,
    "is_public": true,
    "owner": {
      "id": "uuid",
      "email": "user@example.com"
    },
    "tags": [
      {"id": "uuid", "name": "landmark"},
      {"id": "uuid", "name": "photo"}
    ],
    "annotation_count": 5,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:45:00Z",
    "editing_lock_user": null,
    "editing_lock_acquired_at": null
  }
]
```

---

### Create Point

Create a new GPS point.

**Endpoint**: `POST /points/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "title": "Sunset Point",
  "description": "<p>Great spot for sunset photos</p>",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "is_public": false,
  "tags": ["sunset", "photography"]
}
```

**Response** (201 Created): Same as single point object

**Validation**:
- Title: 1-255 characters, required
- Latitude: -90 to 90
- Longitude: -180 to 180
- Description: Optional, HTML allowed
- Tags: Optional, auto-created if not exist (case-insensitive)

---

### Get Point

Get single GPS point details.

**Endpoint**: `GET /points/{id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK): Point object (same as list)

**Permissions**:
- Owner: Full access
- Shared user: View/edit based on permission level
- Public point: Anyone can view

---

### Update Point

Update GPS point.

**Endpoint**: `PUT /points/{id}/` or `PATCH /points/{id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body** (partial update allowed):
```json
{
  "title": "Updated Title",
  "is_public": true,
  "tags": ["new-tag", "updated"]
}
```

**Response** (200 OK): Updated point object

**Permissions**: Owner or shared user with `edit` permission

**Editing Lock**: Automatically acquired on update, released after 15 minutes

---

### Delete Point

Move point to trash (soft delete).

**Endpoint**: `DELETE /points/{id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (204 No Content)

**Permissions**: Owner only

**Effects**:
- Point moved to trash (30-day retention)
- All shares deactivated immediately
- Point visibility set to private
- Annotations preserved (deleted with point after 30 days)

---

### Acquire Editing Lock

Acquire exclusive lock for editing.

**Endpoint**: `POST /points/{id}/lock/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Lock acquired successfully"
}
```

**Response** (409 Conflict - already locked):
```json
{
  "success": false,
  "message": "Point is currently being edited by user@example.com"
}
```

**Lock Duration**: 15 minutes (auto-released)

---

### Release Editing Lock

Release editing lock.

**Endpoint**: `DELETE /points/{id}/lock/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (204 No Content)

---

## Annotations

### List Annotations

Get all annotations for a point.

**Endpoint**: `GET /points/{point_id}/annotations/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "gps_point": "point_uuid",
    "type": "text",
    "text_content": "<p>This is a text annotation</p>",
    "file": null,
    "file_name": null,
    "file_size": null,
    "mime_type": null,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  {
    "id": "uuid",
    "gps_point": "point_uuid",
    "type": "image",
    "text_content": null,
    "file": "/media/annotations/image.jpg",
    "file_name": "sunset.jpg",
    "file_size": 2048576,
    "mime_type": "image/jpeg",
    "created_at": "2025-01-15T11:00:00Z",
    "updated_at": "2025-01-15T11:00:00Z"
  }
]
```

---

### Create Text Annotation

Create a text annotation.

**Endpoint**: `POST /points/{point_id}/annotations/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "type": "text",
  "text_content": "<p>This is my annotation with <strong>rich text</strong></p>"
}
```

**Response** (201 Created): Annotation object

---

### Create File Annotation

Upload file annotation (image, document, or generic file).

**Endpoint**: `POST /points/{point_id}/annotations/`

**Headers**:
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Form Data**:
- `type`: `image`, `document`, or `file`
- `file`: File upload

**Response** (201 Created): Annotation object

**Constraints**:
- Max file size: 1 GB
- User storage quota: 2 GB total
- Allowed image types: JPEG, PNG, GIF, WebP, BMP, TIFF
- Allowed document types: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV
- Disallowed types: Executables, scripts, shell files

**Storage Quota Check**: Returns 413 if quota exceeded

---

### Get Annotation

Get single annotation.

**Endpoint**: `GET /points/{point_id}/annotations/{id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK): Annotation object

---

### Update Text Annotation

Update text annotation content.

**Endpoint**: `PUT /points/{point_id}/annotations/{id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "text_content": "<p>Updated text content</p>"
}
```

**Response** (200 OK): Updated annotation object

**Permissions**: Owner or shared user with `edit` permission

---

### Delete Annotation

Delete annotation and free storage quota.

**Endpoint**: `DELETE /points/{point_id}/annotations/{id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (204 No Content)

**Effects**:
- File deleted from storage
- Storage quota reclaimed
- Permanent deletion (not moved to trash)

---

### Download Annotation

Download annotation file.

**Endpoint**: `GET /annotations/{id}/download/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK): Binary file download

**Headers**:
- `Content-Type`: File MIME type
- `Content-Disposition`: `attachment; filename="filename.ext"`

---

### Preview Annotation

Get annotation preview (images and PDFs only).

**Endpoint**: `GET /annotations/{id}/preview/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
- Images: Resized preview (max 1920x1080)
- PDFs: Original file
- Other types: 404 Not Found

---

## Sharing

### List Shares

Get all shares for a point (owner only).

**Endpoint**: `GET /points/{point_id}/shares/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "gps_point": "point_uuid",
    "shared_with": {
      "id": "uuid",
      "email": "recipient@example.com"
    },
    "permission": "view",
    "is_active": true,
    "invitation_token": "abc123",
    "invitation_sent_at": "2025-01-15T10:00:00Z",
    "created_at": "2025-01-15T10:00:00Z"
  }
]
```

---

### Create Share

Share point with another user.

**Endpoint**: `POST /points/{point_id}/shares/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "shared_with_email": "recipient@example.com",
  "permission": "view"
}
```

**Permissions**:
- `view`: Read-only access
- `edit`: Can edit point and annotations
- `transfer`: Can transfer ownership (removes original owner's access)

**Response** (201 Created): Share object

**Effects**:
- Email invitation sent to recipient
- Invitation valid for 7 days
- Auto-creates user account if email not registered

---

### Get Share

Get single share details.

**Endpoint**: `GET /shares/{id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK): Share object

---

### Update Share

Update share permission.

**Endpoint**: `PATCH /shares/{id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "permission": "edit"
}
```

**Response** (200 OK): Updated share object

**Permissions**: Owner only

---

### Revoke Share

Delete share and revoke access.

**Endpoint**: `DELETE /shares/{id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (204 No Content)

**Permissions**: Owner only

**Effects**: Recipient loses access immediately

---

### Accept Share Invitation

Accept share invitation via email token.

**Endpoint**: `POST /shares/accept/{token}/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "success": true,
  "share": {
    "id": "uuid",
    "gps_point": {
      "id": "uuid",
      "title": "Shared Point"
    },
    "permission": "view"
  }
}
```

**Token Expiry**: 7 days

---

### List Received Shares

Get all points shared with current user.

**Endpoint**: `GET /shares/received/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK): Array of share objects with embedded point data

---

## Export/Import

### Export Points

Export points in various formats.

**Endpoint**: `POST /export/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "format": "geojson",
  "point_ids": ["uuid1", "uuid2"],
  "include_annotations": true
}
```

**Formats**:
- `geojson`: GeoJSON format
- `gpx`: GPX format
- `kml`: KML format
- `csv`: CSV format
- `zip`: ZIP bundle with all formats + files

**Response** (200 OK):
- GeoJSON/GPX/KML/CSV: `Content-Type: application/...`
- ZIP: `Content-Type: application/zip`

**Export Rules**:
- Only owned + shared points
- Annotations included if requested
- Files bundled in ZIP export

---

### Import Points

Import points from file.

**Endpoint**: `POST /import/`

**Headers**:
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Form Data**:
- `file`: File upload (GeoJSON, GPX, KML, CSV, or ZIP)
- `merge_strategy` (optional): `skip`, `update`, or `replace` (default: `skip`)

**Response** (200 OK):
```json
{
  "success": true,
  "imported_count": 10,
  "skipped_count": 2,
  "errors": [
    {
      "line": 5,
      "error": "Invalid coordinates"
    }
  ]
}
```

**Merge Strategies**:
- `skip`: Skip duplicates (by title + coordinates)
- `update`: Update existing points
- `replace`: Replace all existing points

---

## Trash

### List Trash

Get all trashed points.

**Endpoint**: `GET /trash/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "gps_point": {
      "id": "uuid",
      "title": "Deleted Point",
      "annotation_count": 3
    },
    "deleted_at": "2025-01-15T10:00:00Z",
    "permanent_deletion_at": "2025-02-14T10:00:00Z",
    "days_remaining": 25,
    "original_is_public": true
  }
]
```

---

### Restore Point

Restore point from trash.

**Endpoint**: `POST /trash/{id}/restore/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "success": true,
  "point": {
    "id": "uuid",
    "title": "Restored Point"
  }
}
```

**Effects**:
- Point restored with original public status
- Shares reactivated
- Trash entry deleted

**Restrictions**: Cannot restore after 30 days

---

### Permanent Delete

Permanently delete point (bypass trash).

**Endpoint**: `DELETE /trash/{id}/permanent/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (204 No Content)

**Effects**:
- Point deleted immediately
- All annotations deleted
- Storage quota reclaimed
- Cannot be undone

---

### Empty Trash

Permanently delete all expired trash items.

**Endpoint**: `POST /trash/empty/`

**Headers**: `Authorization: Bearer <access_token>`

**Response** (200 OK):
```json
{
  "deleted_count": 5,
  "storage_freed": 52428800
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 204 | No Content | Deletion successful |
| 205 | Reset Content | Logout successful |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Invalid/missing token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Editing lock conflict |
| 413 | Payload Too Large | Storage quota exceeded |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "detail": "Error message",
  "code": "error_code",
  "field_errors": {
    "field_name": ["Error message"]
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `invalid_credentials` | Invalid email or password |
| `token_expired` | JWT token has expired |
| `permission_denied` | Insufficient permissions |
| `quota_exceeded` | Storage quota exceeded |
| `point_locked` | Point is being edited by another user |
| `invalid_file_type` | Unsupported file type |
| `file_too_large` | File exceeds 1GB limit |
| `retention_expired` | Cannot restore (>30 days) |
| `duplicate_email` | Email already registered |
| `invalid_coordinates` | Latitude/longitude out of range |

---

## Rate Limiting

- **Default**: 1000 requests/hour per user
- **Burst**: 10 requests/second

Exceeded limits return `429 Too Many Requests` with `Retry-After` header.

---

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response Headers**:
- `X-Total-Count`: Total items
- `X-Page-Count`: Total pages

**Response Body**:
```json
{
  "count": 100,
  "next": "/api/v1/points/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Webhooks (Future Feature)

Not implemented in v1.0. Planned for v1.1:
- Point created/updated/deleted
- Share accepted/revoked
- Storage quota warnings

---

## OpenAPI Specification

Full OpenAPI 3.0 spec available at `/api/schema/` (requires authentication).

Interactive API documentation: `/api/docs/` (Swagger UI)

---

**Last Updated**: 2025-10-06
**API Version**: 1.0.0
