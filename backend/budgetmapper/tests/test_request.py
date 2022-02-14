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
        bud = factories.BasicBudgetFactory(classification_system=cs)
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


class IconTestCase(TestCase):
    def test_get_icon_by_slug(self):
        icon = factories.IconImageFactory()
        c = Client()
        res = c.get(f"/icons/{icon.slug}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.headers["Content-Type"], f"image/{icon.image_type}")
        self.assertEqual(res.getvalue(), icon.body)

    def test_get_icon_by_id(self):
        icon = factories.IconImageFactory()
        c = Client()
        res = c.get(f"/icons/{icon.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.headers["Content-Type"], f"image/{icon.image_type}")
        self.assertEqual(res.getvalue(), icon.body)


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
        _ = factories.BasicBudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        res = self.client.get("/api/v1/wdmmg/", format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_create_route(self) -> None:
        res = self.client.post("/api/v1/wdmmg/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_returns_unauthorized_error_for_non_member(self) -> None:
        bud = factories.BasicBudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        res = self.client.put(f"/api/v1/wdmmg/{bud.slug}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_returns_method_not_allowed_error_for_member(self) -> None:
        bud = factories.BasicBudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.put(f"/api/v1/wdmmg/{bud.slug}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_destroy_returns_unauthorized_error_for_non_member(self) -> None:
        bud = factories.BasicBudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        res = self.client.delete(f"/api/v1/wdmmg/{bud.slug}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy_returns_method_not_allowed_error_for_member(self) -> None:
        bud = factories.BasicBudgetFactory(name="まほろ市2101年度予算", slug="mahoro-city-2101")
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/wdmmg/{bud.slug}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get(self) -> None:
        self.maxDiff = None
        gov = factories.GovernmentFactory(name="まほろ市", slug="mahoro-city")
        cs = factories.ClassificationSystemFactory(name="まほろ市2101年一般会計", slug="mahoro-city-2101-ippan-kaikei")
        icon0 = factories.IconImageFactory()
        cl0 = factories.ClassificationFactory(classification_system=cs, code="1", icon=icon0)
        icon00 = factories.IconImageFactory()
        cl00 = factories.ClassificationFactory(classification_system=cs, parent=cl0, code="1.1", icon=icon00)
        cl000 = factories.ClassificationFactory(classification_system=cs, parent=cl00, code="1.1.1")
        cl001 = factories.ClassificationFactory(classification_system=cs, parent=cl00, code="1.1.2")
        cl002 = factories.ClassificationFactory(classification_system=cs, parent=cl00, code="1.1.3")
        icon01 = factories.IconImageFactory()
        cl01 = factories.ClassificationFactory(classification_system=cs, parent=cl0, code="1.2", icon=icon01)
        cl010 = factories.ClassificationFactory(classification_system=cs, parent=cl01, code="1.2.1")
        cl1 = factories.ClassificationFactory(classification_system=cs, code="2")
        cl10 = factories.ClassificationFactory(classification_system=cs, parent=cl1, code="2.1")
        cl100 = factories.ClassificationFactory(classification_system=cs, parent=cl10, code="2.1.1")
        cl2 = factories.ClassificationFactory(classification_system=cs, code="10")
        cl20 = factories.ClassificationFactory(classification_system=cs, parent=cl2, code="10.1")
        cl200 = factories.ClassificationFactory(classification_system=cs, parent=cl20, code="10.1.1")
        bud = factories.BasicBudgetFactory(
            name="まほろ市2101年度予算",
            slug="mahoro-city-2101",
            government_value=gov,
            classification_system=cs,
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
            "totalAmount": abi000.amount + abi001.amount + abi002.amount + abi010.amount + abi100.amount,
            "budgets": [
                {
                    "id": cl0.id,
                    "name": cl0.name,
                    "code": cl0.code,
                    "amount": abi000.amount + abi001.amount + abi002.amount + abi010.amount,
                    "iconId": icon0.id,
                    "children": [
                        {
                            "id": cl00.id,
                            "name": cl00.name,
                            "code": cl00.code,
                            "amount": abi000.amount + abi001.amount + abi002.amount,
                            "iconId": icon00.id,
                            "children": [
                                {
                                    "id": cl000.id,
                                    "name": cl000.name,
                                    "code": cl000.code,
                                    "amount": abi000.amount,
                                    "iconId": models.IconImage.get_default_icon().id,
                                    "children": None,
                                },
                                {
                                    "id": cl001.id,
                                    "name": cl001.name,
                                    "code": cl001.code,
                                    "amount": abi001.amount,
                                    "iconId": models.IconImage.get_default_icon().id,
                                    "children": None,
                                },
                                {
                                    "id": cl002.id,
                                    "name": cl002.name,
                                    "code": cl002.code,
                                    "amount": abi002.amount,
                                    "iconId": models.IconImage.get_default_icon().id,
                                    "children": None,
                                },
                            ],
                        },
                        {
                            "id": cl01.id,
                            "name": cl01.name,
                            "code": cl01.code,
                            "amount": abi010.amount,
                            "iconId": icon01.id,
                            "children": [
                                {
                                    "id": cl010.id,
                                    "name": cl010.name,
                                    "code": cl010.code,
                                    "amount": abi010.amount,
                                    "iconId": models.IconImage.get_default_icon().id,
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
                    "amount": abi100.amount,
                    "iconId": models.IconImage.get_default_icon().id,
                    "children": [
                        {
                            "id": cl10.id,
                            "name": cl10.name,
                            "code": cl10.code,
                            "amount": abi100.amount,
                            "iconId": models.IconImage.get_default_icon().id,
                            "children": [
                                {
                                    "id": cl100.id,
                                    "name": cl100.name,
                                    "code": cl100.code,
                                    "amount": abi100.amount,
                                    "iconId": models.IconImage.get_default_icon().id,
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
                    "iconId": models.IconImage.get_default_icon().id,
                    "children": [
                        {
                            "id": cl20.id,
                            "name": cl20.name,
                            "code": cl20.code,
                            "amount": 0,
                            "iconId": models.IconImage.get_default_icon().id,
                            "children": [
                                {
                                    "id": cl200.id,
                                    "name": cl200.name,
                                    "code": cl200.code,
                                    "amount": 0,
                                    "iconId": models.IconImage.get_default_icon().id,
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
                govs,
                key=lambda gov: getattr(gov, ordering.strip("-")),
                reverse=ordering.startswith("-"),
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
        res = self.client.post("/api/v1/governments/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        return_value="ab12345678901234567890",
    )
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_default(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {"name": "まほろ市"}
            res = self.client.post("/api/v1/governments/", query, format="json")
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

    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        return_value="ab12345678901234567890",
    )
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_specified_values(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {
                "name": "まほろ市",
                "slug": "mahoro-city",
                "latitude": -54,
                "longitude": 170,
            }
            res = self.client.post("/api/v1/governments/", query, format="json")
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
            for cs in sorted(
                css,
                key=lambda cs: getattr(cs, ordering.strip("-")),
                reverse=ordering.startswith("-"),
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_retrieve(self):
        css = [factories.ClassificationSystemFactory() for i in range(100)]
        cs = css[random.randint(0, 99)]
        cl0 = factories.ClassificationFactory(classification_system=cs, item_order=2)
        cl1 = factories.ClassificationFactory(classification_system=cs, item_order=0)
        cl2 = factories.ClassificationFactory(classification_system=cs, item_order=1)
        res = self.client.get(f"/api/v1/classification-systems/{cs.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id": cs.id,
            "name": cs.name,
            "slug": cs.slug,
            "levelNames": cs.level_names,
            "items": [
                {
                    "id": cl1.id,
                    "code": cl1.code,
                    "name": cl1.name,
                    "icon": cl1.icon,
                    "classificationSystem": cs.id,
                    "parent": None,
                    "createdAt": cl1.created_at.strftime(datetime_format),
                    "updatedAt": cl1.updated_at.strftime(datetime_format),
                },
                {
                    "id": cl2.id,
                    "code": cl2.code,
                    "name": cl2.name,
                    "icon": cl2.icon,
                    "classificationSystem": cs.id,
                    "parent": None,
                    "createdAt": cl2.created_at.strftime(datetime_format),
                    "updatedAt": cl2.updated_at.strftime(datetime_format),
                },
                {
                    "id": cl0.id,
                    "code": cl0.code,
                    "name": cl0.name,
                    "icon": cl0.icon,
                    "classificationSystem": cs.id,
                    "parent": None,
                    "createdAt": cl0.created_at.strftime(datetime_format),
                    "updatedAt": cl0.updated_at.strftime(datetime_format),
                },
            ],
            "createdAt": cs.created_at.strftime(datetime_format),
            "updatedAt": cs.updated_at.strftime(datetime_format),
        }
        actual = res.json()
        self.assertEqual(actual, expected)

    def test_retrieve_by_slug(self):
        css = [factories.ClassificationSystemFactory() for i in range(100)]
        cs = css[random.randint(0, 99)]
        res = self.client.get(f"/api/v1/classification-systems/{cs.slug}/", format="json")
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

    def test_retrieve_by_empty_slug(self):
        [factories.ClassificationSystemFactory() for i in range(100)]
        res = self.client.get("/api/v1/classification-systems//", format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_requires_authentication(self):
        query = {"name": "まほろ市予算"}
        res = self.client.post("/api/v1/classification-systems/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        return_value="ab12345678901234567890",
    )
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_default(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {"name": "まほろ市予算"}
            res = self.client.post("/api/v1/classification-systems/", query, format="json")
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

    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        return_value="ab12345678901234567890",
    )
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_specified_values(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {
                "name": "まほろ市予算",
                "slug": "mahoro-city-budget",
                "levelNames": ["level1", "level2", "level3"],
            }
            res = self.client.post("/api/v1/classification-systems/", query, format="json")
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

    def test_destroy_by_slug(self):
        css = [factories.ClassificationSystemFactory() for i in range(100)]
        cs = css[random.randint(0, 99)]
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/classification-systems/{cs.slug}/")
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
            res = self.client.put(
                f"/api/v1/classification-systems/{cs.id}/",
                {"slug": None},
                format="json",
            )
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

    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_update_blank_slug_by_slug(self, jp_slugify):
        cs = factories.ClassificationSystemFactory(slug="someslug")
        self.client.login(username=self._user_username, password=self._user_password)
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            res = self.client.put(
                f"/api/v1/classification-systems/{cs.slug}/",
                {"slug": None},
                format="json",
            )
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


class ClassificationCrudTestCase(BudgetMapperTestUserAPITestCase):
    def test_list(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        cs = factories.ClassificationSystemFactory()
        classifications = [factories.ClassificationFactory(classification_system=cs) for _ in range(100)]
        res = self.client.get(f"/api/v1/classification-systems/{cs.id}/classifications/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": b.id,
                "code": b.code,
                "name": b.name,
                "classificationSystem": {
                    "id": cs.id,
                    "name": cs.name,
                    "slug": cs.slug,
                    "levelNames": cs.level_names,
                    "createdAt": cs.created_at.strftime(datetime_format),
                    "updatedAt": cs.updated_at.strftime(datetime_format),
                },
                "icon": b.icon.id if b.icon is not None else None,
                "parent": b.parent,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            for b in sorted(
                classifications,
                key=lambda b: getattr(b, ordering.strip("-")),
                reverse=ordering.startswith("-"),
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_get(self):
        self.maxDiff = None
        cs = factories.ClassificationSystemFactory()
        classification_parent_a = factories.ClassificationFactory(classification_system=cs)
        c = factories.ClassificationFactory(classification_system=cs, parent=classification_parent_a)
        res = self.client.get(
            f"/api/v1/classification-systems/{cs.id}/classifications/{c.id}/",
            format="json",
        )
        expected = {
            "id": c.id,
            "code": c.code,
            "name": c.name,
            "classificationSystem": {
                "id": cs.id,
                "name": cs.name,
                "slug": cs.slug,
                "levelNames": cs.level_names,
                "createdAt": cs.created_at.strftime(datetime_format),
                "updatedAt": cs.updated_at.strftime(datetime_format),
            },
            "icon": c.icon.id if c.icon is not None else None,
            "parent": c.parent.id,
            "createdAt": c.created_at.strftime(datetime_format),
            "updatedAt": c.updated_at.strftime(datetime_format),
        }
        res_cs = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res_cs, expected)

    def test_post_requires_login(self):
        cs = factories.ClassificationSystemFactory()
        classification = factories.ClassificationFactory(classification_system=cs)
        res = self.client.post(
            f"/api/v1/classification-systems/{cs.id}/classifications/{classification.id}/",
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post(self):
        cs = factories.ClassificationSystemFactory()
        classification_parent_b = factories.ClassificationFactory(classification_system=cs)
        expected_name = "HOGEHOGEHOGE"
        expected_code = "codecode"
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.post(
            f"/api/v1/classification-systems/{cs.id}/classifications/",
            {
                "classification_system": cs.id,
                "name": expected_name,
                "code": expected_code,
                "parent": classification_parent_b.id,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        cs_id = res.json()["id"]
        c = models.Classification.objects.get(id=cs_id)
        self.assertEqual(c.classification_system.id, cs.id)
        self.assertEqual(c.name, expected_name)
        self.assertEqual(c.code, expected_code)
        self.assertEqual(c.icon, None)
        self.assertEqual(c.parent.id, classification_parent_b.id)

    def test_partial_update_requires_login(self):
        cs = factories.ClassificationSystemFactory()
        classification = factories.ClassificationFactory(classification_system=cs)
        res = self.client.patch(
            f"/api/v1/classification-systems/{cs.id}/classifications/{classification.id}/",
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update(self):
        cs = factories.ClassificationSystemFactory()
        classification = factories.ClassificationFactory(classification_system=cs)
        expected_name = "HOGEHOGEHOGE"
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.patch(
            f"/api/v1/classification-systems/{cs.id}/classifications/{classification.id}/",
            {"name": expected_name},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        c = models.Classification.objects.get(id=classification.id)
        self.assertEqual(c.name, expected_name)

    def test_partial_update_parent(self):
        cs = factories.ClassificationSystemFactory()
        classification_parent_a = factories.ClassificationFactory(classification_system=cs)
        classification_parent_b = factories.ClassificationFactory(classification_system=cs)
        classification = factories.ClassificationFactory(classification_system=cs, parent=classification_parent_a)
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.patch(
            f"/api/v1/classification-systems/{cs.id}/classifications/{classification.id}/",
            {
                "parent": classification_parent_b.id,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        c = models.Classification.objects.get(id=classification.id)
        self.assertEqual(c.parent.id, classification_parent_b.id)

    def test_update_requires_login(self):
        cs = factories.ClassificationSystemFactory()
        classification = factories.ClassificationFactory(classification_system=cs)
        res = self.client.put(
            f"/api/v1/classification-systems/{cs.id}/classifications/{classification.id}/",
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update(self):
        icon = factories.IconImageFactory()
        cs = factories.ClassificationSystemFactory()
        classification_parent_a = factories.ClassificationFactory(classification_system=cs)
        classification_parent_b = factories.ClassificationFactory(classification_system=cs)
        classification = factories.ClassificationFactory(classification_system=cs, parent=classification_parent_a)
        expected_name = "HOGEHOGEHOGE"
        expected_code = "codecode"
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.put(
            f"/api/v1/classification-systems/{cs.id}/classifications/{classification.id}/",
            {
                "classification_system": cs.id,
                "name": expected_name,
                "code": expected_code,
                "parent": classification_parent_b.id,
                "icon": icon.id,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        c = models.Classification.objects.get(id=classification.id)
        self.assertEqual(c.name, expected_name)
        self.assertEqual(c.code, expected_code)
        self.assertEqual(c.parent.id, classification_parent_b.id)
        self.assertEqual(c.icon.id, icon.id)

    def test_delete_requires_login(self):
        cs = factories.ClassificationSystemFactory()
        classification = factories.ClassificationFactory(classification_system=cs)
        res = self.client.delete(
            f"/api/v1/classification-systems/{cs.id}/classifications/{classification.id}/",
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        try:
            models.Classification.objects.get(id=classification.id)
        except Exception as e:
            self.fail(str(e))

    def test_destroy(self):
        cs = factories.ClassificationSystemFactory()
        classification = factories.ClassificationFactory(classification_system=cs)
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(
            f"/api/v1/classification-systems/{cs.id}/classifications/{classification.id}/",
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(models.Classification.DoesNotExist):
            models.Classification.objects.get(id=classification.id)


class BudgetCrudTestCase(BudgetMapperTestUserAPITestCase):
    def test_list(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        bs = []
        for i in range(100):
            if i % 2 == 0:
                bs.append(factories.BasicBudgetFactory())
            else:
                bs.append(factories.MappedBudgetFactory(source_budget=bs[i - 1]))
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
            if isinstance(b, models.BasicBudget)
            else {
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "year": b.year,
                "subtitle": b.subtitle,
                "classificationSystem": b.classification_system.id,
                "government": b.government.id,
                "sourceBudget": b.source_budget.id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            for b in sorted(
                bs,
                key=lambda b: getattr(b, ordering.strip("-")),
                reverse=ordering.startswith("-"),
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_list_can_filter_by_government(self):
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        govs = [factories.GovernmentFactory() for _ in range(4)]

        bs = []
        for i in range(100):
            if i % 2 == 0:
                bs.append(factories.BasicBudgetFactory(government_value=govs[(i // 2) % 4]))
            else:
                bs.append(factories.MappedBudgetFactory(source_budget=bs[i - 1]))

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
                "government": b.government.id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            if isinstance(b, models.BasicBudget)
            else {
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "year": b.year,
                "subtitle": b.subtitle,
                "classificationSystem": b.classification_system.id,
                "government": b.government.id,
                "sourceBudget": b.source_budget.id,
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
        bs = []
        for i in range(100):
            if i % 2 == 0:
                bs.append(factories.BasicBudgetFactory(year_value=(2000 + i // 10)))
            else:
                bs.append(factories.MappedBudgetFactory(source_budget=bs[i - 1]))
        res = self.client.get("/api/v1/budgets/?year=2001", format="json")
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
            if isinstance(b, models.BasicBudget)
            else {
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "year": b.year,
                "subtitle": b.subtitle,
                "classificationSystem": b.classification_system.id,
                "government": b.government.id,
                "sourceBudget": b.source_budget.id,
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
        bs = []
        for i in range(100):
            if i % 2 == 0:
                bs.append(
                    factories.BasicBudgetFactory(government_value=govs[(i // 2) % 4], year_value=(2000 + (i // 10)))
                )
            else:
                bs.append(factories.MappedBudgetFactory(source_budget=bs[i - 1]))
        res = self.client.get(f"/api/v1/budgets/?government={govs[0].id}&year=2001", format="json")
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
            if isinstance(b, models.BasicBudget)
            else {
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "year": b.year,
                "subtitle": b.subtitle,
                "classificationSystem": b.classification_system.id,
                "government": b.government.id,
                "sourceBudget": b.source_budget.id,
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

    def test_retrieve_basic(self):
        bs = [factories.BasicBudgetFactory() for i in range(100)]
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
            "createdAt": b.created_at.strftime(datetime_format),
            "updatedAt": b.updated_at.strftime(datetime_format),
        }

        actual = res.json()
        self.assertEqual(actual, expected)

    def test_retrieve_mapped(self):
        self.maxDiff = None
        bs = [factories.MappedBudgetFactory() for i in range(100)]
        b = random.choice(bs)
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
            "sourceBudget": {
                "id": b.source_budget.id,
                "name": b.source_budget.name,
                "slug": b.source_budget.slug,
                "year": b.source_budget.year,
                "subtitle": b.source_budget.subtitle,
                "classificationSystem": {
                    "id": b.source_budget.classification_system.id,
                    "name": b.source_budget.classification_system.name,
                    "slug": b.source_budget.classification_system.slug,
                    "levelNames": b.source_budget.classification_system.level_names,
                    "createdAt": b.source_budget.classification_system.created_at.strftime(datetime_format),
                    "updatedAt": b.source_budget.classification_system.updated_at.strftime(datetime_format),
                },
                "government": {
                    "id": b.source_budget.government.id,
                    "name": b.source_budget.government.name,
                    "slug": b.source_budget.government.slug,
                    "latitude": b.source_budget.government.latitude,
                    "longitude": b.source_budget.government.longitude,
                    "createdAt": b.source_budget.government.created_at.strftime(datetime_format),
                    "updatedAt": b.source_budget.government.updated_at.strftime(datetime_format),
                },
                "createdAt": b.source_budget.created_at.strftime(datetime_format),
                "updatedAt": b.source_budget.updated_at.strftime(datetime_format),
            },
            "createdAt": b.created_at.strftime(datetime_format),
            "updatedAt": b.updated_at.strftime(datetime_format),
        }

        actual = res.json()
        self.assertEqual(actual, expected)

    def test_create_requires_authentication(self):
        gov = factories.GovernmentFactory()
        cs = factories.ClassificationSystemFactory()
        query = {
            "name": "まほろ市2101年度予算",
            "year": 2101,
            "government": gov.id,
            "classificationSystem": cs.id,
        }
        res = self.client.post("/api/v1/budgets/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        return_value="ab12345678901234567890",
    )
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_default_basic(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
        gov = factories.GovernmentFactory()
        cs = factories.ClassificationSystemFactory()
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {
                "name": "まほろ市2101年度予算",
                "year": 2101,
                "government": gov.id,
                "classificationSystem": cs.id,
            }
            res = self.client.post("/api/v1/budgets/", query, format="json")
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
        bud = models.BudgetBase.objects.get(pk="ab12345678901234567890")
        self.assertIsInstance(bud, models.BasicBudget)

    def test_create_with_default_mapped(self):
        cs = factories.ClassificationSystemFactory()
        basic_bud = factories.BasicBudgetFactory()
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {"name": "まほろ市2101年度COFOG", "classificationSystem": cs.id, "sourceBudget": basic_bud.id}
            with patch(
                "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
                return_value="ab12345678901234567890",
            ), patch("budgetmapper.models.jp_slugify", return_value="theslug"):
                res = self.client.post("/api/v1/budgets/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            expected = {
                "id": "ab12345678901234567890",
                "name": "まほろ市2101年度COFOG",
                "slug": "theslug",
                "year": basic_bud.year,
                "subtitle": None,
                "classificationSystem": cs.id,
                "government": basic_bud.government.id,
                "sourceBudget": basic_bud.id,
                "createdAt": dt.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)
        bud = models.BudgetBase.objects.get(pk="ab12345678901234567890")
        self.assertIsInstance(bud, models.MappedBudget)

    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        return_value="ab12345678901234567890",
    )
    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_create_with_specified_values_basic(self, jp_slugify, shortuuidfield_ShortUUIDField_get_default):
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
            res = self.client.post("/api/v1/budgets/", query, format="json")
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
        bud = models.BudgetBase.objects.get(pk="ab12345678901234567890")
        self.assertIsInstance(bud, models.BasicBudget)

    def test_create_with_specified_values_mapped(self):
        cs = factories.ClassificationSystemFactory()
        basic_bud = factories.BasicBudgetFactory()
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {
                "name": "まほろ市2101年度COFOG",
                "classificationSystem": cs.id,
                "sourceBudget": basic_bud.id,
                "slug": "mahoro-city-2101-cofog",
                "subtitle": "試作",
            }
            with patch(
                "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
                return_value="ab12345678901234567890",
            ), patch("budgetmapper.models.jp_slugify", return_value="theslug"):
                res = self.client.post("/api/v1/budgets/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            expected = {
                "id": "ab12345678901234567890",
                "name": "まほろ市2101年度COFOG",
                "slug": "mahoro-city-2101-cofog",
                "year": basic_bud.year,
                "subtitle": "試作",
                "classificationSystem": cs.id,
                "government": basic_bud.government.id,
                "sourceBudget": basic_bud.id,
                "createdAt": dt.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)
        bud = models.BudgetBase.objects.get(pk="ab12345678901234567890")
        self.assertIsInstance(bud, models.MappedBudget)

    def test_destroy_requires_login(self):
        bs = [factories.BasicBudgetFactory() for i in range(100)]
        b = bs[random.randint(0, 99)]
        res = self.client.delete(f"/api/v1/budgets/{b.id}/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy(self):
        bs = [factories.BasicBudgetFactory() for i in range(100)]
        b = bs[random.randint(0, 99)]
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/budgets/{b.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(models.BudgetBase.DoesNotExist):
            models.BudgetBase.objects.get(id=b.id)

    def test_update_requires_login(self):
        bs = [factories.BasicBudgetFactory() for i in range(100)]
        b = bs[random.randint(0, 99)]
        res = self.client.put(f"/api/v1/budgets/{b.id}/", {"slug": ""}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("budgetmapper.models.jp_slugify", return_value="theslug")
    def test_partial_update_basic(self, jp_slugify):
        b = factories.BasicBudgetFactory(slug="someslug")
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

    def test_partial_update_mapped(self):
        b = factories.MappedBudgetFactory(slug="someslug")
        self.client.login(username=self._user_username, password=self._user_password)
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt), patch("budgetmapper.models.jp_slugify", return_value="theslug"):
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
                "sourceBudget": b.source_budget.id,
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
        budget = factories.BasicBudgetFactory(classification_system=cs)
        budget_items = [
            factories.AtomicBudgetItemFactory(
                budget=budget,
                classification=factories.ClassificationFactory(classification_system=cs),
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
                budget_items,
                key=lambda b: getattr(b, ordering.strip("-")),
                reverse=ordering.startswith("-"),
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_retrieve(self):
        cs = factories.ClassificationSystemFactory()
        budget = factories.BasicBudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget,
            classification=factories.ClassificationFactory(classification_system=cs),
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
                "icon": None,
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
        budget = factories.BasicBudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget,
            classification=factories.ClassificationFactory(classification_system=cs),
        )
        res = self.client.patch(f"/api/v1/budgets/{budget.id}/items/{budget_item.id}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_modify_value(self):
        cs = factories.ClassificationSystemFactory()
        budget = factories.BasicBudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget,
            classification=factories.ClassificationFactory(classification_system=cs),
            value=20.0,
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
        budget = factories.BasicBudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget,
            classification=factories.ClassificationFactory(classification_system=cs),
        )
        res = self.client.delete(f"/api/v1/budgets/{budget.id}/items/{budget_item.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy(self):
        cs = factories.ClassificationSystemFactory()
        budget = factories.BasicBudgetFactory(classification_system=cs)
        budget_item = factories.AtomicBudgetItemFactory(
            budget=budget,
            classification=factories.ClassificationFactory(classification_system=cs),
        )
        self.client.login(username=self._user_username, password=self._user_password)
        res = self.client.delete(f"/api/v1/budgets/{budget.id}/items/{budget_item.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_requires_login(self):
        cs = factories.ClassificationSystemFactory()
        c = factories.ClassificationFactory(classification_system=cs)
        budget = factories.BasicBudgetFactory(classification_system=cs)
        res = self.client.post(
            f"/api/v1/budgets/{budget.id}/items/",
            {"classification": c.id, "budget": budget.id, "value": 3.14},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create(self):
        cs = factories.ClassificationSystemFactory()
        c = factories.ClassificationFactory(classification_system=cs)
        budget = factories.BasicBudgetFactory(classification_system=cs)
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
                "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
                return_value="ab12345678901234567890",
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
        bud0 = factories.BasicBudgetFactory(classification_system=cs0)
        cl00 = factories.ClassificationFactory(classification_system=cs0)
        cl000 = factories.ClassificationFactory(classification_system=cs0, parent=cl00)
        cl001 = factories.ClassificationFactory(classification_system=cs0, parent=cl00)
        cl01 = factories.ClassificationFactory(classification_system=cs0)
        cl010 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)
        cl011 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)
        cl012 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)

        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl000)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl001)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl010)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl011)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl012)

        cs1 = factories.ClassificationSystemFactory()
        bud1 = factories.MappedBudgetFactory(classification_system=cs1, source_budget=bud0)
        cl10 = factories.ClassificationFactory(classification_system=cs1)
        cl100 = factories.ClassificationFactory(classification_system=cs1, parent=cl10)
        cl101 = factories.ClassificationFactory(classification_system=cs1, parent=cl10)
        cl11 = factories.ClassificationFactory(classification_system=cs1)
        cl110 = factories.ClassificationFactory(classification_system=cs1, parent=cl11)

        mbi00 = models.MappedBudgetItem(budget=bud1, classification=cl100)
        mbi00.save()
        mbi00.source_classifications.set([cl000])

        mbi01 = models.MappedBudgetItem(budget=bud1, classification=cl101)
        mbi01.save()
        mbi01.source_classifications.set([cl010, cl011])

        mbi10 = models.MappedBudgetItem(budget=bud1, classification=cl110)
        mbi10.save()
        mbi10.source_classifications.set([cl001, cl012])

        res = self.client.get(f"/api/v1/budgets/{bud1.id}/items/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": b.id,
                "budget": bud1.id,
                "sourceClassifications": [c.id for c in b.source_classifications.all()],
                "classification": b.classification.id,
                "createdAt": b.created_at.strftime(datetime_format),
                "updatedAt": b.updated_at.strftime(datetime_format),
            }
            for b in sorted(
                [mbi00, mbi01, mbi10],
                key=lambda b: getattr(b, ordering.strip("-")),
                reverse=ordering.startswith("-"),
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_retrieve(self):
        cs0 = factories.ClassificationSystemFactory()
        bud0 = factories.BasicBudgetFactory(classification_system=cs0)
        cl00 = factories.ClassificationFactory(classification_system=cs0)
        cl000 = factories.ClassificationFactory(classification_system=cs0, parent=cl00)
        cl001 = factories.ClassificationFactory(classification_system=cs0, parent=cl00)
        cl01 = factories.ClassificationFactory(classification_system=cs0)
        cl010 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)
        cl011 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)
        cl012 = factories.ClassificationFactory(classification_system=cs0, parent=cl01)

        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl000)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl001)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl010)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl011)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl012)

        cs1 = factories.ClassificationSystemFactory()
        bud1 = factories.MappedBudgetFactory(classification_system=cs1, source_budget=bud0)
        cl10 = factories.ClassificationFactory(classification_system=cs1)
        cl100 = factories.ClassificationFactory(classification_system=cs1, parent=cl10)
        cl101 = factories.ClassificationFactory(classification_system=cs1, parent=cl10)
        cl11 = factories.ClassificationFactory(classification_system=cs1)
        cl110 = factories.ClassificationFactory(classification_system=cs1, parent=cl11)

        mbi00 = models.MappedBudgetItem(budget=bud1, classification=cl100)
        mbi00.save()
        mbi00.source_classifications.set([cl000])

        mbi01 = models.MappedBudgetItem(budget=bud1, classification=cl101)
        mbi01.save()
        mbi01.source_classifications.set([cl010, cl011])

        mbi10 = models.MappedBudgetItem(budget=bud1, classification=cl110)
        mbi10.save()
        mbi10.source_classifications.set([cl001, cl012])

        res = self.client.get(f"/api/v1/budgets/{bud1.id}/items/{mbi01.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        bud1 = models.MappedBudget.objects.get(pk=bud1.pk)
        expected = {
            "id": mbi01.id,
            "sourceClassifications": [
                {
                    "id": cl010.id,
                    "name": cl010.name,
                    "code": cl010.code,
                    "classificationSystem": cs0.id,
                    "icon": None,
                    "parent": cl01.id,
                    "createdAt": cl010.created_at.strftime(datetime_format),
                    "updatedAt": cl010.updated_at.strftime(datetime_format),
                },
                {
                    "id": cl011.id,
                    "name": cl011.name,
                    "code": cl011.code,
                    "classificationSystem": cs0.id,
                    "icon": None,
                    "parent": cl01.id,
                    "createdAt": cl011.created_at.strftime(datetime_format),
                    "updatedAt": cl011.updated_at.strftime(datetime_format),
                },
            ],
            "budget": {
                "id": bud1.id,
                "name": bud1.name,
                "slug": bud1.slug,
                "sourceBudget": bud0.id,
                "subtitle": bud1.subtitle,
                "classificationSystem": cs1.id,
                "year": bud0.year,
                "government": bud0.government.id,
                "createdAt": bud1.created_at.strftime(datetime_format),
                "updatedAt": bud1.updated_at.strftime(datetime_format),
            },
            "classification": {
                "id": cl101.id,
                "name": cl101.name,
                "code": cl101.code,
                "parent": cl10.id,
                "icon": None,
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
        bud0 = factories.BasicBudgetFactory(classification_system=cs0)
        cl00 = factories.ClassificationFactory(classification_system=cs0)
        cl01 = factories.ClassificationFactory(classification_system=cs0)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl00)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl01)
        cs1 = factories.ClassificationSystemFactory()
        bud1 = factories.MappedBudgetFactory(classification_system=cs1, source_budget=bud0)
        cl10 = factories.ClassificationFactory(classification_system=cs1)
        query = {
            "budget": bud1.id,
            "classification": cl10.id,
            "sourceClassifications": [cl00.id, cl01.id],
        }
        res = self.client.post(f"/api/v1/budgets/{bud1.id}/items/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create(self):
        cs0 = factories.ClassificationSystemFactory()
        bud0 = factories.BasicBudgetFactory(classification_system=cs0)
        cl00 = factories.ClassificationFactory(classification_system=cs0)
        cl01 = factories.ClassificationFactory(classification_system=cs0)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl00)
        factories.AtomicBudgetItemFactory(budget=bud0, classification=cl01)
        cs1 = factories.ClassificationSystemFactory()
        bud1 = factories.MappedBudgetFactory(classification_system=cs1, source_budget=bud0)
        cl10 = factories.ClassificationFactory(classification_system=cs1)
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            query = {
                "classification": cl10.id,
                "sourceClassifications": [cl00.id, cl01.id],
            }
            with patch(
                "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
                return_value="ab12345678901234567890",
            ):
                res = self.client.post(f"/api/v1/budgets/{bud1.id}/items/", query, format="json")
                self.assertEqual(res.status_code, status.HTTP_201_CREATED)
                expected = {
                    "id": "ab12345678901234567890",
                    "budget": bud1.id,
                    "classification": cl10.id,
                    "sourceClassifications": [cl00.id, cl01.id],
                    "createdAt": dt.strftime(datetime_format),
                    "updatedAt": dt.strftime(datetime_format),
                }
                actual = res.json()
                self.assertEqual(actual, expected)

    def test_destroy_requires_login(self):
        mbi = factories.MappedBudgetItemFactory()
        res = self.client.delete(f"/api/v1/budgets/{mbi.budget.id}/items/{mbi.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy(self):
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
        cl = factories.ClassificationFactory(classification_system=mbi.budget.source_budget.classification_system)
        query = {"sourceClassifications": [c.id for c in mbi.source_classifications.all()] + [cl.id]}
        res = self.client.patch(f"/api/v1/budgets/{mbi.budget.id}/items/{mbi.id}/", query, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_adding_source_classifications(self):
        mbi = factories.MappedBudgetItemFactory()
        cl_orig = [c.id for c in mbi.source_classifications.all()]
        cl = factories.ClassificationFactory(classification_system=mbi.budget.source_budget.classification_system)
        query = {"sourceClassifications": cl_orig + [cl.id]}
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt):
            self.client.login(username=self._user_username, password=self._user_password)
            res = self.client.patch(f"/api/v1/budgets/{mbi.budget.id}/items/{mbi.id}/", query, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            expected = {
                "id": mbi.id,
                "budget": mbi.budget.id,
                "classification": mbi.classification.id,
                "sourceClassifications": cl_orig + [cl.id],
                "createdAt": mbi.created_at.strftime(datetime_format),
                "updatedAt": dt.strftime(datetime_format),
            }
            actual = res.json()
            self.assertEqual(actual, expected)


class IconImageCrudTestCase(BudgetMapperTestUserAPITestCase):
    def test_list(self) -> None:
        ordering = CreatedAtPagination.ordering
        page_size = CreatedAtPagination.page_size
        icons = [factories.IconImageFactory() for i in range(100)]
        res = self.client.get("/api/v1/icon-images/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": icon.id,
                "name": icon.name,
                "slug": icon.slug,
                "createdAt": icon.created_at.strftime(datetime_format),
                "updatedAt": icon.updated_at.strftime(datetime_format),
            }
            for icon in sorted(
                icons, key=lambda icon: getattr(icon, ordering.strip("-")), reverse=ordering.startswith("-")
            )[:page_size]
        ]
        res_json = res.json()
        self.assertIn("results", res_json)
        actual = res_json["results"]
        self.assertEqual(actual, expected)

    def test_retrieve(self):
        icons = [factories.IconImageFactory() for i in range(100)]
        icon = random.choice(icons)
        res = self.client.get(f"/api/v1/icon-images/{icon.id}/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id": icon.id,
            "name": icon.name,
            "slug": icon.slug,
            "dataUri": icon.to_data_uri(),
            "createdAt": icon.created_at.strftime(datetime_format),
            "updatedAt": icon.updated_at.strftime(datetime_format),
        }

        actual = res.json()
        self.assertEqual(actual, expected)

    def test_icon_image_is_read_only(self):
        self.client.login(username=self._user_username, password=self._user_password)
        icons = [factories.IconImageFactory() for i in range(100)]
        icon = random.choice(icons)
        res = self.client.post("/api/v1/icon-images/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        res = self.client.put(f"/api/v1/icon-images/{icon.id}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        res = self.client.patch(f"/api/v1/icon-images/{icon.id}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        res = self.client.delete(f"/api/v1/icon-images/{icon.id}/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
