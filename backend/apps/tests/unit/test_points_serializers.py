import pytest
from django.test import override_settings

from apps.annotations.models import Annotation
from apps.points.models import GPSPoint
from apps.points.models import PointType
from apps.points.models import UserTypeOrder
from apps.points.serializers import CreateGPSPointSerializer
from apps.points.serializers import CreatePointTypeSerializer
from apps.points.serializers import EditingLockSerializer
from apps.points.serializers import GPSPointSerializer
from apps.points.serializers import PointTypeReorderSerializer
from apps.points.serializers import PointTypeSerializer
from apps.sharing.models import Share
from apps.trash.models import AnnotationTrash


@pytest.mark.django_db
def test_pointtype_serializer_validate_and_repr(alice, api_request_factory):
    # Lang code en majuscules -> erreur
    req = api_request_factory.get("/types")
    req.user = alice

    ser = PointTypeSerializer(
        data={
            "names": {"EN": "Forest"},
            "creation_language": "EN",
            "icon": "/media/icon.png",
            "visibility": "private",
        },
        context={"request": req},
    )
    assert not ser.is_valid()
    # erreurs sur names/creation_language
    errs = ser.errors
    assert "names" in errs or "creation_language" in errs

    # Cas valide puis représentation: URL absolue pour icon
    ser_ok = PointTypeSerializer(
        data={
            "names": {"en": "Forest"},
            "creation_language": "en",
            "icon": "/media/icon.png",
            "visibility": "private",
        },
        context={"request": req},
    )
    assert ser_ok.is_valid(), ser_ok.errors
    inst = ser_ok.save()  # create: owner=alice, type_choice=custom
    out = PointTypeSerializer(inst, context={"request": req}).data
    assert out["icon"].startswith("http://testserver/")


@pytest.mark.django_db
def test_create_pointtype_serializer_duplicates_and_limit(alice, api_request_factory):
    req = api_request_factory.get("/types")
    req.user = alice

    # Un type initial
    PointType.objects.create(
        names={"en": "Trail"}, creation_language="en", owner=alice, type_choice="custom"
    )

    # Dupliquer les names -> erreur
    s_dup = CreatePointTypeSerializer(
        data={"names": {"en": "Trail"}, "creation_language": "en"},
        context={"request": req},
    )
    assert not s_dup.is_valid()
    assert "names" in s_dup.errors

    # Limite à 1 -> créer un second échoue
    with override_settings(MAX_POINT_TYPES_PER_USER=1):
        s_limit = CreatePointTypeSerializer(
            data={"names": {"en": "Lake"}, "creation_language": "en"},
            context={"request": req},
        )
        assert not s_limit.is_valid()
        assert "names" in s_limit.errors


@pytest.mark.django_db
def test_pointtype_reorder_validate_and_save(alice, bob, api_request_factory):
    req = api_request_factory.get("/types/reorder")
    req.user = alice

    base = PointType.get_default_type()  # owner=None
    mine = PointType.objects.create(
        names={"en": "Cabin"}, creation_language="en", owner=alice, type_choice="custom"
    )
    others = PointType.objects.create(
        names={"en": "BobType"}, creation_language="en", owner=bob, type_choice="custom"
    )

    # Invalide: inclut un type d'un autre utilisateur
    ser_bad = PointTypeReorderSerializer(
        data={
            "order": [
                {"id": str(base.id), "order": "1"},
                {"id": str(others.id), "order": "2"},
            ]
        },
        context={"request": req},
    )
    assert not ser_bad.is_valid()

    # Valide: seulement types accessibles
    ser_ok = PointTypeReorderSerializer(
        data={
            "order": [
                {"id": str(base.id), "order": "1"},
                {"id": str(mine.id), "order": "2"},
            ]
        },
        context={"request": req},
    )
    assert ser_ok.is_valid(), ser_ok.errors
    result = ser_ok.save()
    assert result["success"] is True and result["updated"] == 2
    assert UserTypeOrder.objects.filter(user=alice).count() == 2


@pytest.mark.django_db
def test_editing_lock_serializer_expires_at(alice, gps_point_alice):
    gps_point_alice.editing_lock_user = alice
    from django.utils import timezone

    gps_point_alice.editing_lock_acquired_at = timezone.now()
    gps_point_alice.save()

    data = EditingLockSerializer(gps_point_alice).data
    assert data["expires_at"] is not None


@pytest.mark.django_db
def test_gpspoint_serializer_location_lock_and_permissions(
    alice, bob, public_gps_point_alice, api_request_factory
):
    # location getters
    s = GPSPointSerializer(public_gps_point_alice)
    assert s.data["latitude"] == public_gps_point_alice.location.y
    assert s.data["longitude"] == public_gps_point_alice.location.x
    assert s.data["location"]["type"] == "Point"

    # permission: anonyme -> view si public
    from django.contrib.auth.models import AnonymousUser

    req_anon = api_request_factory.get("/points")
    req_anon.user = AnonymousUser()
    out_anon = GPSPointSerializer(public_gps_point_alice, context={"request": req_anon}).data
    assert out_anon["permission"] == "view"

    # permission: owner
    req_owner = api_request_factory.get("/points")
    req_owner.user = alice
    out_owner = GPSPointSerializer(public_gps_point_alice, context={"request": req_owner}).data
    assert out_owner["permission"] == "owner"

    # permission: shared recipient (edit)
    Share.objects.create(
        gps_point=public_gps_point_alice,
        owner=alice,
        recipient_email="bob@example.com",
        recipient_user=bob,
        permission_level=Share.PERMISSION_EDIT,
        is_active=True,
    )
    req_bob = api_request_factory.get("/points")
    req_bob.user = bob
    out_bob = GPSPointSerializer(public_gps_point_alice, context={"request": req_bob}).data
    assert out_bob["permission"] == "edit"


@pytest.mark.django_db
def test_gpspoint_serializer_annotation_count_excludes_trashed(alice, gps_point_alice):
    ann = Annotation.objects.create(gps_point=gps_point_alice, type="text", text_content="x")
    # le mettre à la corbeille
    AnnotationTrash.objects.create(annotation=ann, deleted_by=alice)

    s = GPSPointSerializer(gps_point_alice)
    assert s.data["annotation_count"] == 0


@pytest.mark.django_db
def test_create_gpspoint_serializer_creates_with_tags(alice, api_request_factory):
    req = api_request_factory.post("/points")
    req.user = alice

    ser = CreateGPSPointSerializer(
        data={
            "title": "P1",
            "description": "D",
            "latitude": 45.5,
            "longitude": -122.6,
            "tags": ["A", "b"],
            "is_public": True,
        },
        context={"request": req},
    )
    assert ser.is_valid(), ser.errors
    p = ser.save()
    assert isinstance(p, GPSPoint)
    assert p.is_public is True
    # Tags preserve original casing
    assert {t.name for t in p.tags.all()} == {"A", "b"}


@pytest.mark.django_db
def test_update_gpspoint_serializer_updates_location_tags_and_type(
    alice, bob, gps_point_alice, api_request_factory
):
    # Créer deux types: un pour alice, un pour bob
    t_alice = PointType.objects.create(
        names={"en": "Spot"}, creation_language="en", owner=alice, type_choice="custom"
    )
    t_bob = PointType.objects.create(
        names={"en": "Other"}, creation_language="en", owner=bob, type_choice="custom"
    )

    from apps.points.serializers import UpdateGPSPointSerializer

    # mise à jour OK (location+tags+type)
    req = api_request_factory.patch("/points")
    req.user = alice
    ser_ok = UpdateGPSPointSerializer(
        gps_point_alice,
        data={
            "latitude": 45.0,
            "longitude": -122.0,
            "tags": ["x", "y"],
            "type_id": str(t_alice.id),
        },
        partial=True,
        context={"request": req},
    )
    assert ser_ok.is_valid(), ser_ok.errors
    p2 = ser_ok.save()
    assert round(p2.location.y, 3) == 45.000
    assert round(p2.location.x, 3) == -122.000
    assert {t.name for t in p2.tags.all()} == {"x", "y"}
    assert p2.type == t_alice

    # type d'un autre utilisateur -> erreur
    ser_bad = UpdateGPSPointSerializer(
        gps_point_alice,
        data={"type_id": str(t_bob.id)},
        partial=True,
        context={"request": req},
    )
    assert not ser_bad.is_valid()
    assert "type_id" in ser_bad.errors
