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
        cln = ["a", "b"]
        cs = factories.ClassificationSystemFactory(level_names=cln)
        bud = factories.BudgetFactory(classification_system=cs)
        cl0 = factories.ClassificationFactory(classification_system=cs, code="1")
        cl00 = factories.ClassificationFactory(classification_system=cs, parent=cl0, code="1.1")
        cl01 = factories.ClassificationFactory(classification_system=cs, parent=cl0, code="1.2")
        cl1 = factories.ClassificationFactory(classification_system=cs, code="2")
        cl10 = factories.ClassificationFactory(classification_system=cs, parent=cl1, code="2.1")
        abi00 = factories.AtomicBudgetItemFactory(value=123, budget=bud, classification=cl00)
        abi01 = factories.AtomicBudgetItemFactory(value=125, budget=bud, classification=cl01)
        abi10 = factories.AtomicBudgetItemFactory(value=127, budget=bud, classification=cl10)

        c = Client()
        res = c.get(f"/transfer/csv/{bud.id}")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.streaming)
        expected = [
            ["a", "a名称", "b", "b名称", "金額"],
            [cl0.code, cl0.name, cl00.code, cl00.name, str(abi00.amount)],
            [cl0.code, cl0.name, cl01.code, cl01.name, str(abi01.amount)],
            [cl1.code, cl1.name, cl10.code, cl10.name, str(abi10.amount)],
        ]
        actual = list(csv.reader(getreader("utf-8")(io.BytesIO(res.getvalue()))))
        self.assertEqual(actual, expected)


class BudgetMapperTestUserAPITestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self._user_username = "testuser"
        self._user_password = "5up9rSecre+"
        user = User.objects.create(username=self._user_username)
        user.set_password(self._user_password)
        user.save()


class WdmmgTestCase(BudgetMapperTestUserAPITestCase):
    def setUp(self):
        super(WdmmgTestCase, self).setUp()

    def test_no_list_route(self) -> None:
        bud = factories.BudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        res = self.client.get(f"/api/v1/wdmmg/", format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_create_route(self) -> None:
        res = self.client.post(f"/api/v1/wdmmg/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_returns_unauthorized_error_for_non_member(self) -> None:
        bud = factories.BudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        res = self.client.put(f"/api/v1/wdmmg/{bud.slug}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_returns_method_not_allowed_error_for_member(self) -> None:
        bud = factories.BudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.put(f"/api/v1/wdmmg/{bud.slug}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_destroy_returns_unauthorized_error_for_non_member(self) -> None:
        bud = factories.BudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        res = self.client.delete(f"/api/v1/wdmmg/{bud.slug}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy_returns_method_not_allowed_error_for_member(self) -> None:
        bud = factories.BudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/wdmmg/{bud.slug}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get(self) -> None:
        gov = factories.GovernmentFactory(name="まほろ市", slug="mahoro-city")
        cs = factories.ClassificationSystemFactory(name="まほろ市2101年一般会計", slug="mahoro-city-2101-ippan-kaikei")
        cl0 = factories.ClassificationFactory(classification_system=cs, code="1")
        cl00 = factories.ClassificationFactory(classification_system=cs, parent=cl0, code="1.1")
        cl000 = factories.ClassificationFactory(classification_system=cs, parent=cl00, code="1.1.1")
        cl001 = factories.ClassificationFactory(classification_system=cs, parent=cl00, code="1.1.2")
        cl002 = factories.ClassificationFactory(classification_system=cs, parent=cl00, code="1.1.3")
        cl01 = factories.ClassificationFactory(classification_system=cs, parent=cl0, code="1.2")
        cl010 = factories.ClassificationFactory(classification_system=cs, parent=cl01, code="1.2.1")
        cl1 = factories.ClassificationFactory(classification_system=cs, code="2")
        cl10 = factories.ClassificationFactory(classification_system=cs, parent=cl1, code="2.1")
        cl100 = factories.ClassificationFactory(classification_system=cs, parent=cl10, code="2.1.1")
        cl2 = factories.ClassificationFactory(classification_system=cs, code="10")
        cl20 = factories.ClassificationFactory(classification_system=cs, parent=cl2, code="10.1")
        cl200 = factories.ClassificationFactory(classification_system=cs, parent=cl20, code="10.1.1")
        bud = factories.BudgetFactory(
            name="まほろ市2101年度予算", slug="mahoro-city-2101", government=gov, classification_system=cs
        )

        abi000 = factories.AtomicBudgetItemFactory(value=123.0, budget=bud, classification=cl000)
        abi001 = factories.AtomicBudgetItemFactory(value=125.0, budget=bud, classification=cl001)
        abi002 = factories.AtomicBudgetItemFactory(value=127.0, budget=bud, classification=cl002)
        abi010 = factories.AtomicBudgetItemFactory(value=129.0, budget=bud, classification=cl010)
        abi100 = factories.AtomicBudgetItemFactory(value=131.0, budget=bud, classification=cl100)

        res = self.client.get(f"/api/v1/wdmmg/{bud.slug}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id": bud.id,
            "name": bud.name,
            "subtitle": bud.subtitle,
            "slug": bud.slug,
            "year": bud.year,
            "createdAt": bud.created_at.strftime(datetime_format),
            "updatedAt": bud.updated_at.strftime(datetime_format),
            "budgets": [
                {
                    "id": cl0.id,
                    "name": cl0.name,
                    "code": cl0.code,
                    "amount": 504.0,
                    "children": [
                        {
                            "id": cl00.id,
                            "name": cl00.name,
                            "code": cl00.code,
                            "amount": 375.0,
                            "children": [
                                {
                                    "id": cl000.id,
                                    "name": cl000.name,
                                    "code": cl000.code,
                                    "amount": 123.0,
                                    "children": None,
                                },
                                {
                                    "id": cl001.id,
                                    "name": cl001.name,
                                    "code": cl001.code,
                                    "amount": 125.0,
                                    "children": None,
                                },
                                {
                                    "id": cl002.id,
                                    "name": cl002.name,
                                    "code": cl002.code,
                                    "amount": 127.0,
                                    "children": None,
                                },
                            ],
                        },
                        {
                            "id": cl01.id,
                            "name": cl01.name,
                            "code": cl01.code,
                            "amount": 129.0,
                            "children": [
                                {
                                    "id": cl010.id,
                                    "name": cl010.name,
                                    "code": cl010.code,
                                    "amount": 129.0,
                                    "children": None,
                                }
                            ],
                        },
                    ],
                },
                {
                    "id": cl1.id,
                    "name": cl1.name,
                    "code": cl1.code,
                    "amount": 131.0,
                    "children": [
                        {
                            "id": cl10.id,
                            "name": cl10.name,
                            "code": cl10.code,
                            "amount": 131.0,
                            "children": [
                                {
                                    "id": cl100.id,
                                    "name": cl100.name,
                                    "code": cl100.code,
                                    "amount": 131.0,
                                    "children": None,
                                }
                            ],
                        }
                    ],
                },
                {
                    "id": cl2.id,
                    "name": cl2.name,
                    "code": cl2.code,
                    "amount": 0,
                    "children": [
                        {
                            "id": cl20.id,
                            "name": cl20.name,
                            "code": cl20.code,
                            "amount": 0,
                            "children": [
                                {
                                    "id": cl200.id,
                                    "name": cl200.name,
                                    "code": cl200.code,
                                    "amount": 0,
                                    "children": None,
                                }
                            ],
                        }
                    ],
                },
            ],
            "government": {
                "id": gov.id,
                "name": gov.name,
                "slug": gov.slug,
                "latitude": gov.latitude,
                "longitude": gov.longitude,
                "createdAt": gov.created_at.strftime(datetime_format),
                "updatedAt": gov.updated_at.strftime(datetime_format),
            },
        }
        actual = res.json()
        self.assertEqual(actual, expected)


class GovernmentCrudTestCase(BudgetMapperTestUserAPITestCase):
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
        gov = govs[random.randint(0, 99)]
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
        gov = govs[random.randint(0, 99)]
        res = self.client.delete(f"/api/v1/governments/{gov.id}/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy(self):
        govs = [factories.GovernmentFactory() for i in range(100)]
        gov = govs[random.randint(0, 99)]
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/governments/{gov.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(models.Government.DoesNotExist):
            models.Government.objects.get(id=gov.id)

    def test_update_requires_login(self):
        govs = [factories.GovernmentFactory() for i in range(100)]
        gov = govs[random.randint(0, 99)]
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


class ClassificationSystemCrudTestCase(BudgetMapperTestUserAPITestCase):
    def test_list(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        css = [factories.ClassificationSystemFactory() for i in range(100)]
        res = self.client.get("/api/v1/classification-systems/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": cs.id,
                "name": cs.name,
                "slug": cs.slug,
                "levelNames": cs.level_names,
                "createdAt": cs.created_at.strftime(datetime_format),
                "updatedAt": cs.updated_at.strftime(datetime_format),
            }
            for cs in sorted(css, key=lambda cs: getattr(cs, ordering.strip("-")), reverse=ordering.startswith("-"))[
                :page_size
            ]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_retrieve(self):
        css = [factories.ClassificationSystemFactory() for i in range(100)]
        cs = css[random.randint(0, 99)]
        res = self.client.get(f"/api/v1/classification-systems/{cs.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id": cs.id,
            "name": cs.name,
            "slug": cs.slug,
            "levelNames": cs.level_names,
            "items": [],
            "createdAt": cs.created_at.strftime(datetime_format),
            "updatedAt": cs.updated_at.strftime(datetime_format),
        }
        actual = res.json()
        self.assertEqual(actual, expected)

    def test_create_requires_authentication(self):
        query = {"name": "まほろ市予算"}
        res = self.client.post(f"/api/v1/classification-systems/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890")
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_default(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {"name": "まほろ市予算"}
            res = self.client.post(f"/api/v1/classification-systems/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            expected = {
                "id": "ab12345678901234567890",
                "name": "まほろ市予算",
                "slug": "theslug",
                "levelNames": models.get_default_level_name_list(),
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
            query = {"name": "まほろ市予算", "slug": "mahoro-city-budget", "levelNames": ["level1", "level2", "level3"]}
            res = self.client.post(f"/api/v1/classification-systems/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            expected = {
                "id": "ab12345678901234567890",
                "name": "まほろ市予算",
                "slug": "mahoro-city-budget",
                "levelNames": ["level1", "level2", "level3"],
                "createdAt": dt.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)

    def test_destroy_requires_login(self):
        css = [factories.ClassificationSystemFactory() for i in range(100)]
        cs = css[random.randint(0, 99)]
        res = self.client.delete(f"/api/v1/classification-systems/{cs.id}/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy(self):
        css = [factories.ClassificationSystemFactory() for i in range(100)]
        cs = css[random.randint(0, 99)]
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/classification-systems/{cs.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(models.ClassificationSystem.DoesNotExist):
            models.ClassificationSystem.objects.get(id=cs.id)

    def test_update_requires_login(self):
        css = [factories.ClassificationSystemFactory() for i in range(100)]
        cs = css[random.randint(0, 99)]
        res = self.client.put(f"/api/v1/classification-systems/{cs.id}/", {"slug": ""}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_update_blank_slug(self, jp_slugify):
        cs = factories.ClassificationSystemFactory(slug="someslug")
        self.client.login(username=self._user_username, password=self._user_password)
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            res = self.client.put(f"/api/v1/classification-systems/{cs.id}/", {"slug": None}, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            expected = {
                "id": cs.id,
                "name": cs.name,
                "slug": "theslug",
                "levelNames": cs.level_names,
                "createdAt": cs.created_at.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)


class BudgetCrudTestCase(BudgetMapperTestUserAPITestCase):
    def test_list(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        bs = [factories.BudgetFactory() for i in range(100)]
        res = self.client.get("/api/v1/budgets/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "year": b.year,
                "subtitle": b.subtitle,
                "classificationSystem": b.classification_system.id,
                "government": b.government.id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            for b in sorted(bs, key=lambda b: getattr(b, ordering.strip("-")), reverse=ordering.startswith("-"))[
                :page_size
            ]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_list_can_filter_by_government(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        govs = [factories.GovernmentFactory() for _ in range(4)]
        bs = [factories.BudgetFactory(government=govs[i % 4]) for i in range(100)]
        res = self.client.get(f"/api/v1/budgets/?government={govs[0].id}", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "year": b.year,
                "subtitle": b.subtitle,
                "classificationSystem": b.classification_system.id,
                "government": govs[0].id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            for b in sorted(
                [b for b in bs if b.government.id == govs[0].id],
                key=lambda b: getattr(b, ordering.strip("-")),
                reverse=ordering.startswith("-"),
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_list_can_filter_by_year(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        bs = [factories.BudgetFactory(year=(2000 + i // 10)) for i in range(100)]
        res = self.client.get(f"/api/v1/budgets/?year=2001", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "year": 2001,
                "subtitle": b.subtitle,
                "classificationSystem": b.classification_system.id,
                "government": b.government.id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            for b in sorted(
                [b for b in bs if b.year == 2001],
                key=lambda b: getattr(b, ordering.strip("-")),
                reverse=ordering.startswith("-"),
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_list_can_filter_by_government_and_year(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        govs = [factories.GovernmentFactory() for _ in range(4)]
        bs = [factories.BudgetFactory(government=govs[i % 4], year=(2000 + (i // 10))) for i in range(100)]
        res = self.client.get(f"/api/v1/budgets/?government={govs[0].id}&year=2001", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "year": 2001,
                "subtitle": b.subtitle,
                "classificationSystem": b.classification_system.id,
                "government": govs[0].id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            for b in sorted(
                [b for b in bs if b.government.id == govs[0].id and b.year == 2001],
                key=lambda b: getattr(b, ordering.strip("-")),
                reverse=ordering.startswith("-"),
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_retrieve(self):
        bs = [factories.BudgetFactory() for i in range(100)]
        b = bs[random.randint(0, 99)]
        res = self.client.get(f"/api/v1/budgets/{b.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id": b.id,
            "name": b.name,
            "slug": b.slug,
            "year": b.year,
            "subtitle": b.subtitle,
            "classificationSystem": {
                "id": b.classification_system.id,
                "name": b.classification_system.name,
                "slug": b.classification_system.slug,
                "levelNames": b.classification_system.level_names,
                "createdAt": b.classification_system.created_at.strftime(datetime_format),
                "updatedAt": b.classification_system.updated_at.strftime(datetime_format),
            },
            "government": {
                "id": b.government.id,
                "name": b.government.name,
                "slug": b.government.slug,
                "latitude": b.government.latitude,
                "longitude": b.government.longitude,
                "createdAt": b.government.created_at.strftime(datetime_format),
                "updatedAt": b.government.updated_at.strftime(datetime_format),
            },
            "items": [],
            "createdAt": b.created_at.strftime(datetime_format),
            "updatedAt": b.updated_at.strftime(datetime_format),
        }

        actual = res.json()
        self.assertEqual(actual, expected)

    def test_create_requires_authentication(self):
        gov = factories.GovernmentFactory()
        cs = factories.ClassificationSystemFactory()
        query = {"name": "まほろ市2101年度予算", "year": 2101, "government": gov.id, "classificationSystem": cs.id}
        res = self.client.post(f"/api/v1/budgets/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890")
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_default(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        gov = factories.GovernmentFactory()
        cs = factories.ClassificationSystemFactory()
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {"name": "まほろ市2101年度予算", "year": 2101, "government": gov.id, "classificationSystem": cs.id}
            res = self.client.post(f"/api/v1/budgets/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            expected = {
                "id": "ab12345678901234567890",
                "name": "まほろ市2101年度予算",
                "slug": "theslug",
                "year": 2101,
                "subtitle": None,
                "classificationSystem": cs.id,
                "government": gov.id,
                "createdAt": dt.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)

    @patch("budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890")
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_specified_values(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        gov = factories.GovernmentFactory()
        cs = factories.ClassificationSystemFactory()
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {
                "name": "まほろ市2101年度予算",
                "slug": "mahoro-city-2101-budget",
                "year": 2101,
                "subtitle": "第一次補正案",
                "government": gov.id,
                "classificationSystem": cs.id,
            }
            res = self.client.post(f"/api/v1/budgets/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            expected = {
                "id": "ab12345678901234567890",
                "name": "まほろ市2101年度予算",
                "slug": "mahoro-city-2101-budget",
                "year": 2101,
                "subtitle": "第一次補正案",
                "classificationSystem": cs.id,
                "government": gov.id,
                "createdAt": dt.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)

    def test_destroy_requires_login(self):
        bs = [factories.BudgetFactory() for i in range(100)]
        b = bs[random.randint(0, 99)]
        res = self.client.delete(f"/api/v1/budgets/{b.id}/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy(self):
        bs = [factories.BudgetFactory() for i in range(100)]
        b = bs[random.randint(0, 99)]
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/budgets/{b.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(models.Budget.DoesNotExist):
            models.Budget.objects.get(id=b.id)

    def test_update_requires_login(self):
        bs = [factories.BudgetFactory() for i in range(100)]
        b = bs[random.randint(0, 99)]
        res = self.client.put(f"/api/v1/budgets/{b.id}/", {"slug": ""}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_partial_update(self, jp_slugify):
        b = factories.BudgetFactory(slug="someslug")
        self.client.login(username=self._user_username, password=self._user_password)
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            res = self.client.patch(f"/api/v1/budgets/{b.id}/", {"slug": None}, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            expected = {
                "id": b.id,
                "name": b.name,
                "slug": "theslug",
                "year": b.year,
                "subtitle": b.subtitle,
                "classificationSystem": b.classification_system.id,
                "government": b.government.id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)


class AtomicBudgetItemCrudTestCase(BudgetMapperTestUserAPITestCase):
    def test_list(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        cs = factories.ClassificationSystemFactory()
        budget = factories.BudgetFactory(classification_system=cs)
        budget_items = [
            factories.AtomicBudgetItemFactory(
                budget=budget, classification=factories.ClassificationFactory(classification_system=cs)
            )
            for _ in range(100)
        ]
        res = self.client.get(f"/api/v1/budgets/{budget.id}/items/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": b.id,
                "value": b.value,
                "budget": budget.id,
                "classification": b.classification.id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            for b in sorted(
                budget_items, key=lambda b: getattr(b, ordering.strip("-")), reverse=ordering.startswith("-")
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_retrieve(self):
        cs = factories.ClassificationSystemFactory()
        budget = factories.BudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget, classification=factories.ClassificationFactory(classification_system=cs)
        )
        res = self.client.get(f"/api/v1/budgets/{budget.id}/items/{budget_item.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id": budget_item.id,
            "value": budget_item.value,
            "budget": {
                "id": budget.id,
                "name": budget.name,
                "slug": budget.slug,
                "year": budget.year,
                "subtitle": budget.subtitle,
                "classificationSystem": cs.id,
                "government": budget.government.id,
                "createdAt": budget.created_at.strftime(datetime_format),
                "updatedAt": budget.updated_at.strftime(datetime_format),
            },
            "classification": {
                "id": budget_item.classification.id,
                "name": budget_item.classification.name,
                "code": budget_item.classification.code,
                "classificationSystem": cs.id,
                "parent": None,
                "createdAt": budget_item.classification.created_at.strftime(datetime_format),
                "updatedAt": budget_item.classification.updated_at.strftime(datetime_format),
            },
            "createdAt": budget_item.created_at.strftime(datetime_format),
            "updatedAt": budget_item.updated_at.strftime(datetime_format),
        }
        actual = res.json()
        self.assertEqual(actual, expected)

    def test_update_requires_login(self):
        cs = factories.ClassificationSystemFactory()
        budget = factories.BudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget, classification=factories.ClassificationFactory(classification_system=cs)
        )
        res = self.client.patch(f"/api/v1/budgets/{budget.id}/items/{budget_item.id}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_modify_value(self):
        cs = factories.ClassificationSystemFactory()
        budget = factories.BudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget, classification=factories.ClassificationFactory(classification_system=cs), value=20.0
        )
        self.client.login(username=self._user_username, password=self._user_password)
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            expected = {
                "id": budget_item.id,
                "budget": budget.id,
                "classification": budget_item.classification.id,
                "value": 100.0,
                "createdAt": budget_item.created_at.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            res = self.client.patch(
                f"/api/v1/budgets/{budget.id}/items/{budget_item.id}/",
                {
                    "value": 100.0,
                },
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            actual = res.json()
            self.assertEqual(actual, expected)

    def test_destroy_requires_login(self):
        cs = factories.ClassificationSystemFactory()
        budget = factories.BudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget, classification=factories.ClassificationFactory(classification_system=cs)
        )
        res = self.client.delete(f"/api/v1/budgets/{budget.id}/items/{budget_item.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy(self):
        cs = factories.ClassificationSystemFactory()
        budget = factories.BudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget, classification=factories.ClassificationFactory(classification_system=cs)
        )
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/budgets/{budget.id}/items/{budget_item.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_requires_login(self):
        cs = factories.ClassificationSystemFactory()
        c = factories.ClassificationFactory(classification_system=cs)
        budget = factories.BudgetFactory(classification_system=cs)
        res = self.client.post(
            f"/api/v1/budgets/{budget.id}/items/",
            {"classification": c.id, "budget": budget.id, "value": 3.14},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create(self):
        cs = factories.ClassificationSystemFactory()
        c = factories.ClassificationFactory(classification_system=cs)
        budget = factories.BudgetFactory(classification_system=cs)
        self.client.login(username=self._user_username, password=self._user_password)
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            expected = {
                "id": "ab12345678901234567890",
                "budget": budget.id,
                "classification": c.id,
                "value": 3.14,
                "createdAt": dt.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            with patch(
                "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890"
            ):
                res = self.client.post(
                    f"/api/v1/budgets/{budget.id}/items/",
                    {"classification": c.id, "value": 3.14},
                    format="json",
                )
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            actual = res.json()
            self.assertEqual(actual, expected)


class MappedBudgetItemCrudTestCase(BudgetMapperTestUserAPITestCase):
    def test_list(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size

        cs0 = factories.ClassificationSystemFactory()
        bud0 = factories.BudgetFactory(classification_system=cs0)
        cl00 = factories.ClassificationFactory(classification_system=cs0)
        cl000 = factories.ClassificationFactory(classification_system=cs0, parent=cl00)
        cl001 = factories.ClassificationFactory(classification_system=cs0, parent=cl00)
        cl01 = factories.ClassificationFactory(classification_system=cs0)
        cl010 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)
        cl011 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)
        cl012 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)

        abi00 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl000)
        abi01 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl001)
        abi10 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl010)
        abi11 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl011)
        abi12 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl012)

        cs1 = factories.ClassificationSystemFactory()
        bud1 = factories.BudgetFactory(classification_system=cs1)
        cl10 = factories.ClassificationFactory(classification_system=cs1)
        cl100 = factories.ClassificationFactory(classification_system=cs1, parent=cl10)
        cl101 = factories.ClassificationFactory(classification_system=cs1, parent=cl10)
        cl11 = factories.ClassificationFactory(classification_system=cs1)
        cl110 = factories.ClassificationFactory(classification_system=cs1, parent=cl11)

        mbi00 = models.MappedBudgetItem(budget=bud1, classification=cl100, mapped_budget=bud0)
        mbi00.save()
        mbi00.mapped_classifications.set([cl000])

        mbi01 = models.MappedBudgetItem(budget=bud1, classification=cl101, mapped_budget=bud0)
        mbi01.save()
        mbi01.mapped_classifications.set([cl010, cl011])

        mbi10 = models.MappedBudgetItem(budget=bud1, classification=cl110, mapped_budget=bud0)
        mbi10.save()
        mbi10.mapped_classifications.set([cl001, cl012])

        res = self.client.get(f"/api/v1/budgets/{bud1.id}/items/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": b.id,
                "budget": bud1.id,
                "mappedBudget": b.mapped_budget.id,
                "mappedClassifications": [c.id for c in b.mapped_classifications.all()],
                "classification": b.classification.id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            for b in sorted(
                [mbi00, mbi01, mbi10], key=lambda b: getattr(b, ordering.strip("-")), reverse=ordering.startswith("-")
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_retrieve(self):
        cs0 = factories.ClassificationSystemFactory()
        bud0 = factories.BudgetFactory(classification_system=cs0)
        cl00 = factories.ClassificationFactory(classification_system=cs0)
        cl000 = factories.ClassificationFactory(classification_system=cs0, parent=cl00)
        cl001 = factories.ClassificationFactory(classification_system=cs0, parent=cl00)
        cl01 = factories.ClassificationFactory(classification_system=cs0)
        cl010 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)
        cl011 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)
        cl012 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)

        abi00 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl000)
        abi01 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl001)
        abi10 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl010)
        abi11 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl011)
        abi12 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl012)

        cs1 = factories.ClassificationSystemFactory()
        bud1 = factories.BudgetFactory(classification_system=cs1)
        cl10 = factories.ClassificationFactory(classification_system=cs1)
        cl100 = factories.ClassificationFactory(classification_system=cs1, parent=cl10)
        cl101 = factories.ClassificationFactory(classification_system=cs1, parent=cl10)
        cl11 = factories.ClassificationFactory(classification_system=cs1)
        cl110 = factories.ClassificationFactory(classification_system=cs1, parent=cl11)

        mbi00 = models.MappedBudgetItem(budget=bud1, classification=cl100, mapped_budget=bud0)
        mbi00.save()
        mbi00.mapped_classifications.set([cl000])

        mbi01 = models.MappedBudgetItem(budget=bud1, classification=cl101, mapped_budget=bud0)
        mbi01.save()
        mbi01.mapped_classifications.set([cl010, cl011])

        mbi10 = models.MappedBudgetItem(budget=bud1, classification=cl110, mapped_budget=bud0)
        mbi10.save()
        mbi10.mapped_classifications.set([cl001, cl012])

        res = self.client.get(f"/api/v1/budgets/{bud1.id}/items/{mbi01.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id": mbi01.id,
            "mappedBudget": {
                "id": mbi01.mapped_budget.id,
                "name": mbi01.mapped_budget.name,
                "slug": mbi01.mapped_budget.slug,
                "year": mbi01.mapped_budget.year,
                "subtitle": mbi01.mapped_budget.subtitle,
                "classificationSystem": cs0.id,
                "government": mbi01.mapped_budget.government.id,
                "createdAt": mbi01.mapped_budget.created_at.strftime(datetime_format),
                "updatedAt": mbi01.mapped_budget.updated_at.strftime(datetime_format),
            },
            "mappedClassifications": [
                {
                    "id": cl010.id,
                    "name": cl010.name,
                    "code": cl010.code,
                    "classificationSystem": cs0.id,
                    "parent": cl01.id,
                    "createdAt": cl010.created_at.strftime(datetime_format),
                    "updatedAt": cl010.updated_at.strftime(datetime_format),
                },
                {
                    "id": cl011.id,
                    "name": cl011.name,
                    "code": cl011.code,
                    "classificationSystem": cs0.id,
                    "parent": cl01.id,
                    "createdAt": cl011.created_at.strftime(datetime_format),
                    "updatedAt": cl011.updated_at.strftime(datetime_format),
                },
            ],
            "budget": {
                "id": bud1.id,
                "name": bud1.name,
                "slug": bud1.slug,
                "year": bud1.year,
                "subtitle": bud1.subtitle,
                "classificationSystem": cs1.id,
                "government": bud1.government.id,
                "createdAt": bud1.created_at.strftime(datetime_format),
                "updatedAt": bud1.updated_at.strftime(datetime_format),
            },
            "classification": {
                "id": cl101.id,
                "name": cl101.name,
                "code": cl101.code,
                "parent": cl10.id,
                "classificationSystem": cs1.id,
                "createdAt": cl101.created_at.strftime(datetime_format),
                "updatedAt": cl101.updated_at.strftime(datetime_format),
            },
            "createdAt": mbi01.created_at.strftime(datetime_format),
            "updatedAt": mbi01.updated_at.strftime(datetime_format),
        }
        actual = res.json()
        self.assertEqual(actual, expected)

    def test_create_requires_authentication(self):
        cs0 = factories.ClassificationSystemFactory()
        bud0 = factories.BudgetFactory(classification_system=cs0)
        cl00 = factories.ClassificationFactory(classification_system=cs0)
        cl01 = factories.ClassificationFactory(classification_system=cs0)
        abi00 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl00)
        abi01 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl01)
        cs1 = factories.ClassificationSystemFactory()
        bud1 = factories.BudgetFactory(classification_system=cs1)
        cl10 = factories.ClassificationFactory(classification_system=cs1)
        query = {
            "budget": bud1.id,
            "classification": cl10.id,
            "mappedBudget": bud0.id,
            "mappedClassifications": [cl00.id, cl01.id],
        }
        res = self.client.post(f"/api/v1/budgets/{bud1.id}/items/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create(self):
        cs0 = factories.ClassificationSystemFactory()
        bud0 = factories.BudgetFactory(classification_system=cs0)
        cl00 = factories.ClassificationFactory(classification_system=cs0)
        cl01 = factories.ClassificationFactory(classification_system=cs0)
        abi00 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl00)
        abi01 = factories.AtomicBudgetItemFactory(budget=bud0, classification=cl01)
        cs1 = factories.ClassificationSystemFactory()
        bud1 = factories.BudgetFactory(classification_system=cs1)
        cl10 = factories.ClassificationFactory(classification_system=cs1)
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {
                "classification": cl10.id,
                "mappedBudget": bud0.id,
                "mappedClassifications": [cl00.id, cl01.id],
            }
            with patch(
                "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890"
            ):
                res = self.client.post(f"/api/v1/budgets/{bud1.id}/items/", query, format="json")
                self.assertEqual(res.status_code, status.HTTP_201_CREATED)
                expected = {
                    "id": "ab12345678901234567890",
                    "budget": bud1.id,
                    "classification": cl10.id,
                    "mappedBudget": bud0.id,
                    "mappedClassifications": [cl00.id, cl01.id],
                    "createdAt": dt.strftime(datetime_format),
                    "updatedAt": dt.strftime(datetime_format),
                }
                actual = res.json()
                self.assertEqual(actual, expected)

    def test_destroy_requires_login(self):
        mbi = factories.MappedBudgetItemFactory()
        res = self.client.delete(f"/api/v1/budgets/{mbi.budget.id}/items/{mbi.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy_requires_login(self):
        mbi0 = factories.MappedBudgetItemFactory()
        mbi1 = factories.MappedBudgetItemFactory()
        mbi2 = factories.MappedBudgetItemFactory()
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/budgets/{mbi0.budget.id}/items/{mbi0.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(models.MappedBudgetItem.DoesNotExist):
            models.MappedBudgetItem.objects.get(id=mbi0.id)
        models.MappedBudgetItem.objects.get(id=mbi1.id)
        models.MappedBudgetItem.objects.get(id=mbi2.id)

    def test_update_requires_login(self):
        mbi = factories.MappedBudgetItemFactory()
        cl = factories.ClassificationFactory(classification_system=mbi.mapped_budget.classification_system)
        query = {"mappedClassifications": [c.id for c in mbi.mapped_classifications.all()] + [cl.id]}
        res = self.client.patch(f"/api/v1/budgets/{mbi.budget.id}/items/{mbi.id}/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_adding_mapped_classifications(self):
        mbi = factories.MappedBudgetItemFactory()
        cl_orig = [c.id for c in mbi.mapped_classifications.all()]
        cl = factories.ClassificationFactory(classification_system=mbi.mapped_budget.classification_system)
        query = {"mappedClassifications": cl_orig + [cl.id]}
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            res = self.client.patch(f"/api/v1/budgets/{mbi.budget.id}/items/{mbi.id}/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            expected = {
                "id": mbi.id,
                "budget": mbi.budget.id,
                "classification": mbi.classification.id,
                "mappedBudget": mbi.mapped_budget.id,
                "mappedClassifications": cl_orig + [cl.id],
                "createdAt": mbi.created_at.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)
