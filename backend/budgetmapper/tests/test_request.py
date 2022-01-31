import csv
import io
import random
from codecs import getreader
from datetime import datetime
from unittest.mock import patch

import freezegun
from budgetmapper import models
from budgetmapper.views import CreatedAtPagination
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from . import factories

datetime_format = settings.REST_FRAMEWORK.get("DATETIME_FORMAT", "%Y-%m-%dT%H:%M:%S.%fZ")


class TestCsvDownload(TestCase):
    def test_request(self):
        cln = factories.ClassificationLevelNameListFactory(names=["a", "b"])
        cs = factories.ClassificationSystemFactory(level_names=cln)
        bud = factories.BudgetFactory(classification_system=cs)
        cl0 = factories.ClassificationFactory(classification_system=cs, code="1")
        cl00 = factories.ClassificationFactory(classification_system=cs, parent=cl0, code="1.1")
        cl01 = factories.ClassificationFactory(classification_system=cs, parent=cl0, code="1.2")
        cl1 = factories.ClassificationFactory(classification_system=cs, code="2")
        cl10 = factories.ClassificationFactory(classification_system=cs, parent=cl1, code="2.1")
        abi00 = factories.AtomicBudgetItemFactory(amount=123, budget=bud, classification=cl00)
        abi01 = factories.AtomicBudgetItemFactory(amount=125, budget=bud, classification=cl01)
        abi10 = factories.AtomicBudgetItemFactory(amount=127, budget=bud, classification=cl10)

        c = Client()
        res = c.get(f"/transfer/csv/{bud.id}")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.streaming)
        expected = [
            ["a", "a名称", "b", "b名称", "金額"],
            [cl0.code, cl0.name, cl00.code, cl00.name, str(abi00.value)],
            [cl0.code, cl0.name, cl01.code, cl01.name, str(abi01.value)],
            [cl1.code, cl1.name, cl10.code, cl10.name, str(abi10.value)],
        ]
        actual = list(csv.reader(getreader("utf-8")(io.BytesIO(res.getvalue()))))
        self.assertEqual(actual, expected)


class GovernmentCrudTestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self._user_username = "testuser"
        self._user_password = "5up9rSecre+"
        user = User.objects.create(username=self._user_username)
        user.set_password(self._user_password)
        user.save()

    def test_list(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        govs = [factories.GovernmentFactory() for i in range(100)]
        res = self.client.get("/api/v1/governments/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": gov.id,
                "name": gov.name,
                "slug": gov.slug,
                "latitude": gov.latitude,
                "longitude": gov.longitude,
                "createdAt": gov.created_at.strftime(datetime_format),
                "updatedAt": gov.updated_at.strftime(datetime_format),
            }
            for gov in sorted(
                govs, key=lambda gov: getattr(gov, ordering.strip("-")), reverse=ordering.startswith("-")
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_retrieve(self):
        govs = [factories.GovernmentFactory() for i in range(100)]
        gov = govs[random.randint(0, 100)]
        res = self.client.get(f"/api/v1/governments/{gov.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id": gov.id,
            "name": gov.name,
            "slug": gov.slug,
            "latitude": gov.latitude,
            "longitude": gov.longitude,
            "createdAt": gov.created_at.strftime(datetime_format),
            "updatedAt": gov.updated_at.strftime(datetime_format),
        }
        actual = res.json()
        self.assertEqual(actual, expected)

    def test_create_requires_authentication(self):
        query = {"name": "まほろ市"}
        res = self.client.post(f"/api/v1/governments/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890")
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_default(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {"name": "まほろ市"}
            res = self.client.post(f"/api/v1/governments/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            expected = {
                "id": "ab12345678901234567890",
                "name": "まほろ市",
                "slug": "theslug",
                "latitude": None,
                "longitude": None,
                "createdAt": dt.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)

    @patch("budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890")
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_specified_values(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {"name": "まほろ市", "slug": "mahoro-city", "latitude": -54, "longitude": 170}
            res = self.client.post(f"/api/v1/governments/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            expected = {
                "id": "ab12345678901234567890",
                "name": "まほろ市",
                "slug": "mahoro-city",
                "latitude": -54,
                "longitude": 170,
                "createdAt": dt.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)

    def test_destroy_requires_login(self):
        govs = [factories.GovernmentFactory() for i in range(100)]
        gov = govs[random.randint(0, 100)]
        res = self.client.delete(f"/api/v1/governments/{gov.id}/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy(self):
        govs = [factories.GovernmentFactory() for i in range(100)]
        gov = govs[random.randint(0, 100)]
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/governments/{gov.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(models.Government.DoesNotExist):
            models.Government.objects.get(id=gov.id)

    def test_update_requires_login(self):
        govs = [factories.GovernmentFactory() for i in range(100)]
        gov = govs[random.randint(0, 100)]
        res = self.client.put(f"/api/v1/governments/{gov.id}/", {"slug": ""}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_update_blank_slug(self, jp_slugify):
        gov = factories.GovernmentFactory(slug="someslug")
        self.client.login(username=self._user_username, password=self._user_password)
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            res = self.client.put(f"/api/v1/governments/{gov.id}/", {"slug": None}, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            expected = {
                "id": gov.id,
                "name": gov.name,
                "slug": "theslug",
                "latitude": gov.latitude,
                "longitude": gov.longitude,
                "createdAt": gov.created_at.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)
