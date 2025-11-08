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

When the management command runs:
- If the `icon` value ends with an image extension, it loads the file from this directory
- The file is saved using Django's storage backend to `point_type_icons/` with a unique `base_` prefixed filename
- The storage backend automatically handles the destination:
  - **Development**: Local filesystem at `media/point_type_icons/`
  - **Production**: S3/MinIO object storage
- The storage URL is stored in the database's `icon` field:
  - **Development**: Domain-relative path (e.g., `/media/point_type_icons/base_hunting_area_abc12345.png`)
  - **Production**: Full S3 URL (e.g., `https://s3.amazonaws.com/bucket/point_type_icons/base_hunting_area_abc12345.png`)
- The frontend displays the image using this URL, which works correctly in any environment
- This is consistent with how user-uploaded custom type icons are handled

## Image Recommendations

- **Format**: PNG with transparency works best for icons
- **Size**: 32x32 to 64x64 pixels (icons will be displayed small)
- **File Size**: Keep under 10KB for performance
- **Colors**: Use simple, clear designs that work on both light and dark backgrounds

## Current Icons

- `hunting_area.png` - Hunter with dog icon for hunting areas
