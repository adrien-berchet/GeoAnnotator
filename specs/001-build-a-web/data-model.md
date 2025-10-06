# Data Model: GeoAnnotator

**Created**: 2025-10-06
**Status**: Complete

## Overview

This document defines the database schema for the GeoAnnotator application, including entities, relationships, fields, validation rules, and indexes. All models use Django ORM with PostGIS extensions for geographic operations.

---

## Entity Relationship Diagram

```
User (Django built-in + extensions)
  ↓ owns (1:N)
GPSPoint
  ↓ has (1:N)
Annotation

GPSPoint ←→ Tag (M:N)
GPSPoint ←→ Share (1:N) ←→ User (recipient)
GPSPoint ←→ Trash (1:1, optional)
```

---

## Entities

### 1. User (Extended Django User Model)

**Purpose**: Represents an authenticated user account with storage quota tracking.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUIDField | PK, auto | Unique user identifier |
| email | EmailField | Unique, indexed | User email (used for login) |
| password | CharField | Hashed (PBKDF2) | Encrypted password |
| is_active | BooleanField | Default: true | Account active status |
| date_joined | DateTimeField | Auto-now-add | Registration timestamp |
| storage_used | BigIntegerField | Default: 0, ≥0 | Bytes used (annotations) |
| storage_limit | BigIntegerField | Default: 2GB | Max bytes allowed |

**Validation Rules**:
- Email must be valid format (Django EmailValidator)
- Password must meet strength requirements (min 8 chars, mixed case, numbers)
- storage_used ≤ storage_limit (enforced at upload time)

**Indexes**:
- Unique index on email (for login lookup)
- Index on is_active (for filtering active users)

**Relationships**:
- One-to-many with GPSPoint (user owns points)
- Many-to-many with GPSPoint via Share (user receives shared points)

---

### 2. GPSPoint

**Purpose**: Represents a geographic location with metadata.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUIDField | PK, auto | Unique point identifier |
| title | CharField | Max 255, indexed | Point title (required) |
| description | TextField | Optional, rich text | HTML description with emoticons |
| location | PointField (PostGIS) | SRID=4326, indexed | Lat/lon coordinates (WGS 84) |
| owner | ForeignKey(User) | ON DELETE CASCADE | Point owner |
| created_at | DateTimeField | Auto-now-add | Creation timestamp |
| updated_at | DateTimeField | Auto-now | Last modification timestamp |
| is_public | BooleanField | Default: false | Public visibility flag |
| editing_lock_user | ForeignKey(User) | NULL, ON DELETE SET NULL | User currently editing (null if unlocked) |
| editing_lock_acquired_at | DateTimeField | NULL | Lock acquisition timestamp |

**Validation Rules**:
- title length: 1-255 characters
- location must be valid WGS 84 coordinates (-90 ≤ lat ≤ 90, -180 ≤ lon ≤ 180)
- editing_lock_user and editing_lock_acquired_at must both be NULL or both be set
- Auto-release lock if acquired_at > 15 minutes ago (handled in service layer)

**Indexes**:
- Spatial index on location (PostGIS GIST index for bounding box queries)
- Index on owner (for user's point list)
- Index on is_public (for public point browsing)
- Composite index on (owner, created_at DESC) for user's point timeline
- GIN index on title for full-text search

**Relationships**:
- Many-to-one with User (owner)
- One-to-many with Annotation
- Many-to-many with Tag
- One-to-many with Share
- One-to-one with Trash (optional)

---

### 3. Tag

**Purpose**: Represents a label for categorizing points.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUIDField | PK, auto | Unique tag identifier |
| name | CharField | Max 50, unique | Tag name (e.g., "forest", "river") |
| created_at | DateTimeField | Auto-now-add | Creation timestamp |

**Validation Rules**:
- name: 1-50 characters, alphanumeric + hyphens/underscores only
- name is case-insensitive unique (enforced via database constraint)

**Indexes**:
- Unique index on LOWER(name) (for case-insensitive uniqueness)

**Relationships**:
- Many-to-many with GPSPoint (through GPSPoint_Tags table)

---

### 4. GPSPoint_Tags (Join Table)

**Purpose**: Many-to-many relationship between GPSPoint and Tag.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | AutoField | PK, auto | Join table ID |
| gps_point | ForeignKey(GPSPoint) | ON DELETE CASCADE | Point reference |
| tag | ForeignKey(Tag) | ON DELETE CASCADE | Tag reference |

**Validation Rules**:
- Unique together: (gps_point, tag) (no duplicate tags per point)

**Indexes**:
- Composite index on (gps_point, tag)
- Index on tag (for finding all points with a tag)

---

### 5. Annotation

**Purpose**: Represents content attached to a GPS point (text, image, document, or file).

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUIDField | PK, auto | Unique annotation identifier |
| gps_point | ForeignKey(GPSPoint) | ON DELETE CASCADE | Associated point |
| type | CharField | Choices, indexed | text / image / document / file |
| text_content | TextField | NULL for non-text | Rich text HTML (for text type) |
| file | FileField | NULL for text | File upload path |
| file_name | CharField | Max 255 | Original filename |
| file_size | BigIntegerField | ≥0, ≤1GB | File size in bytes |
| mime_type | CharField | Max 100 | MIME type (e.g., image/jpeg) |
| can_preview | BooleanField | Default: false | Preview supported? |
| created_at | DateTimeField | Auto-now-add | Upload timestamp |

**Validation Rules**:
- type must be one of: text, image, document, file
- If type=text: text_content required, file must be NULL
- If type≠text: file required, text_content must be NULL
- file_size ≤ 1GB (1,073,741,824 bytes)
- Image types: MIME must be image/jpeg, image/png, image/tiff, image/gif
- Document types: MIME must be application/pdf, application/vnd.oasis.opendocument.*, application/vnd.openxmlformats-officedocument.*, application/msword, application/vnd.ms-excel
- can_preview = true for images, PDF, and supported docs

**Indexes**:
- Index on gps_point (for fetching point's annotations)
- Index on type (for filtering by annotation type)

**Relationships**:
- Many-to-one with GPSPoint

---

### 6. Share

**Purpose**: Represents a sharing relationship between a point owner and a recipient.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUIDField | PK, auto | Unique share identifier |
| gps_point | ForeignKey(GPSPoint) | ON DELETE CASCADE | Shared point |
| owner | ForeignKey(User) | related_name='shares_sent' | Point owner |
| recipient_email | EmailField | Indexed | Recipient email (may not be registered) |
| recipient_user | ForeignKey(User) | NULL, related_name='shares_received' | Recipient user (NULL if not registered) |
| permission_level | CharField | Choices, indexed | view / edit / transfer |
| invitation_token | UUIDField | Unique, NULL | Token for email invitation |
| invitation_sent_at | DateTimeField | Auto-now-add | Invitation timestamp |
| accepted_at | DateTimeField | NULL | Acceptance timestamp |
| is_active | BooleanField | Default: true | Share active (false when point trashed) |
| created_at | DateTimeField | Auto-now-add | Share creation timestamp |

**Validation Rules**:
- permission_level must be one of: view, edit, transfer
- Unique together: (gps_point, recipient_email) (no duplicate shares)
- If accepted_at is not NULL, recipient_user must be set
- invitation_token expires after 7 days (checked in service layer)

**Indexes**:
- Index on gps_point (for point's share list)
- Index on recipient_email (for invitation lookup)
- Index on recipient_user (for user's received shares)
- Index on invitation_token (for invitation acceptance)
- Index on is_active (for filtering active shares)

**Relationships**:
- Many-to-one with GPSPoint
- Many-to-one with User (owner)
- Many-to-one with User (recipient, optional)

**State Transitions**:
1. Created → invitation_sent_at set, invitation_token generated, email sent
2. Accepted → accepted_at set, recipient_user set (if registered)
3. Deactivated → is_active=false (when point moved to trash)

---

### 7. Trash

**Purpose**: Represents a deleted point with 30-day retention period.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUIDField | PK, auto | Unique trash entry identifier |
| gps_point | OneToOneField(GPSPoint) | ON DELETE CASCADE, unique | Trashed point |
| deleted_by | ForeignKey(User) | ON DELETE SET NULL | User who deleted |
| deleted_at | DateTimeField | Auto-now-add | Deletion timestamp |
| permanent_deletion_at | DateTimeField | Auto-calculated | deletion_at + 30 days |
| original_is_public | BooleanField | - | Original public status (for restoration) |

**Validation Rules**:
- permanent_deletion_at = deleted_at + 30 days (auto-calculated)
- Unique constraint on gps_point (one trash entry per point)

**Indexes**:
- Index on permanent_deletion_at (for scheduled cleanup task)
- Index on deleted_by (for user's trash view)

**Relationships**:
- One-to-one with GPSPoint

**Lifecycle**:
1. Point deleted → Trash entry created, all shares set is_active=false
2. Point restored (within 30 days) → Trash entry deleted, shares reactivated (if not revoked)
3. 30 days elapsed → Scheduled task deletes GPSPoint (CASCADE deletes Trash, Annotations, Shares)

---

## Database Migrations

**Initial Migration**:
1. Create User model extension (storage_used, storage_limit)
2. Create Tag, GPSPoint, Annotation, Share, Trash models
3. Create GPSPoint_Tags join table
4. Add spatial index on GPSPoint.location
5. Add GIN indexes for full-text search
6. Add CHECK constraints for quotas and validation

**Migration Best Practices**:
- Use Django migrations for schema changes
- Create data migrations for any required data transformations
- Test migrations on a copy of production data before deployment
- Keep migrations atomic (wrap in transaction)

---

## Quota Enforcement Strategy

**Storage Quota**:
1. Before file upload: Check `user.storage_used + file_size ≤ user.storage_limit`
2. On upload success: Update `user.storage_used += file_size`
3. On annotation deletion: Update `user.storage_used -= annotation.file_size`
4. On point permanent deletion: Update `user.storage_used -= SUM(annotations.file_size)`

**Quota Warning**:
- Show warning when `user.storage_used ≥ 0.9 * user.storage_limit` (90% used)
- Provide UI for viewing storage breakdown by point

---

## Performance Optimizations

**Query Optimization**:
- Use `select_related()` for foreign keys (owner, gps_point)
- Use `prefetch_related()` for many-to-many (tags) and reverse foreign keys (annotations, shares)
- Use `only()` / `defer()` to fetch only needed fields for list views
- Implement pagination for point lists (25-50 points per page)

**Spatial Queries**:
- Bounding box query for map viewport: `GPSPoint.objects.filter(location__within=bbox)`
- Nearest points: `GPSPoint.objects.annotate(distance=Distance('location', user_point)).order_by('distance')[:10]`
- Point clustering: Use PostGIS `ST_ClusterKMeans` or application-level Leaflet.markercluster

**Caching**:
- Cache public points for 5 minutes (Redis or Django cache backend)
- Cache tag list for 10 minutes (rarely changes)
- Invalidate cache on point/tag creation/deletion

---

## Security Considerations

**Access Control**:
- All queries filtered by `owner=request.user` OR `shares__recipient_user=request.user AND shares__is_active=true` OR `is_public=true`
- Edit permission checked via `permission_level IN ['edit', 'transfer']`
- Transfer permission checked via `permission_level='transfer'`

**Data Sanitization**:
- Rich text HTML sanitized with `bleach` library (whitelist tags: p, strong, em, u, ul, ol, li, a, br, img for emoji)
- File uploads validated by MIME type (reject executable types)
- File names sanitized (remove path traversal characters)

**SQL Injection Prevention**:
- Django ORM parameterized queries (no raw SQL except for complex geospatial operations)
- Use `.filter()` with Q objects instead of raw WHERE clauses

---

**Next Step**: Generate API contracts (OpenAPI schemas) for each endpoint in contracts/ directory.
