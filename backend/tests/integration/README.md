# Integration Tests - GeoAnnotator

## Overview

This directory contains comprehensive integration tests for the GeoAnnotator application. These tests validate complete user workflows and feature interactions, ensuring that all components work together correctly.

## Test Scenarios

The integration tests are organized into 8 scenarios based on the quickstart guide:

### Scenario 1: User Registration and Authentication (`test_scenario_auth.py`)
**Acceptance Criteria**: FR-001 to FR-004

Tests the complete authentication flow:
- User registration with email/password
- Login with JWT tokens (access + refresh)
- User profile retrieval with storage quota
- Token refresh mechanism
- Invalid credentials handling

**Key Tests**:
- `test_step_1_register_new_user` - User registration with 2GB default quota
- `test_step_2_login_with_valid_credentials` - JWT token generation
- `test_step_3_get_user_profile` - Profile with storage percentage
- `test_step_4_refresh_access_token` - Token refresh
- `test_step_5_login_with_invalid_credentials` - Error handling
- `test_complete_authentication_flow` - Full lifecycle

### Scenario 2: GPS Point Creation and Management (`test_scenario_points.py`)
**Acceptance Criteria**: FR-005 to FR-018

Tests point CRUD operations and search:
- Create private/public points
- List user's points
- Bounding box search
- Tag filtering
- Full-text search
- Point updates with lock acquisition
- Point deletion (move to trash)

**Key Tests**:
- `test_step_1_create_private_gps_point` - Private point creation
- `test_step_2_create_public_gps_point` - Public point creation
- `test_step_4_search_points_by_bounding_box` - Geospatial search
- `test_step_5_filter_points_by_tag` - Tag filtering
- `test_step_6_full_text_search` - Text search
- `test_step_7_update_gps_point` - Updates with lock

### Scenario 3: Annotations (Text and Files) (`test_scenario_annotations.py`)
**Acceptance Criteria**: FR-019 to FR-029

Tests annotation creation and management:
- Text annotations with rich HTML
- Image file uploads with preview
- Document uploads (PDF, Office)
- Storage quota enforcement
- Invalid file type rejection
- File download and preview
- Quota reclaim on deletion

**Key Tests**:
- `test_step_1_add_text_annotation` - Rich text annotations
- `test_step_2_upload_image_annotation` - Image upload with quota tracking
- `test_step_3_upload_document_annotation` - PDF upload
- `test_step_4_upload_file_exceeding_quota` - Quota enforcement
- `test_step_5_upload_invalid_file_type` - File validation
- `test_step_10_delete_file_annotation_quota_reclaim` - Storage reclaim

### Scenario 4: Sharing and Permissions (`test_scenario_sharing.py`)
**Acceptance Criteria**: FR-030 to FR-045

Tests sharing workflow and permissions:
- Share points with view/edit/transfer permissions
- Email invitation system
- Permission enforcement
- Editing locks with concurrent access
- Cascade revoke
- Non-registered user invitations

**Key Tests**:
- `test_step_1_share_point_with_view_permission` - View-only sharing
- `test_step_2_accept_share_invitation` - Invitation acceptance
- `test_step_4_bob_attempts_edit_with_view_only` - Permission denial
- `test_step_6_bob_edits_shared_point_with_edit_permission` - Edit permission
- `test_step_7_alice_attempts_edit_while_bob_holds_lock` - Lock conflict
- `test_step_11_alice_revokes_bob_share_cascade` - Cascade deletion

### Scenario 5: Import/Export (`test_scenario_import_export.py`)
**Acceptance Criteria**: FR-046 to FR-055

Tests data import/export:
- Export in multiple formats (GeoJSON, GPX, KML, CSV, ZIP)
- Import from various formats
- Validation error handling
- Duplicate detection
- Selective export
- Bundle export with annotations

**Key Tests**:
- `test_step_1_export_points_as_geojson` - GeoJSON export
- `test_step_2_export_specific_points_as_gpx` - GPX export
- `test_step_3_export_full_bundle_as_zip` - ZIP bundle
- `test_step_4_import_geojson_file` - GeoJSON import
- `test_step_5_import_csv_with_validation_errors` - Error handling
- `test_step_6_import_with_duplicate_detection` - Duplicate handling

### Scenario 6: Trash and Restoration (`test_scenario_trash.py`)
**Acceptance Criteria**: FR-056 to FR-062

Tests trash management:
- Move points to trash (30-day retention)
- List trashed points
- Restore from trash
- Permanent deletion
- Empty trash
- Expired point handling
- Share deactivation on trash

**Key Tests**:
- `test_step_1_delete_point_move_to_trash` - Soft delete
- `test_step_2_list_trashed_points` - Trash listing with days remaining
- `test_step_3_restore_point_from_trash` - Restoration
- `test_step_4_permanently_delete_point` - Hard delete with quota reclaim
- `test_step_5_empty_entire_trash` - Bulk deletion
- `test_step_6_attempt_restore_expired_point` - Expiry validation

### Scenario 7: Public Point Browsing (`test_scenario_public.py`)
**Acceptance Criteria**: FR-063 to FR-068

Tests public point access:
- Create public points
- Browse public points
- View public point details
- Permission checks (view-only)
- Anonymous access (if enabled)

**Key Tests**:
- `test_step_1_alice_creates_public_point` - Public point creation
- `test_step_2_bob_browses_public_points` - Public listing
- `test_step_3_bob_views_public_point_details` - Detail view
- `test_step_4_bob_cannot_edit_public_point` - Permission check
- `test_step_5_anonymous_user_browses_public_points` - Anonymous access

### Scenario 8: Editing Locks and Concurrency (`test_scenario_locks.py`)
**Acceptance Criteria**: FR-069 to FR-073

Tests concurrency control:
- Acquire editing lock
- Lock conflict handling
- Auto-refresh on edit
- Auto-expiry (15 minutes)
- Manual lock release

**Key Tests**:
- `test_step_1_alice_acquires_lock` - Lock acquisition
- `test_step_2_bob_attempts_to_acquire_lock_conflict` - Conflict handling
- `test_step_3_alice_edits_point_auto_refresh_lock` - Auto-refresh
- `test_step_4_wait_15_minutes_lock_expires` - Expiry simulation
- `test_step_5_alice_manually_releases_lock` - Manual release

## Running the Tests

### Prerequisites
- PostgreSQL with PostGIS extension
- Python 3.11+
- All dependencies installed (see `requirements/development.txt`)

### Setup Test Database
```bash
# Create test database with PostGIS
createdb geoannotator_test
psql geoannotator_test -c "CREATE EXTENSION postgis;"

# Run migrations
python manage.py migrate --settings=config.settings.development
```

### Run All Integration Tests
```bash
# From backend/ directory
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ --cov=apps --cov-report=html
```

### Run Specific Scenario
```bash
# Run authentication tests
pytest tests/integration/test_scenario_auth.py -v

# Run sharing tests
pytest tests/integration/test_scenario_sharing.py -v
```

### Run Specific Test
```bash
# Run a single test function
pytest tests/integration/test_scenario_auth.py::TestScenario1AuthenticationFlow::test_step_1_register_new_user -v
```

## Test Structure

Each test scenario follows this pattern:

```python
@pytest.mark.django_db
class TestScenarioX:
    """Integration tests for X workflow."""

    def setup_method(self):
        """Set up test client and data before each test."""
        # Create users, authenticate, prepare test data

    def test_step_1_description(self):
        """
        Step 1: Description

        Expected:
        - Expected outcome 1
        - Expected outcome 2
        """
        # Given - Setup
        # When - Action
        # Then - Assertions
```

## Test Data

Tests use the following conventions:
- **Users**: `alice@example.com`, `bob@example.com`, `charlie@example.com`
- **Passwords**: `SecurePass123`, `SecurePass456`, etc.
- **Coordinates**: Portland, Oregon area (45.5°N, -122.7°W)
- **File sizes**: Varied to test quota limits (1KB to 2GB+)

## Coverage Goals

- **General Coverage**: ≥80% for all code
- **Critical Paths**: ≥95% for:
  - Authentication flows
  - Storage quota enforcement
  - Permission checks
  - Sharing logic
  - Lock management

## CI/CD Integration

These tests are run automatically on:
- Every pull request
- Merge to main branch
- Nightly builds

See `.github/workflows/test.yml` for configuration.

## Troubleshooting

### Common Issues

**PostGIS not installed**:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15-postgis-3
```

**Database connection errors**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify test database exists
psql -l | grep geoannotator_test
```

**Import errors**:
```bash
# Ensure in backend/ directory
cd backend/

# Install dependencies
pip install -r requirements/development.txt
```

### Debug Mode

Run tests with verbose output:
```bash
pytest tests/integration/ -vv -s
```

## Next Steps

After integration tests pass:
1. Run unit tests for individual components
2. Execute E2E tests with Playwright
3. Perform load testing with k6
4. Validate accessibility with axe-core

## References

- [Quickstart Guide](../../specs/001-build-a-web/quickstart.md) - Test scenario source
- [API Contracts](../../specs/001-build-a-web/contracts/) - Endpoint specifications
- [Data Model](../../specs/001-build-a-web/data-model.md) - Entity relationships
