from unittest.mock import MagicMock, patch

from budgetmapper import serializers
from django.conf import settings
from django.test import TestCase

from . import factories

datetime_format = settings.REST_FRAMEWORK.get("DATETIME_FORMAT", "%Y-%m-%dT%H:%M:%S.%fZ")


class GovernmentSerializerTestCase(TestCase):
    def test_government_serializer(self):
        g = factories.GovernmentFactory()
        sut = serializers.GovernmentSerializer(instance=g)
        expected = {
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "latitude": g.latitude,
            "longitude": g.longitude,
            "created_at": g.created_at.strftime(datetime_format),
            "updated_at": g.updated_at.strftime(datetime_format),
        }
        actual = sut.data
        self.assertEqual(actual, expected)


class ClassificationLevelNameListDetailSerializerTestCase(TestCase):
    def test_classification_level_name_serializer(self):
        cln = factories.ClassificationLevelNameListFactory()
        sut = serializers.ClassificationLevelNameListDetailSerializer(instance=cln)
        expected = {
            "id": cln.id,
            "names": cln.names,
            "created_at": cln.created_at.strftime(datetime_format),
            "updated_at": cln.updated_at.strftime(datetime_format),
        }
        actual = sut.data
        self.assertEqual(actual, expected)


class ClassificationLevelNameListSerializerTestCase(TestCase):
    def test_classification_level_name_serializer(self):
        cln = factories.ClassificationLevelNameListFactory()
        sut = serializers.ClassificationLevelNameListSerializer(instance=cln)
        expected = {
            "names": cln.names,
        }
        actual = sut.data
        self.assertEqual(actual, expected)


class ClassificationSystemSerializerTestCase(TestCase):
    def test_classification_system_serializer(self):
        cs = factories.ClassificationSystemFactory()
        sut = serializers.ClassificationSystemSerializer(instance=cs)
        expected = {
            "id": cs.id,
            "slug": cs.slug,
            "name": cs.name,
            "level_names": {"names": cs.level_names.names},
            "created_at": cs.created_at.strftime(datetime_format),
            "updated_at": cs.updated_at.strftime(datetime_format),
        }
        actual = sut.data
        self.assertEqual(actual, expected)
