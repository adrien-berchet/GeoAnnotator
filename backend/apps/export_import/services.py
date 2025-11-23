"""
Export/Import services.

Handles multi-format export (GeoJSON, GPX, KML, CSV, ZIP) and import with validation.
"""

import csv
import json
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from io import BytesIO
from io import StringIO

import gpxpy
import gpxpy.gpx
import simplekml
from django.db import models
from django.http import HttpResponse

from apps.annotations.models import Annotation
from apps.authentication.models import User
from apps.points.models import GPSPoint
from apps.points.models import Tag
from apps.points.services import PointService


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
            # Get point type information
            point_type_name = None
            point_type_icon = None
            if point.type:
                # Use English name as fallback if available
                point_type_name = (
                    point.type.names.get("en")
                    or point.type.names.get(point.type.creation_language)
                    or list(point.type.names.values())[0]
                    if point.type.names
                    else None
                )
                point_type_icon = point.type.icon

            feature = {
                "type": "Feature",
                "id": str(point.id),
                "geometry": {"type": "Point", "coordinates": [point.longitude, point.latitude]},
                "properties": {
                    "title": point.title,
                    "description": point.description,
                    "is_public": point.is_public,
                    "owner": point.owner.username,
                    "tags": [tag.name for tag in point.tags.all()],
                    "point_type": point_type_name,
                    "point_type_icon": point_type_icon,
                    "created_at": point.created_at.isoformat(),
                    "updated_at": point.updated_at.isoformat(),
                },
            }

            if include_annotations:
                annotations = Annotation.objects.filter(gps_point=point)
                feature["properties"]["annotations"] = [
                    {
                        "id": str(ann.id),
                        "type": ann.type,
                        "text_content": ann.text_content if ann.type == "text" else None,
                        "file_name": ann.file_name if ann.file else None,
                        "created_at": ann.created_at.isoformat(),
                    }
                    for ann in annotations
                ]

            features.append(feature)

        geojson = {"type": "FeatureCollection", "features": features}

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
        gpx.name = "GeoAnnotator Export"
        gpx.description = f"Exported {len(points)} points from GeoAnnotator"
        gpx.time = datetime.now()

        for point in points:
            waypoint = gpxpy.gpx.GPXWaypoint(
                latitude=point.latitude,
                longitude=point.longitude,
                name=point.title,
                description=point.description or "",
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
                description=point.description or "",
                coords=[(point.longitude, point.latitude)],
            )

            # Add extended data
            pnt.extendeddata.newdata(
                name="owner",
                value=point.owner.username,
            )
            pnt.extendeddata.newdata(
                name="is_public",
                value=str(point.is_public),
            )
            pnt.extendeddata.newdata(
                name="tags",
                value=", ".join([tag.name for tag in point.tags.all()]),
            )

            # Add point type if available
            if point.type:
                point_type_name = (
                    point.type.names.get("en")
                    or point.type.names.get(point.type.creation_language)
                    or list(point.type.names.values())[0]
                    if point.type.names
                    else None
                )
                if point_type_name:
                    pnt.extendeddata.newdata(
                        name="point_type",
                        value=point_type_name,
                    )
                if point.type.icon:
                    pnt.extendeddata.newdata(
                        name="point_type_icon",
                        value=point.type.icon,
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
        writer.writerow(
            [
                "id",
                "title",
                "description",
                "latitude",
                "longitude",
                "is_public",
                "owner",
                "tags",
                "point_type",
                "created_at",
                "updated_at",
            ]
        )

        # Data rows
        for point in points:
            # Get point type name
            point_type_name = ""
            if point.type:
                # Use English name as fallback if available
                point_type_name = (
                    point.type.names.get("en")
                    or point.type.names.get(point.type.creation_language)
                    or list(point.type.names.values())[0]
                    if point.type.names
                    else ""
                )

            writer.writerow(
                [
                    str(point.id),
                    point.title,
                    point.description or "",
                    point.latitude,
                    point.longitude,
                    point.is_public,
                    point.owner.username,
                    "|".join([tag.name for tag in point.tags.all()]),
                    point_type_name,
                    point.created_at.isoformat(),
                    point.updated_at.isoformat(),
                ]
            )

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

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add points as GeoJSON
            geojson_content = ExportService.export_geojson(points, include_annotations=False)
            zf.writestr("points.geojson", geojson_content)

            # Add annotations if requested
            if include_annotations:
                for point in points:
                    annotations = Annotation.objects.filter(gps_point=point, file__isnull=False)

                    for ann in annotations:
                        # Add file to zip
                        if ann.file:
                            file_path = f"annotations/{point.id}/{ann.id}_{ann.file_name}"
                            try:
                                # Open and read the file content
                                ann.file.open("rb")
                                file_content = ann.file.read()
                                ann.file.close()
                                zf.writestr(file_path, file_content)
                            except Exception as e:
                                # Log error but continue with other annotations
                                import logging

                                logger = logging.getLogger(__name__)
                                logger.warning(f"Failed to add annotation file {file_path}: {e}")

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
            "geojson": "application/geo+json",
            "gpx": "application/gpx+xml",
            "kml": "application/vnd.google-earth.kml+xml",
            "csv": "text/csv",
            "zip": "application/zip",
        }

        extensions = {
            "geojson": "geojson",
            "gpx": "gpx",
            "kml": "kml",
            "csv": "csv",
            "zip": "zip",
        }

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"geoannotator_export_{timestamp}.{extensions[format]}"

        response = HttpResponse(
            content=content,
            content_type=content_types.get(format, "application/octet-stream"),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


class ImportService:
    """Service for importing GPS points from various formats."""

    @staticmethod
    def import_geojson(file_content: str, user: User, merge_strategy: str = "create_new") -> dict:
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
            "total_points": 0,
            "imported_points": 0,
            "skipped_points": 0,
            "failed_points": 0,
            "errors": [],
            "created_point_ids": [],
        }

        try:
            data = json.loads(file_content)
        except json.JSONDecodeError as e:
            result["errors"].append(
                {
                    "line_number": 0,
                    "error": "INVALID_JSON",
                    "message": str(e),
                }
            )
            return result

        features = data.get("features", [])
        result["total_points"] = len(features)

        for idx, feature in enumerate(features, start=1):
            try:
                geometry = feature.get("geometry", {})
                properties = feature.get("properties", {})

                if geometry.get("type") != "Point":
                    raise ValueError("Only Point geometries are supported")

                coords = geometry.get("coordinates", [])
                if len(coords) < 2:
                    raise ValueError("Invalid coordinates")

                longitude, latitude = coords[0], coords[1]

                # Validate coordinates
                if not (-180 <= longitude <= 180):
                    raise ValueError(f"Longitude out of range: {longitude}")
                if not (-90 <= latitude <= 90):
                    raise ValueError(f"Latitude out of range: {latitude}")

                # Check for duplicates
                if merge_strategy == "skip":
                    from django.contrib.gis.geos import Point

                    location = Point(longitude, latitude, srid=4326)
                    existing = GPSPoint.objects.filter(
                        owner=user,
                        location__distance_lte=(location, 1),  # Within 1 meter
                    ).first()

                    if existing:
                        result["skipped_points"] += 1
                        continue
                elif merge_strategy == "replace":
                    from django.contrib.gis.geos import Point

                    location = Point(longitude, latitude, srid=4326)
                    existing = GPSPoint.objects.filter(
                        owner=user,
                        location__distance_lte=(location, 1),  # Within 1 meter
                    ).first()

                    if existing:
                        # Get or create point type
                        point_type = None
                        point_type_name = properties.get("point_type")
                        if point_type_name:
                            from apps.points.models import PointType

                            # Try to find existing type (base type or user's custom type)
                            point_type = (
                                PointType.objects.filter(names__en=point_type_name, status="active")
                                .filter(models.Q(type_choice="base") | models.Q(owner=user))
                                .first()
                            )

                            if not point_type:
                                # Create new custom type with default marker
                                point_type = PointType.objects.create(
                                    type_choice="custom",
                                    names={"en": point_type_name},
                                    creation_language="en",
                                    icon=properties.get("point_type_icon", "📍"),
                                    owner=user,
                                    visibility="private",
                                    status="active",
                                )

                        # Update existing point
                        existing.title = properties.get("title", "Imported Point")
                        existing.description = properties.get("description")
                        existing.is_public = properties.get("is_public", False)
                        if point_type:
                            existing.type = point_type
                        existing.save()

                        # Update tags
                        tags = properties.get("tags", [])
                        if tags:
                            existing.tags.clear()
                            for tag_name in tags:
                                tag = Tag.get_or_create_tag(name=tag_name, owner=user)
                                existing.tags.add(tag)

                        result["imported_points"] += 1
                        result["created_point_ids"].append(str(existing.id))
                        continue

                # Get or create point type
                point_type = None
                point_type_name = properties.get("point_type")
                if point_type_name:
                    from apps.points.models import PointType

                    # Try to find existing type (base type or user's custom type)
                    point_type = (
                        PointType.objects.filter(names__en=point_type_name, status="active")
                        .filter(models.Q(type_choice="base") | models.Q(owner=user))
                        .first()
                    )

                    if not point_type:
                        # Create new custom type with default marker
                        point_type = PointType.objects.create(
                            type_choice="custom",
                            names={"en": point_type_name},
                            creation_language="en",
                            icon=properties.get("point_type_icon", "📍"),
                            owner=user,
                            visibility="private",
                            status="active",
                        )

                # Create point

                point = PointService.create_point(
                    title=properties.get("title", "Imported Point"),
                    latitude=latitude,
                    longitude=longitude,
                    owner=user,
                    description=properties.get("description"),
                    tags=properties.get("tags", []),
                    is_public=properties.get("is_public", False),
                )

                # Set point type if found/created
                if point_type:
                    point.type = point_type
                    point.save(update_fields=["type"])

                result["imported_points"] += 1
                result["created_point_ids"].append(str(point.id))

            except Exception as e:
                result["failed_points"] += 1
                result["errors"].append(
                    {
                        "line_number": idx,
                        "error": "IMPORT_ERROR",
                        "message": str(e),
                    }
                )

        return result

    @staticmethod
    def import_csv(file_content: str, user: User, merge_strategy: str = "create_new") -> dict:
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
            "total_points": 0,
            "imported_points": 0,
            "skipped_points": 0,
            "failed_points": 0,
            "errors": [],
            "created_point_ids": [],
        }

        try:
            reader = csv.DictReader(StringIO(file_content))
            rows = list(reader)
            result["total_points"] = len(rows)

            for idx, row in enumerate(rows, start=2):  # Start at 2 (1 is header)
                try:
                    # Required fields
                    lat_str = row.get("latitude", "").strip()
                    lon_str = row.get("longitude", "").strip()

                    if not lat_str:
                        raise ValueError("Latitude is required")
                    if not lon_str:
                        raise ValueError("Longitude is required")

                    latitude = float(lat_str)
                    longitude = float(lon_str)
                    title = row.get("title", "").strip()

                    if not title:
                        raise ValueError("Title is required")

                    # Validate coordinates
                    if not (-180 <= longitude <= 180):
                        raise ValueError(f"Longitude out of range: {longitude}")
                    if not (-90 <= latitude <= 90):
                        raise ValueError(f"Latitude out of range: {latitude}")

                    # Optional fields
                    description = row.get("description", "").strip() or None
                    is_public = row.get("is_public", "false").lower() in ["true", "1", "yes"]
                    tags = [t.strip() for t in row.get("tags", "").split("|") if t.strip()]

                    # Get or create point type
                    point_type = None
                    point_type_name = row.get("point_type", "").strip()
                    if point_type_name:
                        from apps.points.models import PointType

                        # Try to find existing type (base type or user's custom type)
                        point_type = (
                            PointType.objects.filter(names__en=point_type_name, status="active")
                            .filter(models.Q(type_choice="base") | models.Q(owner=user))
                            .first()
                        )

                        if not point_type:
                            # Create new custom type with default marker
                            point_type = PointType.objects.create(
                                type_choice="custom",
                                names={"en": point_type_name},
                                creation_language="en",
                                icon="📍",
                                owner=user,
                                visibility="private",
                                status="active",
                            )

                    # Check for duplicates
                    if merge_strategy == "skip":
                        from django.contrib.gis.geos import Point

                        location = Point(longitude, latitude, srid=4326)
                        existing = GPSPoint.objects.filter(
                            owner=user,
                            location__distance_lte=(location, 1),  # Within 1 meter
                        ).first()

                        if existing:
                            result["skipped_points"] += 1
                            continue
                    elif merge_strategy == "replace":
                        from django.contrib.gis.geos import Point

                        location = Point(longitude, latitude, srid=4326)
                        existing = GPSPoint.objects.filter(
                            owner=user,
                            location__distance_lte=(location, 1),  # Within 1 meter
                        ).first()

                        if existing:
                            # Update existing point
                            existing.title = title
                            existing.description = description
                            existing.is_public = is_public
                            if point_type:
                                existing.type = point_type
                            existing.save()

                            # Update tags
                            if tags:
                                from apps.points.models import Tag

                                existing.tags.clear()
                                for tag_name in tags:
                                    tag = Tag.get_or_create_tag(name=tag_name, owner=user)
                                    existing.tags.add(tag)

                            result["imported_points"] += 1
                            result["created_point_ids"].append(str(existing.id))
                            continue

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

                    # Set point type if found/created
                    if point_type:
                        point.type = point_type
                        point.save(update_fields=["type"])

                    result["imported_points"] += 1
                    result["created_point_ids"].append(str(point.id))

                except Exception as e:
                    result["failed_points"] += 1
                    result["errors"].append(
                        {
                            "line_number": idx,
                            "error": "IMPORT_ERROR",
                            "message": str(e),
                        }
                    )

        except Exception as e:
            result["errors"].append(
                {
                    "line_number": 0,
                    "error": "INVALID_CSV",
                    "message": str(e),
                }
            )

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
            "total_points": 0,
            "imported_points": 0,
            "skipped_points": 0,
            "failed_points": 0,
            "errors": [],
            "created_point_ids": [],
        }

        try:
            gpx = gpxpy.parse(file_content)
            waypoints = gpx.waypoints
            result["total_points"] = len(waypoints)

            for idx, waypoint in enumerate(waypoints, start=1):
                try:
                    from apps.points.services import PointService

                    point = PointService.create_point(
                        title=waypoint.name or f"Waypoint {idx}",
                        latitude=waypoint.latitude,
                        longitude=waypoint.longitude,
                        owner=user,
                        description=waypoint.description,
                        tags=[],
                        is_public=False,
                    )

                    result["imported_points"] += 1
                    result["created_point_ids"].append(str(point.id))

                except Exception as e:
                    result["failed_points"] += 1
                    result["errors"].append(
                        {
                            "line_number": idx,
                            "error": "IMPORT_ERROR",
                            "message": str(e),
                        }
                    )

        except Exception as e:
            result["errors"].append(
                {
                    "line_number": 0,
                    "error": "INVALID_GPX",
                    "message": str(e),
                }
            )

        return result

    @staticmethod
    def import_kml(file_content: str, user: User, merge_strategy: str = "create_new") -> dict:
        """
        Import points from KML.

        Args:
            file_content: KML XML string
            user: User importing points
            merge_strategy: 'create_new', 'skip', or 'replace'

        Returns:
            dict: Import result
        """
        result = {
            "total_points": 0,
            "imported_points": 0,
            "skipped_points": 0,
            "failed_points": 0,
            "errors": [],
            "created_point_ids": [],
        }

        try:
            # Parse KML XML
            root = ET.fromstring(file_content)

            # KML namespace
            ns = {"kml": "http://www.opengis.net/kml/2.2"}

            # Find all Placemark elements (can work with or without namespace)
            placemarks = root.findall(".//kml:Placemark", ns)
            if not placemarks:
                # Try without namespace (some KML files don't use it)
                placemarks = root.findall(".//Placemark")

            result["total_points"] = len(placemarks)

            for idx, placemark in enumerate(placemarks, start=1):
                try:
                    # Extract name (title)
                    name_elem = placemark.find(".//{http://www.opengis.net/kml/2.2}name")
                    if name_elem is None:
                        name_elem = placemark.find(".//name")
                    title = (
                        name_elem.text
                        if name_elem is not None and name_elem.text
                        else f"KML Point {idx}"
                    )

                    # Extract description
                    desc_elem = placemark.find(".//{http://www.opengis.net/kml/2.2}description")
                    if desc_elem is None:
                        desc_elem = placemark.find(".//description")
                    description = (
                        desc_elem.text if desc_elem is not None and desc_elem.text else None
                    )

                    # Extract coordinates from Point geometry
                    # Use explicit namespace syntax for better compatibility
                    coord_elem = placemark.find(".//{http://www.opengis.net/kml/2.2}coordinates")
                    if coord_elem is None:
                        # Try without namespace (for KML files without namespace)
                        coord_elem = placemark.find(".//coordinates")
                    if coord_elem is None:
                        raise ValueError("No Point coordinates found")

                    coords_text = coord_elem.text.strip()
                    # KML format: longitude,latitude[,altitude]
                    coords = coords_text.split(",")
                    if len(coords) < 2:
                        raise ValueError("Invalid coordinates format")

                    longitude = float(coords[0])
                    latitude = float(coords[1])

                    # Validate coordinates
                    if not (-180 <= longitude <= 180):
                        raise ValueError(f"Longitude out of range: {longitude}")
                    if not (-90 <= latitude <= 90):
                        raise ValueError(f"Latitude out of range: {latitude}")

                    # Extract extended data (tags, is_public, etc.)
                    extended_data = {}
                    ext_data_elem = placemark.find(
                        ".//{http://www.opengis.net/kml/2.2}ExtendedData"
                    )
                    if ext_data_elem is None:
                        ext_data_elem = placemark.find(".//ExtendedData")
                    if ext_data_elem is not None:
                        data_elems = ext_data_elem.findall(
                            ".//{http://www.opengis.net/kml/2.2}Data"
                        )
                        if not data_elems:
                            data_elems = ext_data_elem.findall(".//Data")
                        for data_elem in data_elems:
                            name = data_elem.get("name")
                            value_elem = data_elem.find(".//{http://www.opengis.net/kml/2.2}value")
                            if value_elem is None:
                                value_elem = data_elem.find(".//value")
                            if name and value_elem is not None:
                                extended_data[name] = value_elem.text

                    # Parse extended data
                    is_public = extended_data.get("is_public", "false").lower() in [
                        "true",
                        "1",
                        "yes",
                    ]
                    tags_str = extended_data.get("tags", "")
                    tags = [t.strip() for t in tags_str.replace(",", "|").split("|") if t.strip()]

                    # Get or create point type
                    point_type = None
                    point_type_name = extended_data.get("point_type", "").strip()
                    if point_type_name:
                        from apps.points.models import PointType

                        # Try to find existing type (base type or user's custom type)
                        point_type = (
                            PointType.objects.filter(names__en=point_type_name, status="active")
                            .filter(models.Q(type_choice="base") | models.Q(owner=user))
                            .first()
                        )

                        if not point_type:
                            # Create new custom type with default marker
                            point_type_icon = extended_data.get("point_type_icon", "📍")
                            point_type = PointType.objects.create(
                                type_choice="custom",
                                names={"en": point_type_name},
                                creation_language="en",
                                icon=point_type_icon,
                                owner=user,
                                visibility="private",
                                status="active",
                            )

                    # Check for duplicates
                    if merge_strategy == "skip":
                        from django.contrib.gis.geos import Point

                        location = Point(longitude, latitude, srid=4326)
                        existing = GPSPoint.objects.filter(
                            owner=user,
                            location__distance_lte=(location, 1),  # Within 1 meter
                        ).first()

                        if existing:
                            result["skipped_points"] += 1
                            continue
                    elif merge_strategy == "replace":
                        from django.contrib.gis.geos import Point

                        location = Point(longitude, latitude, srid=4326)
                        existing = GPSPoint.objects.filter(
                            owner=user,
                            location__distance_lte=(location, 1),  # Within 1 meter
                        ).first()

                        if existing:
                            # Update existing point
                            existing.title = title
                            existing.description = description
                            existing.is_public = is_public
                            if point_type:
                                existing.type = point_type
                            existing.save()

                            # Update tags
                            if tags:
                                from apps.points.models import Tag

                                existing.tags.clear()
                                for tag_name in tags:
                                    tag = Tag.get_or_create_tag(name=tag_name, owner=user)
                                    existing.tags.add(tag)

                            result["imported_points"] += 1
                            result["created_point_ids"].append(str(existing.id))
                            continue

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

                    # Set point type if found/created
                    if point_type:
                        point.type = point_type
                        point.save(update_fields=["type"])

                    result["imported_points"] += 1
                    result["created_point_ids"].append(str(point.id))

                except Exception as e:
                    result["failed_points"] += 1
                    result["errors"].append(
                        {
                            "line_number": idx,
                            "error": "IMPORT_ERROR",
                            "message": str(e),
                        }
                    )

        except Exception as e:
            result["errors"].append(
                {
                    "line_number": 0,
                    "error": "INVALID_KML",
                    "message": str(e),
                }
            )

        return result

    @staticmethod
    def import_zip(file_content: bytes, user: User, merge_strategy: str = "create_new") -> dict:
        """
        Import points and annotations from ZIP file.

        Args:
            file_content: ZIP file bytes
            user: User importing points
            merge_strategy: 'create_new', 'skip', or 'replace'

        Returns:
            dict: Import result
        """
        result = {
            "total_points": 0,
            "imported_points": 0,
            "skipped_points": 0,
            "failed_points": 0,
            "errors": [],
            "created_point_ids": [],
        }

        try:
            # Extract ZIP file
            zip_buffer = BytesIO(file_content)

            with zipfile.ZipFile(zip_buffer, "r") as zf:
                # Find the points file (should be points.geojson)
                points_file = None
                for filename in zf.namelist():
                    if filename.endswith(".geojson") and "points" in filename.lower():
                        points_file = filename
                        break

                if not points_file:
                    raise ValueError("No points.geojson file found in ZIP archive")

                # Read and import points
                geojson_content = zf.read(points_file).decode("utf-8")

                # First pass: import points and build ID mapping
                points_result = ImportService.import_geojson(geojson_content, user, merge_strategy)
                result.update(points_result)

                # Parse GeoJSON to get point IDs and annotation references
                geojson_data = json.loads(geojson_content)
                features = geojson_data.get("features", [])

                # Build mapping from original point IDs to new point IDs
                id_mapping = {}
                if len(features) == len(points_result["created_point_ids"]):
                    for idx, feature in enumerate(features):
                        original_id = feature.get("id")
                        if original_id and idx < len(points_result["created_point_ids"]):
                            new_id = points_result["created_point_ids"][idx]
                            id_mapping[str(original_id)] = new_id

                # Second pass: import annotation files
                annotation_count = 0
                for filename in zf.namelist():
                    if filename.startswith("annotations/") and not filename.endswith("/"):
                        try:
                            # Extract point ID from path: annotations/{point_id}/{annotation_id}_{filename}
                            parts = filename.split("/")
                            if len(parts) >= 3:
                                original_point_id = parts[1]
                                file_name = parts[2]

                                # Get the new point ID
                                new_point_id = id_mapping.get(original_point_id)
                                if not new_point_id:
                                    continue

                                # Get the point
                                point = GPSPoint.objects.filter(id=new_point_id).first()
                                if not point:
                                    continue

                                # Extract annotation ID and actual filename
                                # Format: {annotation_id}_{filename}
                                ann_parts = file_name.split("_", 1)
                                actual_filename = ann_parts[1] if len(ann_parts) > 1 else file_name

                                # Read file content
                                file_content = zf.read(filename)

                                # Determine MIME type based on extension
                                import mimetypes

                                mime_type, _ = mimetypes.guess_type(actual_filename)

                                # Determine annotation type
                                if mime_type:
                                    if mime_type.startswith("image/"):
                                        ann_type = "image"
                                    elif mime_type == "application/pdf":
                                        ann_type = "document"
                                    else:
                                        ann_type = "file"
                                else:
                                    ann_type = "file"

                                # Create annotation with file
                                from django.core.files.base import ContentFile

                                annotation = Annotation.objects.create(
                                    gps_point=point,
                                    type=ann_type,
                                    file_name=actual_filename,
                                    file_size=len(file_content),
                                    mime_type=mime_type or "application/octet-stream",
                                    order=annotation_count,
                                )
                                annotation.file.save(actual_filename, ContentFile(file_content))
                                annotation_count += 1

                        except Exception as e:
                            # Log error but continue importing other files
                            print(f"Failed to import annotation {filename}: {e}")

        except Exception as e:
            result["errors"].append(
                {
                    "line_number": 0,
                    "error": "INVALID_ZIP",
                    "message": str(e),
                }
            )

        return result
