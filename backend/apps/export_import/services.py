"""
Export/Import services.

Handles multi-format export (GeoJSON, GPX, KML, CSV, ZIP) and import with validation.
"""

import json
import csv
import zipfile
from io import StringIO, BytesIO
from datetime import datetime
from pathlib import Path
import geopandas as gpd
import gpxpy
import gpxpy.gpx
import simplekml
from django.http import HttpResponse

from apps.points.models import GPSPoint
from apps.annotations.models import Annotation
from apps.authentication.models import User


class ExportService:
    """Service for exporting GPS points in various formats."""

    @staticmethod
    def export_geojson(points: list[GPSPoint], include_annotations: bool = True) -> str:
        """
        Export points as GeoJSON FeatureCollection.

        Args:
            points: List of GPSPoint objects
            include_annotations: Include annotation details

        Returns:
            str: GeoJSON string
        """
        features = []

        for point in points:
            feature = {
                'type': 'Feature',
                'id': str(point.id),
                'geometry': {
                    'type': 'Point',
                    'coordinates': [point.longitude, point.latitude]
                },
                'properties': {
                    'title': point.title,
                    'description': point.description,
                    'is_public': point.is_public,
                    'owner': point.owner.email,
                    'tags': [tag.name for tag in point.tags.all()],
                    'created_at': point.created_at.isoformat(),
                    'updated_at': point.updated_at.isoformat(),
                }
            }

            if include_annotations:
                annotations = Annotation.objects.filter(gps_point=point)
                feature['properties']['annotations'] = [
                    {
                        'id': str(ann.id),
                        'type': ann.type,
                        'text_content': ann.text_content if ann.type == 'text' else None,
                        'file_name': ann.file_name if ann.file else None,
                        'created_at': ann.created_at.isoformat(),
                    }
                    for ann in annotations
                ]

            features.append(feature)

        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }

        return json.dumps(geojson, indent=2, ensure_ascii=False)

    @staticmethod
    def export_gpx(points: list[GPSPoint]) -> str:
        """
        Export points as GPX (GPS Exchange Format).

        Args:
            points: List of GPSPoint objects

        Returns:
            str: GPX XML string
        """
        gpx = gpxpy.gpx.GPX()

        # GPX metadata
        gpx.name = 'GeoAnnotator Export'
        gpx.description = f'Exported {len(points)} points from GeoAnnotator'
        gpx.time = datetime.now()

        for point in points:
            waypoint = gpxpy.gpx.GPXWaypoint(
                latitude=point.latitude,
                longitude=point.longitude,
                name=point.title,
                description=point.description or '',
                time=point.created_at,
            )
            gpx.waypoints.append(waypoint)

        return gpx.to_xml()

    @staticmethod
    def export_kml(points: list[GPSPoint]) -> str:
        """
        Export points as KML (Google Earth format).

        Args:
            points: List of GPSPoint objects

        Returns:
            str: KML XML string
        """
        kml = simplekml.Kml()

        for point in points:
            pnt = kml.newpoint(
                name=point.title,
                description=point.description or '',
                coords=[(point.longitude, point.latitude)]
            )

            # Add extended data
            pnt.extendeddata.newdata(
                name='owner',
                value=point.owner.email,
            )
            pnt.extendeddata.newdata(
                name='is_public',
                value=str(point.is_public),
            )
            pnt.extendeddata.newdata(
                name='tags',
                value=', '.join([tag.name for tag in point.tags.all()]),
            )

        return kml.kml()

    @staticmethod
    def export_csv(points: list[GPSPoint]) -> str:
        """
        Export points as CSV.

        Args:
            points: List of GPSPoint objects

        Returns:
            str: CSV string
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'id',
            'title',
            'description',
            'latitude',
            'longitude',
            'is_public',
            'owner',
            'tags',
            'created_at',
            'updated_at',
        ])

        # Data rows
        for point in points:
            writer.writerow([
                str(point.id),
                point.title,
                point.description or '',
                point.latitude,
                point.longitude,
                point.is_public,
                point.owner.email,
                '|'.join([tag.name for tag in point.tags.all()]),
                point.created_at.isoformat(),
                point.updated_at.isoformat(),
            ])

        return output.getvalue()

    @staticmethod
    def export_zip(points: list[GPSPoint], include_annotations: bool = True) -> BytesIO:
        """
        Export points and annotations as ZIP archive.

        Args:
            points: List of GPSPoint objects
            include_annotations: Include annotation files

        Returns:
            BytesIO: ZIP file bytes
        """
        output = BytesIO()

        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add points as GeoJSON
            geojson_content = ExportService.export_geojson(points, include_annotations=False)
            zf.writestr('points.geojson', geojson_content)

            # Add annotations if requested
            if include_annotations:
                for point in points:
                    annotations = Annotation.objects.filter(gps_point=point, file__isnull=False)

                    for ann in annotations:
                        # Add file to zip
                        if ann.file:
                            file_path = f'annotations/{point.id}/{ann.id}_{ann.file_name}'
                            try:
                                zf.writestr(file_path, ann.file.read())
                            except Exception as e:
                                print(f"Failed to add annotation file: {e}")

        output.seek(0)
        return output

    @staticmethod
    def get_export_response(
        content: str | BytesIO,
        format: str,
        filename: str = None,
    ) -> HttpResponse:
        """
        Create HTTP response for export.

        Args:
            content: Export content (string or BytesIO)
            format: Export format (geojson, gpx, kml, csv, zip)
            filename: Optional custom filename

        Returns:
            HttpResponse with appropriate headers
        """
        content_types = {
            'geojson': 'application/geo+json',
            'gpx': 'application/gpx+xml',
            'kml': 'application/vnd.google-earth.kml+xml',
            'csv': 'text/csv',
            'zip': 'application/zip',
        }

        extensions = {
            'geojson': 'geojson',
            'gpx': 'gpx',
            'kml': 'kml',
            'csv': 'csv',
            'zip': 'zip',
        }

        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'geoannotator_export_{timestamp}.{extensions[format]}'

        response = HttpResponse(
            content=content,
            content_type=content_types.get(format, 'application/octet-stream'),
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


class ImportService:
    """Service for importing GPS points from various formats."""

    @staticmethod
    def import_geojson(file_content: str, user: User, merge_strategy: str = 'create_new') -> dict:
        """
        Import points from GeoJSON.

        Args:
            file_content: GeoJSON string
            user: User importing points
            merge_strategy: 'create_new', 'skip', or 'replace'

        Returns:
            dict: {
                'total_points': int,
                'imported_points': int,
                'skipped_points': int,
                'failed_points': int,
                'errors': list,
                'created_point_ids': list
            }
        """
        result = {
            'total_points': 0,
            'imported_points': 0,
            'skipped_points': 0,
            'failed_points': 0,
            'errors': [],
            'created_point_ids': [],
        }

        try:
            data = json.loads(file_content)
        except json.JSONDecodeError as e:
            result['errors'].append({
                'line_number': 0,
                'error': 'INVALID_JSON',
                'message': str(e),
            })
            return result

        features = data.get('features', [])
        result['total_points'] = len(features)

        for idx, feature in enumerate(features, start=1):
            try:
                geometry = feature.get('geometry', {})
                properties = feature.get('properties', {})

                if geometry.get('type') != 'Point':
                    raise ValueError('Only Point geometries are supported')

                coords = geometry.get('coordinates', [])
                if len(coords) < 2:
                    raise ValueError('Invalid coordinates')

                longitude, latitude = coords[0], coords[1]

                # Validate coordinates
                if not (-180 <= longitude <= 180):
                    raise ValueError(f'Longitude out of range: {longitude}')
                if not (-90 <= latitude <= 90):
                    raise ValueError(f'Latitude out of range: {latitude}')

                # Check for duplicates
                if merge_strategy == 'skip':
                    from django.contrib.gis.geos import Point
                    location = Point(longitude, latitude, srid=4326)
                    existing = GPSPoint.objects.filter(
                        owner=user,
                        location__distance_lte=(location, 1)  # Within 1 meter
                    ).first()

                    if existing:
                        result['skipped_points'] += 1
                        continue

                # Create point
                from apps.points.services import PointService
                point = PointService.create_point(
                    title=properties.get('title', 'Imported Point'),
                    latitude=latitude,
                    longitude=longitude,
                    owner=user,
                    description=properties.get('description'),
                    tags=properties.get('tags', []),
                    is_public=properties.get('is_public', False),
                )

                result['imported_points'] += 1
                result['created_point_ids'].append(str(point.id))

            except Exception as e:
                result['failed_points'] += 1
                result['errors'].append({
                    'line_number': idx,
                    'error': 'IMPORT_ERROR',
                    'message': str(e),
                })

        return result

    @staticmethod
    def import_csv(file_content: str, user: User, merge_strategy: str = 'create_new') -> dict:
        """
        Import points from CSV.

        Args:
            file_content: CSV string
            user: User importing points
            merge_strategy: 'create_new', 'skip', or 'replace'

        Returns:
            dict: Import result
        """
        result = {
            'total_points': 0,
            'imported_points': 0,
            'skipped_points': 0,
            'failed_points': 0,
            'errors': [],
            'created_point_ids': [],
        }

        try:
            reader = csv.DictReader(StringIO(file_content))
            rows = list(reader)
            result['total_points'] = len(rows)

            for idx, row in enumerate(rows, start=2):  # Start at 2 (1 is header)
                try:
                    # Required fields
                    latitude = float(row.get('latitude', 0))
                    longitude = float(row.get('longitude', 0))
                    title = row.get('title', '').strip()

                    if not title:
                        raise ValueError('Title is required')

                    # Validate coordinates
                    if not (-180 <= longitude <= 180):
                        raise ValueError(f'Longitude out of range: {longitude}')
                    if not (-90 <= latitude <= 90):
                        raise ValueError(f'Latitude out of range: {latitude}')

                    # Optional fields
                    description = row.get('description', '').strip() or None
                    is_public = row.get('is_public', 'false').lower() in ['true', '1', 'yes']
                    tags = [t.strip() for t in row.get('tags', '').split('|') if t.strip()]

                    # Create point
                    from apps.points.services import PointService
                    point = PointService.create_point(
                        title=title,
                        latitude=latitude,
                        longitude=longitude,
                        owner=user,
                        description=description,
                        tags=tags,
                        is_public=is_public,
                    )

                    result['imported_points'] += 1
                    result['created_point_ids'].append(str(point.id))

                except Exception as e:
                    result['failed_points'] += 1
                    result['errors'].append({
                        'line_number': idx,
                        'error': 'IMPORT_ERROR',
                        'message': str(e),
                    })

        except Exception as e:
            result['errors'].append({
                'line_number': 0,
                'error': 'INVALID_CSV',
                'message': str(e),
            })

        return result

    @staticmethod
    def import_gpx(file_content: str, user: User) -> dict:
        """
        Import points from GPX.

        Args:
            file_content: GPX XML string
            user: User importing points

        Returns:
            dict: Import result
        """
        result = {
            'total_points': 0,
            'imported_points': 0,
            'skipped_points': 0,
            'failed_points': 0,
            'errors': [],
            'created_point_ids': [],
        }

        try:
            gpx = gpxpy.parse(file_content)
            waypoints = gpx.waypoints
            result['total_points'] = len(waypoints)

            for idx, waypoint in enumerate(waypoints, start=1):
                try:
                    from apps.points.services import PointService
                    point = PointService.create_point(
                        title=waypoint.name or f'Waypoint {idx}',
                        latitude=waypoint.latitude,
                        longitude=waypoint.longitude,
                        owner=user,
                        description=waypoint.description,
                        tags=[],
                        is_public=False,
                    )

                    result['imported_points'] += 1
                    result['created_point_ids'].append(str(point.id))

                except Exception as e:
                    result['failed_points'] += 1
                    result['errors'].append({
                        'line_number': idx,
                        'error': 'IMPORT_ERROR',
                        'message': str(e),
                    })

        except Exception as e:
            result['errors'].append({
                'line_number': 0,
                'error': 'INVALID_GPX',
                'message': str(e),
            })

        return result
