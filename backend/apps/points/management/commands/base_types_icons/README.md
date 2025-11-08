# Base Type Icons

This directory contains custom icon images for base point types.

## Usage

To use a custom image icon instead of an emoji:

1. Place your image file in this directory (supported formats: PNG, JPG, JPEG, GIF, SVG, WEBP)
2. In `create_default_types.py`, reference the filename in the `icon` field instead of an emoji

Example:
```python
{'names': {'en': 'Hunting Area', 'fr': 'Zone de chasse'}, 'icon': 'hunting_area.png', 'order': 38},
```

## How It Works

The command has two modes of operation:

### 1. Docker Build (--icon-files-only mode)

During Docker image build, the command is run with `--icon-files-only`:
- Icon files are copied from this directory to `backend/apps/points/static/points/icons/`
- Then `collectstatic` bundles them with other static files into the Docker image
- Generates static file URLs (e.g., `/static/points/icons/base_hunting_area.png`)
- **No database changes** - only prepares the static icon files
- These icons are served directly from the Docker image (not from S3)

### 2. Runtime (normal mode)

When the container starts (or during development setup), the command runs without `--icon-files-only`:
- References the static icon files that are already bundled in the image
- Creates database entries with static file URLs (e.g., `/static/points/icons/base_viewpoint.png`)
- The frontend displays icons from the static files served by Django/Nginx
- **Icons are served from the Docker image**, not uploaded to S3
- This is different from user-uploaded custom type icons (which use media storage/S3)

## Image Recommendations

- **Format**: PNG with transparency works best for icons
- **Size**: 32x32 to 64x64 pixels (icons will be displayed small)
- **File Size**: Keep under 10KB for performance
- **Colors**: Use simple, clear designs that work on both light and dark backgrounds

## Current Icons

- `hunting_area.png` - Hunter with dog icon for hunting areas
