import doctest
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

from budgetmapper import models
from django.core.exceptions import ValidationError
from django.test import TestCase

from . import factories


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(models))
    return tests


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

    @patch("budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890")
    def test_government_has_short_uuid_id(self, _: MagicMock) -> None:
        sut = models.Government(name="まほろ市")
        sut.save()
        self.assertEqual(sut.id, "ab12345678901234567890")


class ClassificationSystemTest(TestCase):
    @patch("budgetmapper.models.shortuuidfield.ShortUUIDField.get_default", return_value="ab12345678901234567890")
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
        cl0 = factories.ClassificationFactory(classification_system=cs)
        cl00 = factories.ClassificationFactory(classification_system=cs, parent=cl0)
        cl01 = factories.ClassificationFactory(classification_system=cs, parent=cl0)
        cl1 = factories.ClassificationFactory(classification_system=cs)
        cl10 = factories.ClassificationFactory(classification_system=cs, parent=cl1)
        cl11 = factories.ClassificationFactory(classification_system=cs, parent=cl1)
        cl12 = factories.ClassificationFactory(classification_system=cs, parent=cl1)

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


class ClassificationTest(TestCase):
    def test_classification_has_name(self) -> None:
        cs = factories.ClassificationSystemFactory()
        sut = models.Classification(name="総務費", classification_system=cs)
        sut.save()
        self.assertEqual(sut.name, "総務費")
        self.assertEqual(sut.classification_system, cs)
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
            name="総務雑費", classification_system=root.classification_system, code="3", parent=root
        )
        sut.save()
        self.assertEqual(sut.parent, root)
        self.assertEqual(sut.level, 1)

    def test_cs_coincides(self) -> None:
        root = factories.ClassificationFactory()
        sut = models.Classification(
            name="総務雑費", classification_system=root.classification_system, code="3", parent=root
        )
        sut.full_clean()

        cs1 = factories.ClassificationSystemFactory()
        cs2 = factories.ClassificationSystemFactory()
        root = factories.ClassificationFactory(classification_system=cs1)
        sut = models.Classification(name="不整合あり", classification_system=cs2, parent=root)
        with self.assertRaises(ValidationError):
            sut.full_clean()


class BudgetTest(TestCase):
    @patch("budgetmapper.models.jp_slugify", return_value="a-slug")
    def test_budget_default(self, _: MagicMock) -> None:
        gov = factories.GovernmentFactory()
        cs = factories.ClassificationSystemFactory()
        sut = models.Budget(name="まほろ市 2101 年度予算", year=2101, classification_system=cs, government=gov)
        sut.save()
        self.assertEqual(sut.name, "まほろ市 2101 年度予算")
        self.assertEqual(sut.slug, "a-slug")
        self.assertEqual(sut.subtitle, "")
        self.assertEqual(sut.year, 2101)
        self.assertEqual(sut.classification_system, cs)
        self.assertEqual(sut.government, gov)

    def test_budget_has_year(self) -> None:
        gov = factories.GovernmentFactory()
        cs = factories.ClassificationSystemFactory()
        sut = models.Budget(
            name="まほろ市 2101 年度予算",
            year=2101,
            subtitle="改正案",
            slug="a-slug-mahoro",
            classification_system=cs,
            government=gov,
        )
        sut.save()
        self.assertEqual(sut.name, "まほろ市 2101 年度予算")
        self.assertEqual(sut.slug, "a-slug-mahoro")
        self.assertEqual(sut.subtitle, "改正案")
        self.assertEqual(sut.year, 2101)
        self.assertEqual(sut.classification_system, cs)
        self.assertEqual(sut.government, gov)

    def test_iterate_classifications(self) -> None:
        cs = factories.ClassificationSystemFactory()
        bud = factories.BudgetFactory(classification_system=cs)
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
        bud = factories.BudgetFactory()
        cl = factories.ClassificationFactory(classification_system=bud.classification_system)
        sut = models.AtomicBudgetItem(amount=123, classification=cl, budget=bud)
        sut.save()
        self.assertEqual(sut.value, 123)
        self.assertEqual(sut.budget, bud)
        self.assertEqual(sut.classification, cl)

        self.assertEqual(bud.get_value_of(cl), 123)

    def test_cs_must_coincide(self) -> None:
        cs1 = factories.ClassificationSystemFactory()
        bud = factories.BudgetFactory(classification_system=cs1)
        cs2 = factories.ClassificationSystemFactory()
        cl = factories.ClassificationFactory(classification_system=cs2)
        sut = models.AtomicBudgetItem(amount=10000, budget=bud, classification=cl)
        with self.assertRaises(ValidationError):
            sut.full_clean()


class MappedBudgetItemTestCase(TestCase):
    def test_mapped_budget_item_mapped_to_single_budget_item(self) -> None:
        orig_bud = factories.BudgetFactory()
        orig_cl = factories.ClassificationFactory(classification_system=orig_bud.classification_system)
        atm = factories.AtomicBudgetItemFactory(classification=orig_cl, budget=orig_bud)
        bud = factories.BudgetFactory()
        cl = factories.ClassificationFactory(classification_system=bud.classification_system)
        sut = models.MappedBudgetItem(budget=bud, classification=cl, mapped_budget=orig_bud)
        sut.save()
        sut.mapped_classifications.set([orig_cl])
        sut.save()
        self.assertEqual(sut.value, atm.value)
        self.assertEqual(sut.budget, bud)
        self.assertEqual(sut.classification, cl)
        self.assertEqual(bud.get_value_of(cl), atm.value)

    def test_mapped_budget_item_mapped_to_many_budget_item(self) -> None:
        orig_bud = factories.BudgetFactory()
        atms = []
        for i in range(100):
            orig_cl = factories.ClassificationFactory(classification_system=orig_bud.classification_system)
            atms.append(factories.AtomicBudgetItemFactory(classification=orig_cl, budget=orig_bud))

        bud = factories.BudgetFactory()
        cl = factories.ClassificationFactory(classification_system=bud.classification_system)
        sut = models.MappedBudgetItem(budget=bud, classification=cl, mapped_budget=orig_bud)
        sut.save()
        sut.mapped_classifications.set([atm.classification for atm in atms])
        sut.save()
        self.assertEqual(sut.value, sum(atm.value for atm in atms))
        self.assertEqual(sut.budget, bud)
        self.assertEqual(sut.classification, cl)
        self.assertEqual(bud.get_value_of(cl), sum(atm.value for atm in atms))


class ComplexBudgetItemTestCase(TestCase):
    def test_get_value_of_tree_nodes(self) -> None:
        cs = factories.ClassificationSystemFactory()
        bud = factories.BudgetFactory(classification_system=cs)
        cl0 = factories.ClassificationFactory(classification_system=cs)
        cl00 = factories.ClassificationFactory(classification_system=cs, parent=cl0)
        cl01 = factories.ClassificationFactory(classification_system=cs, parent=cl0)
        cl1 = factories.ClassificationFactory(classification_system=cs)
        cl10 = factories.ClassificationFactory(classification_system=cs, parent=cl1)

        abi00 = models.AtomicBudgetItem(amount=123, budget=bud, classification=cl00)
        abi01 = models.AtomicBudgetItem(amount=125, budget=bud, classification=cl01)
        abi10 = models.AtomicBudgetItem(amount=127, budget=bud, classification=cl10)

        abi00.save()
        abi01.save()
        abi10.save()

        self.assertEqual(bud.get_value_of(cl0), abi00.value + abi01.value)
        self.assertEqual(bud.get_value_of(cl00), abi00.value)
        self.assertEqual(bud.get_value_of(cl01), abi01.value)
        self.assertEqual(bud.get_value_of(cl1), abi10.value)
        self.assertEqual(bud.get_value_of(cl10), abi10.value)

    def test_get_value_of_mapped_tree_nodes(self) -> None:
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

        self.assertEqual(bud1.get_value_of(cl10), abi00.value + abi10.value + abi11.value)
        self.assertEqual(bud1.get_value_of(cl100), abi00.value)
        self.assertEqual(bud1.get_value_of(cl101), abi10.value + abi11.value)
        self.assertEqual(bud1.get_value_of(cl11), abi01.value + abi12.value)
        self.assertEqual(bud1.get_value_of(cl110), abi01.value + abi12.value)


class BlobTestCase(TestCase):
    @patch(
        "budgetmapper.models.shortuuidfield.ShortUUIDField.get_default",
        side_effect=["ab12345678901234567890", "ab12345678901234567891", "ab12345678901234567892"],
    )
    def test_blob_write_and_reader(self, _):
        from io import BytesIO

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
