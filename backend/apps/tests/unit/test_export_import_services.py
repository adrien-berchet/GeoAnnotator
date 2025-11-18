import io
import json
import zipfile

import gpxpy.gpx
import pytest

from apps.export_import.services import ExportService
from apps.export_import.services import ImportService
from apps.points.models import GPSPoint


@pytest.mark.django_db
def test_export_geojson_with_annotations(gps_point_alice, text_annotation, tag_hiking):
    # Associer un tag et s'assurer des timestamps
    gps_point_alice.tags.add(tag_hiking)

    geojson_str = ExportService.export_geojson([gps_point_alice], include_annotations=True)
    data = json.loads(geojson_str)

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    feature = data["features"][0]

    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert feature["properties"]["title"] == gps_point_alice.title
    assert feature["properties"]["owner"] == gps_point_alice.owner.email
    assert "created_at" in feature["properties"]
    assert "updated_at" in feature["properties"]
    # tags
    assert feature["properties"]["tags"] == [tag_hiking.name]
    # annotations (text only included with text_content; file_name None)
    annotations = feature["properties"].get("annotations", [])
    assert len(annotations) >= 1
    ann = annotations[0]
    assert ann["type"] == "text"
    assert ann["text_content"] is not None
    assert ann["file_name"] is None


@pytest.mark.django_db
def test_export_csv_headers_and_rows(gps_point_alice, tag_hiking):
    gps_point_alice.tags.add(tag_hiking)
    csv_str = ExportService.export_csv([gps_point_alice])

    lines = [line for line in csv_str.strip().splitlines() if line]
    assert lines[0].split(",")[:5] == [
        "id",
        "title",
        "description",
        "latitude",
        "longitude",
    ]
    assert len(lines) == 2


@pytest.mark.django_db
def test_get_export_response_defaults_and_custom_name():
    content = "id,title\n1,Test\n"
    resp = ExportService.get_export_response(content, format="csv")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "text/csv"
    assert resp["Content-Disposition"].endswith('.csv"')

    custom = ExportService.get_export_response("{}", format="geojson", filename="mydump.geojson")
    assert custom["Content-Disposition"].endswith('mydump.geojson"')
    assert custom["Content-Type"] == "application/geo+json"


@pytest.mark.django_db
def test_import_geojson_success_create_new(alice):
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-122.6765, 45.5231]},
                "properties": {
                    "title": "Imported 1",
                    "description": "Desc",
                    "is_public": True,
                    "tags": ["t1", "t2"],
                },
            }
        ],
    }
    res = ImportService.import_geojson(json.dumps(geojson), user=alice, merge_strategy="create_new")

    assert res["total_points"] == 1
    assert res["imported_points"] == 1
    assert res["failed_points"] == 0
    assert len(res["created_point_ids"]) == 1

    # Le point a bien été créé
    created_id = res["created_point_ids"][0]
    p = GPSPoint.objects.get(id=created_id)
    assert p.title == "Imported 1"
    assert p.is_public is True
    assert {t.name for t in p.tags.all()} == {"t1", "t2"}


@pytest.mark.django_db
def test_import_geojson_invalid_json(alice):
    res = ImportService.import_geojson("not a json", user=alice)
    assert res["total_points"] == 0
    assert res["imported_points"] == 0
    assert res["failed_points"] == 0
    assert res["errors"][0]["error"] == "INVALID_JSON"


@pytest.mark.django_db
def test_import_csv_missing_fields_errors(alice):
    # Manque longitude (ligne 2) et manque title (ligne 3)
    csv_content = """latitude,longitude,title,description,tags
45.0,,Title 1,Desc,a|b
45.1,-122.7,,Desc2,
"""
    res = ImportService.import_csv(csv_content, user=alice)
    assert res["total_points"] == 2
    assert res["imported_points"] == 0
    assert res["failed_points"] == 2
    errs = [e["message"] for e in res["errors"]]
    assert any("Longitude is required" in m for m in errs)
    assert any("Title is required" in m for m in errs)


@pytest.mark.django_db
def test_import_gpx_success_and_invalid(alice):
    gpx = gpxpy.gpx.GPX()
    wpt = gpxpy.gpx.GPXWaypoint(latitude=45.5231, longitude=-122.6765, name="WP1")
    gpx.waypoints.append(wpt)
    xml = gpx.to_xml()

    ok = ImportService.import_gpx(xml, user=alice)
    assert ok["total_points"] == 1
    assert ok["imported_points"] == 1

    bad = ImportService.import_gpx("<notgpx>", user=alice)
    assert bad["errors"][0]["error"] == "INVALID_GPX"


@pytest.mark.django_db
def test_import_kml_success_basic(alice):
    kml = """
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>My KML</name>
      <description>Desc</description>
      <Point>
        <coordinates>-122.6765,45.5231,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>
"""
    res = ImportService.import_kml(kml, user=alice)
    assert res["total_points"] == 1
    assert res["imported_points"] == 1


@pytest.mark.django_db
def test_export_zip_includes_files(gps_point_alice, image_annotation, document_annotation):
    # Exporter un zip avec points.geojson et fichiers d'annotations
    zbytes = ExportService.export_zip([gps_point_alice], include_annotations=True)
    assert isinstance(zbytes, io.BytesIO)

    with zipfile.ZipFile(zbytes, "r") as zf:
        names = zf.namelist()
        assert any(n.endswith("points.geojson") for n in names)
        # Deux fichiers d'annotations (image + document)
        ann_files = [n for n in names if n.startswith("annotations/")]
        assert len(ann_files) >= 2
        # Contenu lisible
        for n in ann_files:
            data = zf.read(n)
            assert len(data) > 0


@pytest.mark.django_db
def test_import_zip_points_and_annotations(alice, clear_media_files):
    # Construire un ZIP en mémoire avec 1 point et 1 fichier d'annotation image
    orig_point_id = "orig-1"
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": orig_point_id,
                "geometry": {"type": "Point", "coordinates": [-122.6765, 45.5231]},
                "properties": {"title": "P1", "description": "D", "tags": ["x"]},
            }
        ],
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("points.geojson", json.dumps(geojson))
        # Fichier d'annotation: annotations/{point_id}/{annotation_id}_{filename}
        zf.writestr(f"annotations/{orig_point_id}/12345_photo.jpg", b"fakejpegbytes")

    content = buf.getvalue()
    res = ImportService.import_zip(content, user=alice, merge_strategy="create_new")

    # 1 point importé
    assert res["total_points"] == 1
    # Import ZIP réutilise le résultat geojson via update(); imported_points est présent
    assert "imported_points" in res

    # Vérifier qu'au moins un point existe et possède une annotation image
    pts = GPSPoint.objects.filter(owner=alice)
    assert pts.count() >= 1
    p = pts.first()
    anns = p.annotations.all()
    assert anns.count() >= 1
    a = anns.first()
    assert a.type in ("image", "file")
    assert a.file_name.endswith("photo.jpg")
    assert a.file and a.file.size > 0
