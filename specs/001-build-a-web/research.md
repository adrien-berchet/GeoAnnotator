# Research: GeoAnnotator Technical Decisions

**Created**: 2025-10-06
**Status**: Complete

## Overview

This document captures key technical decisions for the GeoAnnotator web application, focusing on backend framework, frontend framework, database, authentication, file storage, and geospatial operations.

---

## Backend Framework

**Decision**: Django 4.2+ with Django REST Framework 3.14+

**Rationale**:
- Mature, well-documented framework with excellent ORM for complex data models
- Django REST Framework provides robust serialization, authentication, and API endpoint patterns
- Built-in admin interface useful for debugging and data management
- Strong PostgreSQL integration via psycopg2
- Excellent ecosystem for geospatial operations (GeoDjango with PostGIS)
- Python 3.11+ provides modern type hints for better code quality (mypy support)
- Aligns with TDD requirements via pytest-django

**Alternatives Considered**:
- **FastAPI**: Faster performance but less mature ecosystem for complex auth/permissions; less suitable for admin interface needs
- **Flask**: More lightweight but requires more custom code for REST API patterns, authentication, and ORM integration

**Best Practices**:
- Use Django app-based modular structure (separate apps for authentication, points, annotations, sharing, trash, export/import)
- Follow Django's "fat models, thin views" pattern with service layer for complex business logic
- Use DRF serializers for validation and nested relationships
- Implement custom permissions classes for view/edit/transfer permission levels
- Use Django signals sparingly (prefer explicit service layer calls for clarity)

---

## Frontend Framework

**Decision**: React 18+ with Vite 5+ build tool

**Rationale**:
- Component-based architecture aligns with feature-rich UI requirements (map, forms, previews)
- Large ecosystem for UI components and utilities
- Vite provides fast dev server and optimized production builds (meets <300KB bundle target)
- Strong TypeScript support for type safety across API boundaries
- React hooks simplify state management and side effects
- Excellent accessibility support via React ARIA and testing with React Testing Library

**Alternatives Considered**:
- **Vue.js**: Simpler learning curve but smaller ecosystem for mapping libraries
- **Svelte**: Smaller bundle sizes but less mature ecosystem and fewer geospatial integrations

**Best Practices**:
- Use TypeScript for all code (strict mode enabled)
- Feature-folder structure (components/map/, components/annotations/, etc.)
- Custom hooks for reusable logic (useAuth, usePoints, useGeolocation, useStorageQuota)
- Context + Redux Toolkit for global state (auth, points list)
- React.lazy() for code splitting (annotation previews, export modal)
- Accessibility: semantic HTML, ARIA labels, keyboard navigation, focus management

---

## Database & Geospatial Operations

**Decision**: PostgreSQL 15+ with PostGIS extension

**Rationale**:
- Native geospatial support via PostGIS (GEOGRAPHY type, spatial indexes, distance calculations)
- PostGIS provides efficient clustering queries for map view (ST_ClusterKMeans, ST_Distance)
- JSONB type useful for flexible annotation metadata and tag storage
- Strong ACID compliance for critical operations (ownership transfer, trash management)
- Excellent Django integration via GeoDjango (GEOSGeometry, PointField)
- Supports GIN indexes for full-text search on titles/descriptions/tags

**Alternatives Considered**:
- **MongoDB with geospatial indexes**: Lacks strong ACID guarantees for permissions/ownership; less mature Django integration
- **MySQL with spatial extensions**: Less feature-rich geospatial support than PostGIS

**Best Practices**:
- Use PostGIS GEOGRAPHY type for lat/lon (automatic distance calculations in meters)
- Create spatial indexes on point coordinates for fast bounding-box queries
- Use GIN indexes for full-text search (GinIndex on title, description, tags)
- Implement database-level constraints for quota enforcement (CHECK constraint on user storage)
- Use database transactions for multi-step operations (share creation + email send)

---

## Authentication & Authorization

**Decision**: JWT (JSON Web Tokens) via djangorestframework-simplejwt

**Rationale**:
- Stateless authentication suitable for REST API
- Separate access tokens (1h) and refresh tokens (7d) for security/UX balance
- Frontend can store tokens in localStorage (or httpOnly cookies for enhanced security)
- djangorestframework-simplejwt integrates seamlessly with DRF permissions
- Supports token blacklisting for logout (requires database backend)

**Alternatives Considered**:
- **Session-based auth**: Requires CSRF tokens, less suitable for potential mobile app future
- **OAuth2**: Overcomplicated for initial MVP; can add later for social login

**Best Practices**:
- Use HTTPS only (enforce via Django settings)
- Implement token refresh before expiration (frontend interceptor)
- Add blacklist app for logout support
- Use DRF's IsAuthenticated permission class as base
- Custom permission classes for object-level permissions (IsOwnerOrShared, HasEditPermission)
- Password reset via Django's built-in email backend with temporary tokens

---

## File Storage & Quota Management

**Decision**: Django FileField with local storage (development) and S3-compatible storage (production)

**Rationale**:
- Django's storage abstraction allows easy switching between local/S3
- django-storages library provides S3 backend with minimal config changes
- File metadata (size, MIME type) stored in database for quota tracking
- Quota enforcement at upload time (check user's total storage before accepting file)
- 1GB per file enforced via MAX_UPLOAD_SIZE setting and nginx client_max_body_size

**Alternatives Considered**:
- **Direct S3 uploads with presigned URLs**: More complex to implement quota checking; harder to enforce 1GB limit before upload starts
- **Blob storage in database**: Poor performance for large files; PostgreSQL bloat issues

**Best Practices**:
- Store files in structure: `annotations/{user_id}/{point_id}/{annotation_id}/{filename}`
- Generate unique filenames to avoid conflicts (use UUID or timestamp prefix)
- Implement soft quota warning at 90% (1.8GB)
- Use Django signals to update user's storage quota after upload/deletion
- Implement scheduled task to clean up orphaned files (files without database records)
- Support streaming downloads for large files (avoid loading entire file into memory)

---

## Mapping Library

**Decision**: Leaflet 1.9+ with React Leaflet wrapper

**Rationale**:
- Lightweight, open-source mapping library (50KB gzipped vs 500KB+ for Google Maps SDK)
- React Leaflet provides declarative React components (Map, Marker, Popup)
- Excellent plugin ecosystem (Leaflet.markercluster for point clustering)
- OpenStreetMap tiles are free and unrestricted (no API key required)
- Strong mobile support (touch gestures, responsive)

**Alternatives Considered**:
- **Google Maps**: Requires API key, billing, less customizable marker clustering
- **Mapbox**: Requires API key, billing for high usage; similar features to Leaflet

**Best Practices**:
- Use Leaflet.markercluster plugin for grouping nearby points (threshold: zoom level dependent)
- Implement custom cluster icon showing count of grouped points
- Use marker popup for quick preview (title, creation date, annotation count)
- Lazy load map tiles (only fetch visible tiles)
- Implement bounding box queries to backend (only fetch points in current viewport)
- Add geolocation button using browser's Geolocation API (with fallback for denied permission)

---

## Rich Text Editing

**Decision**: Quill editor for text annotations and descriptions

**Rationale**:
- Lightweight rich text editor (50KB gzipped)
- Supports emoticons via emoji picker plugin
- Clean HTML output (sanitized by default)
- Toolbar customizable (bold, italic, lists, links, emoji)
- Good accessibility support (ARIA labels, keyboard shortcuts)

**Alternatives Considered**:
- **TinyMCE**: Larger bundle size (200KB+), more features than needed
- **Draft.js**: Lower-level API, requires more custom code for toolbar

**Best Practices**:
- Store rich text as sanitized HTML in database (use bleach library for sanitization)
- Limit toolbar to essential features (bold, italic, underline, lists, links, emoji)
- Set max length for descriptions (10,000 characters)
- Render preview with same sanitization rules as editing

---

## File Preview

**Decision**: Native browser previews + react-pdf for PDF preview

**Rationale**:
- Images (JPEG, PNG, TIFF, GIF): Use `<img>` tag with object-fit for responsive display
- PDF: Use react-pdf library for in-browser rendering (supports zoom, pagination)
- Office docs (ODT, DOCX, XLS): Use browser download + system app (no reliable in-browser preview for all formats)
- Other files: Download only

**Alternatives Considered**:
- **Google Docs Viewer iframe**: Requires public URLs, privacy concerns, unreliable for large files
- **LibreOffice Online**: Complex self-hosting, overkill for simple preview needs

**Best Practices**:
- Detect file type from MIME type (stored in annotation model)
- Provide fallback download button for all file types
- Implement lazy loading for image previews (IntersectionObserver)
- Show file size and MIME type for non-previewable files
- Use Content-Disposition: inline for images/PDF, attachment for downloads

---

## Import/Export Formats

**Decision**: Multiple format support - GeoJSON, GPX, KML, CSV for points; ZIP bundle for full export

**Rationale**:
- **GeoJSON**: Standard geospatial format, easy to parse/generate, supports properties (tags, description)
- **GPX**: Standard GPS track format, widely compatible with GPS devices
- **KML**: Google Earth format, supports styling and folders
- **CSV**: Simple tabular format for non-geospatial tools (Excel)
- **ZIP bundle**: Combines KML + annotation files + mapping JSON for full data export

**Best Practices**:
- Generate exports asynchronously for large datasets (Celery task)
- Provide progress indicator for export generation
- Include metadata in export (export date, user, version)
- Validate imports strictly (reject malformed files with clear error messages)
- Assign new UUIDs on import to avoid ID conflicts
- Preserve tag relationships and annotation associations in ZIP mapping file

---

## Testing Strategy

**Decision**: pytest (backend) + Vitest + Playwright (frontend)

**Rationale**:
- **pytest**: Django-native testing with fixtures, excellent plugin ecosystem
- **Vitest**: Fast unit testing for React components (compatible with Vite)
- **Playwright**: Cross-browser E2E testing (Chromium, Firefox, WebKit)
- All tools support coverage reporting (meets ≥80% target)

**Best Practices**:
- Backend: Use factory_boy for test data generation (factories for User, GPSPoint, Annotation)
- Backend: Pytest fixtures for authenticated clients, database setup
- Frontend: React Testing Library for component tests (test user interactions, not implementation details)
- Frontend: Mock API calls with MSW (Mock Service Worker)
- E2E: Test critical paths (register → create point → add annotation → share → export)
- Coverage: Aim for ≥95% on auth, quota, permissions code paths

---

## Deployment & Infrastructure

**Decision**: Deferred to implementation phase

**Notes**:
- Docker containers for backend (Django + Gunicorn) and frontend (nginx serving static build)
- PostgreSQL as separate service (RDS or managed PostgreSQL)
- S3-compatible storage for production file uploads
- Consider Celery + Redis for async tasks (export generation, trash cleanup)
- CI/CD pipeline (GitHub Actions) for automated testing and deployment

---

## Summary of Key Decisions

| Component | Technology | Justification |
|-----------|------------|---------------|
| Backend | Django 4.2 + DRF | Mature ecosystem, GeoDjango for PostGIS, robust auth/permissions |
| Frontend | React 18 + Vite | Component architecture, fast builds, strong ecosystem |
| Database | PostgreSQL 15 + PostGIS | Native geospatial operations, ACID compliance, full-text search |
| Auth | JWT (simplejwt) | Stateless REST auth, token refresh, blacklist support |
| File Storage | Django FileField + S3 | Storage abstraction, easy quota tracking, scalable |
| Mapping | Leaflet + React Leaflet | Lightweight, open-source, excellent clustering support |
| Rich Text | Quill | Lightweight, emoji support, clean HTML output |
| Testing | pytest + Vitest + Playwright | Comprehensive coverage, fast execution, E2E support |

---

**Next Step**: Proceed to Phase 1 (Design & Contracts) to generate data models, API contracts, and test scenarios.
