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
- Icon files are copied from this directory to `/app/media/point_type_icons/` **inside the Docker image**
- Uses local filesystem storage (ignores production S3 settings)
- Generates domain-relative URLs (e.g., `/media/point_type_icons/base_hunting_area_abc12345.png`)
- **No database changes** - only prepares the icon files
- These bundled icons become part of the Docker image

### 2. Runtime (normal mode)

When the container starts in production, the command is run without `--icon-files-only`:
- Reads icon files from the bundled location in the Docker image
- Uploads them to the configured storage backend:
  - **Development**: Local filesystem at `media/point_type_icons/`
  - **Production**: S3/MinIO object storage
- Creates database entries with the appropriate URLs:
  - **Development**: Domain-relative path (e.g., `/media/point_type_icons/base_hunting_area_abc12345.png`)
  - **Production**: Full S3 URL (e.g., `https://s3.amazonaws.com/bucket/point_type_icons/base_hunting_area_abc12345.png`)
- The frontend displays icons using these URLs, which work correctly in any environment
- This is consistent with how user-uploaded custom type icons are handled

## Image Recommendations

- **Format**: PNG with transparency works best for icons
- **Size**: 32x32 to 64x64 pixels (icons will be displayed small)
- **File Size**: Keep under 10KB for performance
- **Colors**: Use simple, clear designs that work on both light and dark backgrounds

## Current Icons

- `hunting_area.png` - Hunter with dog icon for hunting areas
