# Default Point Type Icons

This directory contains static icon images for default (base) point types.

## Overview

These icons are **static files** bundled into the application, not user-generated media files. They are served directly from the Docker image in production, not from S3 storage.

## Usage

Icons are referenced in the `create_default_types.py` management command. For example:

```python
{'names': {'en': 'Viewing Point', 'fr': 'Point de vue'}, 'icon': 'viewpoint.png', 'order': 1}
```

The management command converts `'viewpoint.png'` to the static URL `/static/points/icons/base_viewpoint.png`.

## File Naming Convention

All files use the `base_` prefix to distinguish them from any potential user-uploaded icons:

- Source reference: `viewpoint.png` (in management command)
- Actual file: `base_viewpoint.png` (in this directory)
- Static URL: `/static/points/icons/base_viewpoint.png`

## How It Works

1. **Development**: Icons are stored in this directory and served via Django's static files system
2. **Production**: Icons are collected by `collectstatic` and bundled into the Docker image
3. **Database**: Point types store the static URL (e.g., `/static/points/icons/base_viewpoint.png`)
4. **Frontend**: Displays icons using the static URL, served from the Docker image

## Adding New Icons

To add a new default point type icon:

1. Add the PNG file to this directory with the `base_` prefix (e.g., `base_newicon.png`)
2. Update the `create_default_types.py` command to reference it without the prefix:
   ```python
   {'names': {'en': 'New Type', 'fr': 'Nouveau type'}, 'icon': 'newicon.png', 'order': X}
   ```
3. Run `python manage.py create_default_types` to create/update the database entries

## Image Recommendations

- **Format**: PNG with transparency
- **Size**: 32x32 to 64x64 pixels (icons displayed small)
- **File Size**: Keep under 10KB for performance
- **Colors**: Use simple, clear designs that work on both light and dark backgrounds

## Current Icons

This directory contains 22 custom icons for various point types including:
- Navigation: viewpoint, entry, exit, bridge, tunnel, etc.
- Safety: danger, alarm, first-aid, mine, etc.
- Infrastructure: lighthouse, windmill, etc.
- Activities: food, accessible, hunting_area, etc.
