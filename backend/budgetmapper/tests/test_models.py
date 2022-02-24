import doctest
import json
from collections.abc import Iterator
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, call, patch

import freezegun
from budgetmapper import models
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase, TransactionTestCase

from . import factories

date_format = "%Y%m%d%H%M%S%f"


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(models))
    return tests


class IconImageTestCase(TransactionTestCase):
    @freezegun.freeze_time(datetime(2022, 2, 22, 22, 22, 22, 222222))
    @patch("budgetmapper.models.jp_slugify", return_value="icon-slug-1")
    @patch("budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890")
    def test_icon_image(self, ShortUUIDField_get_default, jp_slugify) -> None:
        sut = models.IconImage(name="icon_1", image_type="svg+xml", body=b"<svg></svg>")
        sut.save()
        self.assertEqual(sut.name, "icon_1")
        self.assertEqual(sut.slug, "icon-slug-1")
        self.assertEqual(sut.image_type, "svg+xml")
        self.assertEqual(sut.id, "ab12345678901234567890")
        self.assertEqual(sut.body, b"<svg></svg>")
        self.assertEqual(
            sut.created_at.strftime(date_format), datetime(2022, 2, 22, 22, 22, 22, 222222).strftime(date_format)
        )
        self.assertEqual(
            sut.updated_at.strftime(date_format), datetime(2022, 2, 22, 22, 22, 22, 222222).strftime(date_format)
        )

    def test_to_data_uri(self):
        sut = models.IconImage(name="icon_1", image_type="svg+xml", body=b"<svg></svg>")
        sut.save()
        expected = 'data:image/svg+xml;base64,PHN2Zz48L3N2Zz4='
        actual = sut.to_data_uri()
        self.assertEqual(actual, expected)

    def test_get_default_icon(self):
        expected = {
            "name": "default icon",
            "slug": "default-icon",
            "image_type": "svg+xml",
            "body": b'<svg version="1.1" id="Ebene_1" xmlns="http://www.w3.org/2000/svg" '
            b'xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="100px" height="100px" '
            b'viewBox="0 0 100 100" enable-background="new 0 0 100 100" xml:space="preserve">'
            b'<circle fill="#B2B2B2" cx="50" cy="50" r="50"/><g>'
            b'<path d="M46.745,79.538c-3.866-0.402-8.458-1.449-12.324-3.705l2.255-6.444c2.819,2.095,'
            b'6.686,3.786,10.391,4.35l1.208-22.876c-5.961-5.075-12.244-10.391-12.244-18.769c0-8.539,'
            b'6.283-13.21,13.936-13.774l0.483-8.78h5.316l-0.483,9.021c2.578,0.322,5.559,1.128,8.861,'
            b'2.497l-1.853,5.639c-2.015-1.047-4.753-1.933-7.331-2.336l-1.208,21.588c6.122,5.155,12.646,'
            b'10.713,12.646,19.655c0,8.457-6.041,13.29-14.419,14.016l-0.563,10.149h-5.155L46.745,79.538z '
            b'M48.759,41.599l0.886-17.238c-3.544,0.645-6.364,2.9-6.364,7.169C43.281,35.477,45.618,38.619,'
            b'48.759,41.599z M53.27,55.132l-0.967,18.606c4.189-0.805,6.848-3.705,6.848-7.894S56.653,58.354,'
            b'53.27,55.132z"/></g></svg>',
        }
        actual = models.IconImage.get_default_icon()
        self.assertEqual(actual.name, expected["name"])
        self.assertEqual(actual.slug, expected["slug"])
        self.assertEqual(actual.body, expected["body"])
        self.assertEqual(actual.image_type, expected["image_type"])


class GovernmentTest(TestCase):
    def test_government_has_slug(self) -> None:
        sut = models.Government(name="まほろ市", slug="mahoro-city")
        sut.save()
        self.assertEqual(sut.name, "まほろ市")
        self.assertEqual(sut.slug, "mahoro-city")

    @patch("budgetmapper.models.jp_slugify", return_value="mahoro-shi")
    def test_government_generates_slug_if_not_provided(self, _: MagicMock) -> None:
        sut = models.Government(name="まほろ市")
        sut.save()
        self.assertEqual(sut.slug, "mahoro-shi")

    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        return_value="ab12345678901234567890",
    )
    def test_government_has_short_uuid_id(self, _: MagicMock) -> None:
        sut = models.Government(name="まほろ市")
        sut.save()
        self.assertEqual(sut.id, "ab12345678901234567890")

    def test_government_has_primary_color_code(self) -> None:
        sut = models.Government(name="まほろ市", primary_color_code="#111111")
        sut.save()
        self.assertEqual(sut.primary_color_code, "#111111")

    def test_government_has_primary_color_code_with_validation(self) -> None:
        sut = models.Government(
            name="まほろ市", latitude=40, longitude=30, primary_color_code="12", secondary_color_code="#123"
        )
        with self.assertRaises(ValidationError):
            sut.full_clean()
            sut.save()

    def test_government_has_secondary_color_code(self) -> None:
        sut = models.Government(name="まほろ市", secondary_color_code="#222")
        sut.save()
        self.assertEqual(sut.secondary_color_code, "#222")


class ClassificationSystemTest(TestCase):
    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        return_value="ab12345678901234567890",
    )
    def test_cs_has_short_uuid_id(self, _: MagicMock) -> None:
        sut = models.ClassificationSystem(name="まほろ市2101年度予算")
        sut.save()
        self.assertEqual(sut.id, "ab12345678901234567890")

    @patch("budgetmapper.models.jp_slugify", return_value="mahoro-shi-yosan")
    def test_cs_generates_slug_if_not_provided(self, _: MagicMock) -> None:
        sut = models.ClassificationSystem(name="まほろ市2101年度予算")
        sut.save()
        self.assertEqual(sut.slug, "mahoro-shi-yosan")

    def test_cs_has_slug(self) -> None:
        sut = models.ClassificationSystem(name="まほろ市2101年度予算", slug="special-slug")
        sut.save()
        self.assertEqual(sut.slug, "special-slug")

    def test_iterate_classifications(self) -> None:
        cs = factories.ClassificationSystemFactory()
        cl0 = factories.ClassificationFactory(classification_system=cs, code="1")
        cl00 = factories.ClassificationFactory(classification_system=cs, code="1.1", parent=cl0)
        cl01 = factories.ClassificationFactory(classification_system=cs, code="1.2", parent=cl0)
        cl1 = factories.ClassificationFactory(classification_system=cs, code="2")
        cl10 = factories.ClassificationFactory(classification_system=cs, code="2.1", parent=cl1)
        cl11 = factories.ClassificationFactory(classification_system=cs, code="2.2", parent=cl1)
        cl12 = factories.ClassificationFactory(classification_system=cs, code="2.3", parent=cl1)

        expected = [
            [cl0, cl00],
            [cl0, cl01],
            [cl1, cl10],
            [cl1, cl11],
            [cl1, cl12],
        ]
        actual = cs.iterate_classifications()
        self.assertIsInstance(actual, Iterator)
        for e, a in zip(expected, actual):
            self.assertEqual(a, e)


class ClassificationTest(TransactionTestCase):
    def test_classification_has_name(self) -> None:
        cs = factories.ClassificationSystemFactory()
        sut = models.Classification(name="総務費", classification_system=cs)
        sut.save()
        self.assertEqual(sut.name, "総務費")
        self.assertEqual(sut.classification_system, cs)
        self.assertEqual(sut.icon, None)
        self.assertIsNone(sut.code)
        self.assertIsNone(sut.parent)
        self.assertEqual(sut.level, 0)

    def test_classification_has_code(self) -> None:
        cs = factories.ClassificationSystemFactory()
        sut = models.Classification(name="総務費", classification_system=cs, code="2")
        sut.save()
        self.assertEqual(sut.code, "2")

    def test_branch_classification(self) -> None:
        root = factories.ClassificationFactory()
        sut = models.Classification(
            name="総務雑費",
            classification_system=root.classification_system,
            code="3",
            parent=root,
        )
        sut.save()
        self.assertEqual(sut.parent, root)
        self.assertEqual(sut.level, 1)

    def test_cs_coincides(self) -> None:
        root = factories.ClassificationFactory()
        sut = models.Classification(
            name="総務雑費",
            classification_system=root.classification_system,
            code="3",
            parent=root,
        )
        sut.save()
        sut.full_clean()

        cs1 = factories.ClassificationSystemFactory()
        cs2 = factories.ClassificationSystemFactory()
        root = factories.ClassificationFactory(classification_system=cs1)
        sut = models.Classification(name="不整合あり", classification_system=cs2, parent=root)
        with self.assertRaises(ValidationError):
            sut.save()
            sut.full_clean()

    def test_classification_has_item_order(self) -> None:
        cs = factories.ClassificationSystemFactory()
        sut0 = models.Classification(name="総務費", classification_system=cs)
        sut1 = models.Classification(name="総務雑貨", classification_system=cs)
        sut0.save()
        sut1.save()
        self.assertEqual(sut0.item_order, 0)
        self.assertEqual(sut1.item_order, 1)
        sut2 = models.Classification(name="上書き不可", classification_system=cs, item_order=1)
        with self.assertRaises(IntegrityError):
            sut2.save()
        sut10 = models.Classification(name="議会費", classification_system=cs, item_order=10)
        sut11 = models.Classification(name="民生貨", classification_system=cs)
        sut10.save()
        sut11.save()
        self.assertEqual(sut10.item_order, 10)
        self.assertEqual(sut11.item_order, 11)
        cs2 = factories.ClassificationSystemFactory()
        sut = models.Classification(name="農林水産業費", classification_system=cs2)
        sut.save()
        self.assertEqual(sut.item_order, 0)

    def test_classification_has_icon(self) -> None:
        icon = factories.IconImageFactory()
        cs = factories.ClassificationSystemFactory()
        sut = models.Classification(name="ワクワク費", classification_system=cs, icon=icon)
        self.assertEqual(sut.icon.id, icon.id)


class BasicBudgetTest(TestCase):
    @patch("budgetmapper.models.jp_slugify", return_value="a-slug")
    def test_budget_default(self, _: MagicMock) -> None:
        gov = factories.GovernmentFactory()
        cs = factories.ClassificationSystemFactory()
        sut = models.BasicBudget(name="まほろ市 2101 年度予算", year_value=2101, classification_system=cs, government_value=gov)
        sut.save()
        self.assertEqual(sut.name, "まほろ市 2101 年度予算")
        self.assertEqual(sut.slug, "a-slug")
        self.assertEqual(sut.subtitle, None)
        self.assertEqual(sut.year, 2101)
        self.assertEqual(sut.classification_system, cs)
        self.assertEqual(sut.government, gov)

    def test_budget_has_year(self) -> None:
        gov = factories.GovernmentFactory()
        cs = factories.ClassificationSystemFactory()
        sut = models.BasicBudget(
            name="まほろ市 2101 年度予算",
            year_value=2101,
            subtitle="改正案",
            slug="a-slug-mahoro",
            classification_system=cs,
            government_value=gov,
        )
        sut.save()
        self.assertEqual(sut.name, "まほろ市 2101 年度予算")
        self.assertEqual(sut.slug, "a-slug-mahoro")
        self.assertEqual(sut.subtitle, "改正案")
        self.assertEqual(sut.year, 2101)
        self.assertEqual(sut.classification_system, cs)
        self.assertEqual(sut.government, gov)

    def test_iterate_items(self) -> None:
        cs = factories.ClassificationSystemFactory()
        bud = factories.BasicBudgetFactory(classification_system=cs)
        cl0 = factories.ClassificationFactory(classification_system=cs)
        cl00 = factories.ClassificationFactory(classification_system=cs, parent=cl0)
        cl01 = factories.ClassificationFactory(classification_system=cs, parent=cl0)
        cl1 = factories.ClassificationFactory(classification_system=cs)
        cl10 = factories.ClassificationFactory(classification_system=cs, parent=cl1)
        cl11 = factories.ClassificationFactory(classification_system=cs, parent=cl1)
        cl12 = factories.ClassificationFactory(classification_system=cs, parent=cl1)
        cl13 = factories.ClassificationFactory(classification_system=cs, parent=cl1)

        abi00 = factories.AtomicBudgetItemFactory(budget=bud, classification=cl00)
        abi01 = factories.AtomicBudgetItemFactory(budget=bud, classification=cl01)
        abi10 = factories.AtomicBudgetItemFactory(budget=bud, classification=cl10)
        abi11 = factories.AtomicBudgetItemFactory(budget=bud, classification=cl11)
        abi12 = factories.AtomicBudgetItemFactory(budget=bud, classification=cl12)

        expected = [
            {"classifications": [cl0, cl00], "budget_item": abi00},
            {"classifications": [cl0, cl01], "budget_item": abi01},
            {"classifications": [cl1, cl10], "budget_item": abi10},
            {"classifications": [cl1, cl11], "budget_item": abi11},
            {"classifications": [cl1, cl12], "budget_item": abi12},
            {"classifications": [cl1, cl13], "budget_item": None},
        ]
        actual = bud.iterate_items()
        self.assertIsInstance(actual, Iterator)
        for e, a in zip(expected, actual):
            self.assertEqual(a, e)


class AtomicBudgetItemTestCase(TestCase):
    def test_atomic_budget_item_default(self) -> None:
        bud = factories.BasicBudgetFactory()
        cl = factories.ClassificationFactory(classification_system=bud.classification_system)
        sut = models.AtomicBudgetItem(value=123, classification=cl, budget=bud)
        sut.save()
        self.assertEqual(sut.value, 123)
        self.assertEqual(sut.budget, bud)
        self.assertEqual(sut.classification, cl)
        self.assertEqual(sut.amount, 123)
        self.assertEqual(bud.get_amount_of(cl), 123)

    def test_cs_must_coincide(self) -> None:
        cs1 = factories.ClassificationSystemFactory()
        bud = factories.BasicBudgetFactory(classification_system=cs1)
        cs2 = factories.ClassificationSystemFactory()
        cl = factories.ClassificationFactory(classification_system=cs2)
        sut = models.AtomicBudgetItem(value=10000, budget=bud, classification=cl)
        with self.assertRaises(ValidationError):
            sut.full_clean()


class MappedBudgetItemTestCase(TestCase):
    def test_mapped_budget_item_mapped_to_single_budget_item(self) -> None:
        orig_bud = factories.BasicBudgetFactory()
        orig_cl = factories.ClassificationFactory(classification_system=orig_bud.classification_system)
        atm = factories.AtomicBudgetItemFactory(classification=orig_cl, budget=orig_bud)
        bud = factories.MappedBudgetFactory(source_budget=orig_bud)
        cl = factories.ClassificationFactory(classification_system=bud.classification_system)
        sut = models.MappedBudgetItem(budget=bud, classification=cl)
        sut.save()
        sut.source_classifications.set([orig_cl])
        sut.save()
        self.assertEqual(sut.amount, atm.value)
        self.assertEqual(sut.budget, bud)
        self.assertEqual(sut.classification, cl)
        self.assertEqual(bud.get_amount_of(cl), atm.value)

    def test_mapped_budget_item_mapped_to_many_budget_item(self) -> None:
        orig_bud = factories.BasicBudgetFactory()
        atms = []
        for i in range(100):
            orig_cl = factories.ClassificationFactory(classification_system=orig_bud.classification_system)
            atms.append(factories.AtomicBudgetItemFactory(classification=orig_cl, budget=orig_bud))

        bud = factories.MappedBudgetFactory(source_budget=orig_bud)
        cl = factories.ClassificationFactory(classification_system=bud.classification_system)
        sut = models.MappedBudgetItem(budget=bud, classification=cl)
        sut.save()
        sut.source_classifications.set([atm.classification for atm in atms])
        sut.save()
        self.assertEqual(sut.amount, sum(atm.value for atm in atms))
        self.assertEqual(sut.budget, bud)
        self.assertEqual(sut.classification, cl)
        self.assertEqual(bud.get_amount_of(cl), sum(atm.value for atm in atms))


class ComplexBudgetItemTestCase(TestCase):
    def assert_datetime_equals(self, a, b):
        return self.assertEqual(a.strftime(date_format), b.strftime(date_format))

    def test_get_amount_of_tree_nodes(self) -> None:
        cs = factories.ClassificationSystemFactory()
        bud = factories.BasicBudgetFactory(classification_system=cs)
        cl0 = factories.ClassificationFactory(classification_system=cs)
        cl00 = factories.ClassificationFactory(classification_system=cs, parent=cl0)
        cl01 = factories.ClassificationFactory(classification_system=cs, parent=cl0)
        cl1 = factories.ClassificationFactory(classification_system=cs)
        cl10 = factories.ClassificationFactory(classification_system=cs, parent=cl1)

        abi00 = models.AtomicBudgetItem(value=123, budget=bud, classification=cl00)
        abi01 = models.AtomicBudgetItem(value=125, budget=bud, classification=cl01)
        abi10 = models.AtomicBudgetItem(value=127, budget=bud, classification=cl10)

        abi00.save()
        abi01.save()
        abi10.save()

        self.assertEqual(bud.get_amount_of(cl0), abi00.value + abi01.value)
        self.assertEqual(bud.get_amount_of(cl00), abi00.value)
        self.assertEqual(bud.get_amount_of(cl01), abi01.value)
        self.assertEqual(bud.get_amount_of(cl1), abi10.value)
        self.assertEqual(bud.get_amount_of(cl10), abi10.value)

    def test_get_amount_of_mapped_tree_nodes(self) -> None:
        cs0 = factories.ClassificationSystemFactory()
        bud0 = factories.BasicBudgetFactory(classification_system=cs0)
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

        self.assertAlmostEqual(bud1.get_amount_of(cl10), abi00.value + abi10.value + abi11.value)
        self.assertAlmostEqual(bud1.get_amount_of(cl100), abi00.value)
        self.assertAlmostEqual(bud1.get_amount_of(cl101), abi10.value + abi11.value)
        self.assertAlmostEqual(bud1.get_amount_of(cl11), abi01.value + abi12.value)
        self.assertAlmostEqual(bud1.get_amount_of(cl110), abi01.value + abi12.value)

    def test_basic_budget_updated_at_renewed_when_atomic_budget_item_added(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            cs = factories.ClassificationSystemFactory()
            gov = factories.GovernmentFactory(name="まほろ市")
            bud = models.BasicBudget(name="まほろ市予算", year_value=2101, government_value=gov, classification_system=cs)
            bud.save()
            other_bud = models.BasicBudget(
                name="無関係な予算", year_value=2101, government_value=gov, classification_system=cs
            )
            other_bud.save()
            cl0 = factories.ClassificationFactory(classification_system=cs)
            self.assert_datetime_equals(bud.created_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            models.AtomicBudgetItem(budget=bud, classification=cl0, value=123).save()
            bud.refresh_from_db()
            other_bud.refresh_from_db()
            self.assert_datetime_equals(bud.created_at, dt_orig)
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            self.assert_datetime_equals(other_bud.updated_at, dt_orig)

    def test_basic_budget_updated_at_renewed_when_atomic_budget_item_updated(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            cs = factories.ClassificationSystemFactory()
            gov = factories.GovernmentFactory(name="まほろ市")
            bud = models.BasicBudget(name="まほろ市予算", year_value=2101, government_value=gov, classification_system=cs)
            bud.save()
            other_bud = models.BasicBudget(
                name="無関係な予算", year_value=2101, government_value=gov, classification_system=cs
            )
            other_bud.save()
            cl0 = factories.ClassificationFactory(classification_system=cs)
            dt.tick(1000)
            abi0 = models.AtomicBudgetItem(budget=bud, classification=cl0, value=123)
            abi0.save()
            self.assert_datetime_equals(bud.created_at, dt_orig)
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            abi0.value = 123000
            abi0.save()
            bud.refresh_from_db()
            other_bud.refresh_from_db()
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            self.assert_datetime_equals(other_bud.updated_at, dt_orig)

    def test_basic_budget_updated_at_renewed_when_atomic_budget_item_deleted(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            cs = factories.ClassificationSystemFactory()
            gov = factories.GovernmentFactory(name="まほろ市")
            bud = models.BasicBudget(name="まほろ市予算", year_value=2101, government_value=gov, classification_system=cs)
            bud.save()
            other_bud = models.BasicBudget(
                name="無関係な予算", year_value=2101, government_value=gov, classification_system=cs
            )
            other_bud.save()
            cl0 = factories.ClassificationFactory(classification_system=cs)
            dt.tick(1000)
            abi0 = models.AtomicBudgetItem(budget=bud, classification=cl0, value=123)
            abi0.save()
            self.assert_datetime_equals(bud.created_at, dt_orig)
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            abi0.delete()
            bud.refresh_from_db()
            other_bud.refresh_from_db()
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            self.assert_datetime_equals(other_bud.updated_at, dt_orig)

    def test_basic_budget_updated_at_renewed_when_atomic_budget_item_deleted_from_manager(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            cs = factories.ClassificationSystemFactory()
            gov = factories.GovernmentFactory(name="まほろ市")
            bud = models.BasicBudget(name="まほろ市予算", year_value=2101, government_value=gov, classification_system=cs)
            bud.save()
            other_bud = models.BasicBudget(
                name="無関係な予算", year_value=2101, government_value=gov, classification_system=cs
            )
            other_bud.save()
            cl0 = factories.ClassificationFactory(classification_system=cs)
            dt.tick(1000)
            abi0 = models.AtomicBudgetItem(budget=bud, classification=cl0, value=123)
            abi0.save()
            self.assert_datetime_equals(bud.created_at, dt_orig)
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            models.AtomicBudgetItem.objects.all().delete()
            bud.refresh_from_db()
            other_bud.refresh_from_db()
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            self.assert_datetime_equals(other_bud.updated_at, dt_orig)

    def test_basic_budget_updated_at_renewed_when_classiification_system_updated(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            cs = models.ClassificationSystem(name="まほろ市予算体型")
            cs.save()
            other_cs = models.ClassificationSystem(name="まほろ市無関係予算体系")
            other_cs.save()
            gov = factories.GovernmentFactory(name="まほろ市")
            bud = models.BasicBudget(name="まほろ市予算", year_value=2101, government_value=gov, classification_system=cs)
            bud.save()
            other_bud = models.BasicBudget(
                name="無関係な予算", year_value=2101, government_value=gov, classification_system=other_cs
            )
            other_bud.save()
            dt.tick(1000)
            cs.name = "まほろ市予算体系"
            cs.save()
            bud.refresh_from_db()
            other_bud.refresh_from_db()
            self.assert_datetime_equals(bud.created_at, dt_orig)
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            self.assert_datetime_equals(other_bud.updated_at, dt_orig)

    def test_basic_budget_and_classification_updated_at_renewed_when_classification_added(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            cs = models.ClassificationSystem(name="まほろ市予算体型")
            cs.save()
            other_cs = models.ClassificationSystem(name="まほろ市無関係予算体系")
            other_cs.save()
            gov = factories.GovernmentFactory(name="まほろ市")
            bud = models.BasicBudget(name="まほろ市予算", year_value=2101, government_value=gov, classification_system=cs)
            bud.save()
            other_bud = models.BasicBudget(
                name="無関係な予算", year_value=2101, government_value=gov, classification_system=other_cs
            )
            other_bud.save()
            cl0 = models.Classification(classification_system=cs, name="議会費")
            cl0.save()
            self.assert_datetime_equals(bud.created_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            cl00 = models.Classification(classification_system=cs, name="議会費詳細", parent=cl0)
            cl00.save()
            bud.refresh_from_db()
            other_bud.refresh_from_db()
            cs.refresh_from_db()
            other_cs.refresh_from_db()
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            self.assert_datetime_equals(other_bud.updated_at, dt_orig)
            self.assert_datetime_equals(cs.updated_at, datetime.now())
            self.assert_datetime_equals(other_cs.updated_at, dt_orig)

    def test_basic_budget_and_classification_updated_at_renewed_when_classification_updated(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            cs = models.ClassificationSystem(name="まほろ市予算体系")
            cs.save()
            other_cs = models.ClassificationSystem(name="まほろ市無関係予算体系")
            other_cs.save()
            gov = factories.GovernmentFactory(name="まほろ市")
            bud = models.BasicBudget(name="まほろ市予算", year_value=2101, government_value=gov, classification_system=cs)
            bud.save()
            other_bud = models.BasicBudget(
                name="無関係な予算", year_value=2101, government_value=gov, classification_system=other_cs
            )
            other_bud.save()
            cl0 = models.Classification(classification_system=cs, name="ギカイ費")
            cl0.save()
            self.assert_datetime_equals(bud.created_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            cl0.name = "議会費"
            cl0.save()
            bud.refresh_from_db()
            other_bud.refresh_from_db()
            cs.refresh_from_db()
            other_cs.refresh_from_db()
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            self.assert_datetime_equals(other_bud.updated_at, dt_orig)
            self.assert_datetime_equals(cs.updated_at, datetime.now())
            self.assert_datetime_equals(other_cs.updated_at, dt_orig)

    def test_basic_budget_and_classification_updated_at_renewed_when_classification_deleted(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            cs = models.ClassificationSystem(name="まほろ市予算体系")
            cs.save()
            other_cs = models.ClassificationSystem(name="まほろ市無関係予算体系")
            other_cs.save()
            gov = factories.GovernmentFactory(name="まほろ市")
            bud = models.BasicBudget(name="まほろ市予算", year_value=2101, government_value=gov, classification_system=cs)
            bud.save()
            other_bud = models.BasicBudget(
                name="無関係な予算", year_value=2101, government_value=gov, classification_system=other_cs
            )
            other_bud.save()
            cl0 = models.Classification(classification_system=cs, name="議会費")
            cl0.save()
            self.assert_datetime_equals(bud.created_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            cl0.delete()
            bud.refresh_from_db()
            other_bud.refresh_from_db()
            cs.refresh_from_db()
            other_cs.refresh_from_db()
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            self.assert_datetime_equals(other_bud.updated_at, dt_orig)
            self.assert_datetime_equals(cs.updated_at, datetime.now())
            self.assert_datetime_equals(other_cs.updated_at, dt_orig)

    def test_mapped_budget_updated_at_renewed_when_source_budget_updated(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            gov = factories.GovernmentFactory(name="まほろ市")
            orig_cs = factories.ClassificationSystemFactory()
            orig_bud = models.BasicBudget(
                name="まほろ市余産", year_value=2101, government_value=gov, classification_system=orig_cs
            )
            orig_bud.save()
            cs = factories.ClassificationSystemFactory(name="COFOG")
            bud = models.MappedBudget(classification_system=cs, source_budget=orig_bud, name="まほろ市COFOG")
            bud.save()
            self.assert_datetime_equals(bud.created_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            orig_bud.name = "まほろ市予算"
            orig_bud.save()
            orig_bud.refresh_from_db()
            bud.refresh_from_db()
            self.assert_datetime_equals(orig_bud.updated_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())

    def test_mappd_budget_updated_at_renewed_when_classification_system_updated(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            gov = factories.GovernmentFactory(name="まほろ市")
            orig_bud = factories.BasicBudgetFactory(government_value=gov)
            cs = models.ClassificationSystem(name="C.O.F.O.G.")
            cs.save()
            bud = models.MappedBudget(classification_system=cs, source_budget=orig_bud, name="まほろ市COFOG")
            bud.save()
            self.assert_datetime_equals(bud.created_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            cs.name = "COFOG"
            cs.save()
            bud.refresh_from_db()
            orig_bud.refresh_from_db()
            self.assert_datetime_equals(orig_bud.updated_at, dt_orig)
            self.assert_datetime_equals(bud.updated_at, datetime.now())

    def test_mapped_budget_updated_at_renewed_when_mapped_budget_item_added(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            gov = factories.GovernmentFactory(name="まほろ市")
            orig_bud = factories.BasicBudgetFactory(government_value=gov)
            cs = factories.ClassificationSystemFactory()
            cl = factories.ClassificationFactory(classification_system=orig_bud.classification_system)
            bud = models.MappedBudget(classification_system=cs, source_budget=orig_bud, name="まほろ市COFOG")
            bud.save()
            self.assert_datetime_equals(bud.created_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            mbi = models.MappedBudgetItem(budget=bud, classification=cl)
            mbi.save()
            bud.refresh_from_db()
            orig_bud.refresh_from_db()
            self.assert_datetime_equals(orig_bud.updated_at, dt_orig)
            self.assert_datetime_equals(bud.updated_at, datetime.now())

    def test_mapped_budget_updated_at_renewed_when_mapped_budget_item_updated(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            gov = factories.GovernmentFactory(name="まほろ市")
            orig_bud = factories.BasicBudgetFactory(government_value=gov)
            orig_cl = factories.ClassificationFactory(classification_system=orig_bud.classification_system)
            cs = factories.ClassificationSystemFactory()
            cl = factories.ClassificationFactory(classification_system=orig_bud.classification_system)
            bud = models.MappedBudget(classification_system=cs, source_budget=orig_bud, name="まほろ市COFOG")
            bud.save()
            mbi = models.MappedBudgetItem(budget=bud, classification=cl)
            mbi.save()
            self.assert_datetime_equals(bud.created_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            mbi.source_classifications.set([orig_cl])
            mbi.save()
            bud.refresh_from_db()
            orig_bud.refresh_from_db()
            self.assert_datetime_equals(orig_bud.updated_at, dt_orig)
            self.assert_datetime_equals(bud.updated_at, datetime.now())

    def test_mapped_budget_updated_at_renewed_when_mapped_budget_item_deleted(self) -> None:
        dt_orig = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt_orig) as dt:
            gov = factories.GovernmentFactory(name="まほろ市")
            orig_bud = factories.BasicBudgetFactory(government_value=gov)
            cs = factories.ClassificationSystemFactory()
            cl = factories.ClassificationFactory(classification_system=orig_bud.classification_system)
            bud = models.MappedBudget(classification_system=cs, source_budget=orig_bud, name="まほろ市COFOG")
            bud.save()
            mbi = models.MappedBudgetItem(budget=bud, classification=cl)
            mbi.save()
            self.assert_datetime_equals(bud.created_at, datetime.now())
            self.assert_datetime_equals(bud.updated_at, datetime.now())
            dt.tick(1000)
            mbi.delete()
            bud.refresh_from_db()
            orig_bud.refresh_from_db()
            self.assert_datetime_equals(orig_bud.updated_at, dt_orig)
            self.assert_datetime_equals(bud.updated_at, datetime.now())


class BlobTestCase(TestCase):
    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        side_effect=[
            "ab12345678901234567890",
            "ab12345678901234567891",
            "ab12345678901234567892",
        ],
    )
    def test_blob_write_and_reader(self, _):
        raw_data = BytesIO(b"F" * 65537)
        name = "test"
        blob = models.Blob.write(raw_data, name=name)
        self.assertEqual(blob.id, "ab12345678901234567890")
        self.assertEqual(blob.name, "test")
        c1, c2 = models.BlobChunk.objects.filter(blob=blob).order_by("index")
        self.assertEqual(c1.id, "ab12345678901234567891")
        self.assertEqual(bytes(c1.body), b"F" * 65536)
        self.assertEqual(c1.index, 0)

        self.assertEqual(c2.id, "ab12345678901234567892")
        self.assertEqual(bytes(c2.body), b"F")
        self.assertEqual(c2.index, 1)

        reader = models.BlobReader(blob)
        expected = b"FFF"
        actual = reader.read(3)
        self.assertEqual(actual, expected)
        expected = b"F" * 65534
        actual = reader.read()
        self.assertEqual(actual, expected)


class WdmmgTreeCacheTestCase(TransactionTestCase):
    def test_wdmmg_tree_cache(self):
        raw_data = BytesIO(json.dumps({"a": 1}).encode("utf-8"))
        blob = models.Blob.write(raw_data, name="cache")
        budget = factories.BasicBudgetFactory()
        dt = datetime(2021, 1, 31, 12, 23, 34, 5678)
        with freezegun.freeze_time(dt), patch(
            "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
            return_value="ab12345678901234567890",
        ):
            actual = models.WdmmgTreeCache(budget=budget, blob=blob)
            actual.save()
            self.assertEqual(actual.id, "ab12345678901234567890")
            self.assertEqual(actual.blob.id, blob.id)
            self.assertEqual(actual.budget.id, budget.id)
            self.assertEqual(
                actual.created_at.strftime("%Y%m%d%H%M%S%f"),
                dt.strftime("%Y%m%d%H%M%S%f"),
            )
            self.assertEqual(
                actual.updated_at.strftime("%Y%m%d%H%M%S%f"),
                dt.strftime("%Y%m%d%H%M%S%f"),
            )

    @patch("budgetmapper.models.BytesIO")
    @patch("budgetmapper.models.Blob.write")
    def test_cache_tree(self, Blob_write, BytesIO):
        blob0, blob1 = factories.BlobFactory(), factories.BlobFactory()
        Blob_write.side_effect = [blob0, blob1]
        bud = factories.BasicBudgetFactory()
        data0 = {"a": 1}
        actual0 = models.WdmmgTreeCache.cache_tree(data0, bud)
        self.assertEqual(actual0.budget.id, bud.id)
        self.assertEqual(actual0.blob.id, blob0.id)
        data1 = {"b": 1}
        actual1 = models.WdmmgTreeCache.cache_tree(data1, bud)
        self.assertEqual(actual1.budget.id, bud.id)
        self.assertEqual(actual1.blob.id, blob1.id)
        self.assertEqual(actual1.id, actual0.id)
        Blob_write.assert_has_calls(
            [
                call(BytesIO.return_value, name=bud.name),
                call(BytesIO.return_value, name=bud.name),
            ]
        )
        BytesIO.assert_has_calls(
            [
                call(json.dumps(data0).encode("utf-8")),
                call(json.dumps(data1).encode("utf-8")),
            ]
        )

    @patch("budgetmapper.models.BlobReader")
    def test_get_or_none_returns_data_when_budget_is_older(self, BlobReader):
        BlobReader.return_value.read.return_value = b'{"a":1}'
        with freezegun.freeze_time(datetime(2021, 1, 31, 12, 23, 34, 5678)) as dt:
            blob = factories.BlobFactory()
            bud = factories.BasicBudgetFactory()
            dt.tick(1000)
            cache = models.WdmmgTreeCache(blob=blob, budget=bud)
            cache.save()
            expected = {"a": 1}
            actual = models.WdmmgTreeCache.get_or_none(bud)
            self.assertEqual(actual, expected)

    def test_get_or_none_returns_none_when_no_cache(self):
        bud = factories.BasicBudgetFactory()
        actual = models.WdmmgTreeCache.get_or_none(bud)
        self.assertIsNone(actual)

    def test_get_or_none_returns_none_when_budget_is_newer(self):
        with freezegun.freeze_time(datetime(2021, 1, 31, 12, 23, 34, 5678)) as dt:
            blob = factories.BlobFactory()
            bud = factories.BasicBudgetFactory()
            cache = models.WdmmgTreeCache(blob=blob, budget=bud)
            cache.save()
            dt.tick(1000)
            blob.updated_at = dt
            blob.save()
            actual = models.WdmmgTreeCache.get_or_none(bud)
            self.assertIsNone(actual)
