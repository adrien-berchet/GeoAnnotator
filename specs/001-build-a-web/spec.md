# Feature Specification: GeoAnnotator Web Application

**Feature Branch**: `001-build-a-web`
**Created**: 2025-10-06
**Status**: Draft
**Input**: User description: "Build a web application that can help me store GPS points and annotate them. Each point must have a title and can have an optional description or a tag. The annotations can be texts, images, documents or any other type of file. Annotations can be downloaded and the usual formats of texts, images and documents can be previewed in the application. The application should be able to use the current GPS position of the device to create a new point but the user can also select an arbitrary point. Each user has its own account and must be authenticated to create new points. The points and annotations created by a user are not accessible to other users by default. However, users can share points and annotations to other users or even make them public if they wish. The points are shown on an interactive map and it is possible to filter them or to search a set of points. Finally, it is possible to export the points and their annotations and import them in another acount."

---

## Clarifications

### Session 2025-10-06

- Q: What is the file size limit per annotation and total storage per user? → A: Each annotation file limited to 1GB, user account total storage limited to 2GB
- Q: How can users share points with non-registered users? → A: Users can send email invitations to share points. Permissions can be view, edit, or ownership transfer
- Q: What permission levels are available for sharing? → A: View permission (read-only), edit permission (modify point/annotations), and ownership transfer
- Q: What happens when a point owner deletes a shared point? → A: Point is deleted for all users who had access, regardless of permission level
- Q: What is the conflict resolution strategy for concurrent edits? → A: Editing lock - when one user starts editing, others are blocked from editing until the first user completes or cancels
- Q: What is the password reset method? → A: Email-based reset with temporary link to create new password
- Q: What is the character limit for point titles? → A: 255 characters maximum
- Q: What happens to deleted points? → A: Points move to trash for 30 days with sharing disabled immediately; users can contact owner for restoration or ownership transfer
- Q: Do text annotations support rich formatting? → A: Yes, rich text and emoticons supported for descriptions and text annotations
- Q: What image formats are supported? → A: Common formats including JPEG, PNG, TIFF, GIF
- Q: What document formats are supported? → A: Common formats including PDF, ODT, ODS, DOC, DOCX, XLS, XLSX
- Q: Which formats support in-app preview? → A: Common image and document formats (same as supported formats)
- Q: How are clustered points handled on the map? → A: Points too close are grouped with count displayed; clicking shows list of grouped points
- Q: What file format for import/export? → A: Multiple formats - GeoJSON, GPX, KML, or CSV for points; ZIP bundle (KML + annotation folders + mapping file) for full export with annotations

---

## User Scenarios & Testing

### Primary User Story

As a field researcher, I want to capture GPS locations with rich annotations (notes, photos, documents) during my outdoor work, so that I can document my findings in context and share them with my team when needed.

### Acceptance Scenarios

1. **Given** I am an authenticated user at a field location, **When** I tap "Create Point" and allow GPS access, **Then** a new point is created at my current location with a timestamp, and I can add a title
2. **Given** I have created a GPS point with a title "Tree Sample A", **When** I add a text annotation describing the tree species and attach a photo, **Then** both annotations are saved and associated with that point
3. **Given** I have 50 GPS points on my map, **When** I enter "oak" in the search box, **Then** only points containing "oak" in their title, description, or tags are displayed
4. **Given** I own a GPS point with 3 annotations, **When** I click "Share" and select another user from my contacts, **Then** that user can view (but not edit) my point and all its annotations
5. **Given** I have a point marked as "Public", **When** any authenticated user searches the public points, **Then** my point appears in their results
6. **Given** I want to transfer my data to a new account, **When** I export my points and annotations, **Then** I receive a downloadable file containing all my data, and I can import it into another account

### Edge Cases

- What happens when GPS is unavailable or denied? User MUST be able to manually place a point on the map
- What happens when a user uploads a file exceeding 1GB as annotation? System MUST reject the file and display error message indicating the 1GB per-file limit
- What happens when a user tries to upload an annotation but has reached their 2GB account storage limit? System MUST prevent upload and display storage quota exceeded message
- What happens when a user tries to share a point with someone who isn't registered? System MUST send an email invitation with a registration link
- How does the system handle a user creating hundreds of points in a single session? Points MUST load progressively with clustering when too close together
- What happens when a user imports points that conflict with existing point IDs? System MUST assign new unique IDs or prompt for conflict resolution
- What happens when a shared point's owner deletes it? Point MUST move to trash for 30 days; sharing is disabled immediately; other users can contact owner for restoration
- What happens when network is lost during annotation upload? System MUST queue for retry or save locally with sync indicator
- What happens when two users try to edit the same point simultaneously? System MUST lock editing for the first user; second user receives message that point is being edited
- What happens when a user forgets to save edits and closes the browser? System SHOULD auto-save drafts or warn before closing
- What happens when a point title exceeds 255 characters? System MUST truncate or reject with validation error before save
- What happens after 30 days in trash? System MUST permanently delete points and free up storage quota

---

## Requirements

### Functional Requirements

**Authentication & User Management**
- **FR-001**: System MUST provide user registration with email and password
- **FR-002**: System MUST authenticate users via email/password before allowing point creation
- **FR-003**: System MUST support password reset via email with temporary link to create new password
- **FR-004**: Each user MUST have a unique account isolated from other users' data by default
- **FR-005**: Password reset links MUST expire after a secure timeframe (e.g., 1-24 hours)

**GPS Point Management**
- **FR-006**: System MUST allow authenticated users to create GPS points with mandatory title (max 255 characters)
- **FR-007**: System MUST validate title length and reject or truncate titles exceeding 255 characters
- **FR-008**: System MUST allow users to add optional description (rich text with emoticons) and tags to GPS points
- **FR-009**: System MUST capture current device GPS location (latitude, longitude) when user creates a point from current location
- **FR-010**: System MUST allow users to manually place points on a map at arbitrary coordinates
- **FR-011**: System MUST store creation timestamp for each GPS point
- **FR-012**: System MUST allow users to edit their own GPS points (title, description, tags)
- **FR-013**: System MUST implement editing lock: when one user starts editing a point, other users with edit permission are blocked until editing completes or is cancelled
- **FR-014**: System MUST display clear message to users when a point is locked for editing by another user
- **FR-015**: System MUST allow users to delete their own GPS points
- **FR-016**: Deleting a GPS point MUST move it to trash for 30 days with sharing disabled immediately
- **FR-017**: System MUST permanently delete points after 30 days in trash and free associated storage quota
- **FR-018**: System MUST allow point owners to restore points from trash within 30-day period
- **FR-019**: Users with shared access MUST be notified when a point is moved to trash so they can contact owner for restoration or ownership transfer

**Annotation Management**
- **FR-020**: System MUST allow users to attach multiple annotations to a single GPS point
- **FR-021**: System MUST support text annotations with rich text formatting and emoticons
- **FR-022**: System MUST support image annotations in common formats: JPEG, PNG, TIFF, GIF
- **FR-023**: System MUST support document annotations in common formats: PDF, ODT, ODS, DOC, DOCX, XLS, XLSX
- **FR-024**: System MUST support "any other type of file" as generic file attachments with download capability
- **FR-025**: System MUST allow in-app preview of text annotations with rich formatting
- **FR-026**: System MUST allow in-app preview of image annotations (JPEG, PNG, TIFF, GIF)
- **FR-027**: System MUST allow in-app preview of document annotations (PDF, ODT, ODS, DOC, DOCX, XLS, XLSX)
- **FR-028**: System MUST allow users to download any annotation
- **FR-029**: System MUST enforce file size limit of 1GB per individual annotation file
- **FR-030**: System MUST enforce total storage quota of 2GB per user account across all annotations
- **FR-031**: System MUST display clear error messages when file size or storage quota limits are exceeded
- **FR-032**: System MUST track and display current storage usage for each user

**Map Visualization & Interaction**
- **FR-033**: System MUST display GPS points on an interactive map
- **FR-034**: System MUST allow users to pan and zoom the map
- **FR-035**: System MUST show point markers with title on hover or click
- **FR-036**: System MUST cluster points that are too close together on the map, displaying the count of grouped points
- **FR-037**: System MUST allow users to click on a cluster to view the list of grouped points
- **FR-038**: Map MUST be responsive and functional on viewports from 320px to 2560px

**Search & Filtering**
- **FR-039**: System MUST provide search functionality across point titles, descriptions, and tags
- **FR-040**: System MUST provide filtering by tags
- **FR-041**: System MUST provide filtering by date range based on creation date
- **FR-042**: System MUST provide filtering by sharing status (private, shared, public)
- **FR-043**: Search results MUST update dynamically as user types (debounced)

**Sharing & Permissions**
- **FR-044**: GPS points MUST be private by default (visible only to owner)
- **FR-045**: System MUST allow users to share points by sending email invitations to specific users
- **FR-046**: System MUST allow users to mark individual points as public (visible to all authenticated users)
- **FR-047**: System MUST support three permission levels for shared points: view (read-only), edit (modify point and annotations with locking), and ownership transfer
- **FR-048**: System MUST allow users to revoke sharing access to specific users
- **FR-049**: System MUST allow users to change a public point back to private
- **FR-050**: Users MUST be able to view a list of points shared with them
- **FR-051**: Users MUST be able to browse public points from all users
- **FR-052**: System MUST allow point owners to transfer ownership to another user via email invitation
- **FR-053**: When ownership is transferred, the new owner gains full control and original owner's access depends on new owner's permissions
- **FR-054**: Email invitations for sharing MUST include a registration link for non-registered recipients

**Import & Export**
- **FR-055**: System MUST support export of GPS points in multiple formats: GeoJSON, GPX, KML, or CSV
- **FR-056**: System MUST support export of complete data (points + annotations) as ZIP bundle containing KML file, annotation folders, and mapping file
- **FR-057**: Export MUST include all point metadata (title, description, tags, coordinates, timestamps)
- **FR-058**: Full export ZIP MUST organize annotations in folders per point with a mapping file to associate points with their annotation folders
- **FR-059**: System MUST support import of GPS points from GeoJSON, GPX, KML, or CSV formats
- **FR-060**: System MUST support import of full data from ZIP bundle format
- **FR-061**: Import MUST validate file format and data integrity before processing
- **FR-062**: Import MUST handle ID conflicts by assigning new unique IDs to imported points
- **FR-063**: Import MUST preserve point relationships and annotation associations

**Performance & Scalability**
- **FR-064**: Map rendering MUST complete within 1.5s (p95) on 3G networks for up to 100 points
- **FR-065**: Point clustering MUST perform efficiently for thousands of points
- **FR-066**: Search results MUST return within 500ms (p95)
- **FR-067**: File upload MUST show progress indicator for files >1MB
- **FR-068**: System MUST support at least 1000 concurrent authenticated users

**Accessibility & User Experience**
- **FR-069**: Application MUST comply with WCAG 2.1 Level AA guidelines
- **FR-070**: All user-facing text, labels, and error messages MUST be in English (US)
- **FR-071**: Error messages MUST be clear and actionable (e.g., "GPS unavailable. Please enable location services or place point manually.")
- **FR-072**: Destructive actions (delete point, revoke sharing) MUST require confirmation
- **FR-073**: System SHOULD implement auto-save for point edits or warn before closing unsaved changes

### Key Entities

- **User**: Represents an authenticated account. Attributes: unique ID, email, password hash, registration date, storage quota used (max 2GB), storage quota limit (2GB). Relationships: owns GPS Points, receives shared GPS Points via email invitations
- **GPS Point**: Represents a geographic location with metadata. Attributes: unique ID, title (required, max 255 chars), description (optional, rich text), tags (list, optional), latitude, longitude, creation timestamp, last modified timestamp, owner (User reference), sharing status (private/shared/public), trash status (active/trashed with 30-day retention), editing lock (user ID if locked). Relationships: belongs to one User (owner), has many Annotations, has many Shares
- **Annotation**: Represents content attached to a GPS Point. Attributes: unique ID, type (text/image/document/file), content (rich text string or file reference), file metadata (filename, size up to 1GB, MIME type - JPEG/PNG/TIFF/GIF for images, PDF/ODT/ODS/DOC/DOCX/XLS/XLSX for docs), creation timestamp, preview capability (boolean). Relationships: belongs to one GPS Point
- **Share**: Represents a sharing relationship. Attributes: unique ID, GPS Point reference, recipient User reference (via email), permission level (view/edit/ownership-transfer), granted timestamp, invitation status (pending/accepted), active status (disabled when point trashed). Relationships: links one GPS Point to one recipient User
- **Tag**: Represents a label for categorization. Attributes: unique ID, name. Relationships: many-to-many with GPS Points (a point can have multiple tags, a tag can apply to multiple points)
- **Trash**: Represents deleted points with recovery period. Attributes: GPS Point reference, deletion timestamp, permanent deletion date (deletion timestamp + 30 days), original sharing status (for restoration). Relationships: one-to-one with GPS Point

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain (all 14+ clarifications resolved)
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable (performance targets defined)
- [x] Scope is clearly bounded (core features defined, extensibility noted)
- [x] Dependencies and assumptions identified (GPS access, file storage, authentication system)

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted (users, GPS points, annotations, sharing, map, import/export)
- [x] Ambiguities marked and resolved (14 clarifications completed)
- [x] User scenarios defined (6 acceptance scenarios + 12 edge cases)
- [x] Requirements generated (73 functional requirements)
- [x] Entities identified (6 key entities with attributes and relationships)
- [x] Review checklist passed

---

**Next Steps**: Specification complete and ready for implementation planning. Run `/plan` to create the technical implementation plan.
