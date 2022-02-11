from unittest.mock import patch

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


class ClassificationSystemSerializerTestCase(TestCase):
    def test_classification_system_serializer(self):
        cs = factories.ClassificationSystemFactory()
        sut = serializers.ClassificationSystemSerializer(instance=cs)
        expected = {
            "id": cs.id,
            "slug": cs.slug,
            "name": cs.name,
            "level_names": cs.level_names,
            "created_at": cs.created_at.strftime(datetime_format),
            "updated_at": cs.updated_at.strftime(datetime_format),
        }
        actual = sut.data
        self.assertEqual(actual, expected)


class WdmmgSerializerTestCase(TestCase):
    def test_get_budgets(self):
        from budgetmapper.models import IconImage

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
        bud = factories.BudgetFactory(
            name="まほろ市2101年度予算",
            slug="mahoro-city-2101",
            government=gov,
            classification_system=cs,
        )

        abi000 = factories.AtomicBudgetItemFactory(value=123.0, budget=bud, classification=cl000)
        abi001 = factories.AtomicBudgetItemFactory(value=125.0, budget=bud, classification=cl001)
        abi002 = factories.AtomicBudgetItemFactory(value=127.0, budget=bud, classification=cl002)
        abi010 = factories.AtomicBudgetItemFactory(value=129.0, budget=bud, classification=cl010)
        abi100 = factories.AtomicBudgetItemFactory(value=131.0, budget=bud, classification=cl100)

        expected = [
            {
                "id": cl0.id,
                "name": cl0.name,
                "code": cl0.code,
                "amount": abi000.amount + abi001.amount + abi002.amount + abi010.amount,
                "icon_slug": icon0.slug,
                "children": [
                    {
                        "id": cl00.id,
                        "name": cl00.name,
                        "code": cl00.code,
                        "icon_slug": icon00.slug,
                        "amount": abi000.amount + abi001.amount + abi002.amount,
                        "children": [
                            {
                                "id": cl000.id,
                                "name": cl000.name,
                                "code": cl000.code,
                                "amount": abi000.amount,
                                "icon_slug": IconImage.get_default_icon().slug,
                                "children": None,
                            },
                            {
                                "id": cl001.id,
                                "name": cl001.name,
                                "code": cl001.code,
                                "amount": abi001.amount,
                                "icon_slug": IconImage.get_default_icon().slug,
                                "children": None,
                            },
                            {
                                "id": cl002.id,
                                "name": cl002.name,
                                "code": cl002.code,
                                "amount": abi002.amount,
                                "icon_slug": IconImage.get_default_icon().slug,
                                "children": None,
                            },
                        ],
                    },
                    {
                        "id": cl01.id,
                        "name": cl01.name,
                        "code": cl01.code,
                        "amount": abi010.amount,
                        "icon_slug": icon01.slug,
                        "children": [
                            {
                                "id": cl010.id,
                                "name": cl010.name,
                                "code": cl010.code,
                                "amount": abi010.amount,
                                "icon_slug": IconImage.get_default_icon().slug,
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
                "icon_slug": IconImage.get_default_icon().slug,
                "children": [
                    {
                        "id": cl10.id,
                        "name": cl10.name,
                        "code": cl10.code,
                        "amount": abi100.amount,
                        "icon_slug": IconImage.get_default_icon().slug,
                        "children": [
                            {
                                "id": cl100.id,
                                "name": cl100.name,
                                "code": cl100.code,
                                "amount": abi100.amount,
                                "icon_slug": IconImage.get_default_icon().slug,
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
                "icon_slug": IconImage.get_default_icon().slug,
                "children": [
                    {
                        "id": cl20.id,
                        "name": cl20.name,
                        "code": cl20.code,
                        "amount": 0,
                        "icon_slug": IconImage.get_default_icon().slug,
                        "children": [
                            {
                                "id": cl200.id,
                                "name": cl200.name,
                                "code": cl200.code,
                                "amount": 0,
                                "icon_slug": IconImage.get_default_icon().slug,
                                "children": None,
                            }
                        ],
                    }
                ],
            },
        ]
        actual = serializers.WdmmgSerializer().get_budgets(obj=bud)
        self.assertEqual(actual, expected)

    @patch("budgetmapper.serializers.models.WdmmgTreeCache.get_or_none", return_value=None)
    @patch("budgetmapper.serializers.models.WdmmgTreeCache.cache_tree")
    def test_get_budgets_creates_cache(self, cache_tree, get_or_none):
        bud = factories.BudgetFactory()
        serializers.WdmmgSerializer().get_budgets(obj=bud)
        cache_tree.assert_called_once_with([], bud)
        get_or_none.assert_called_once_with(bud)

    @patch(
        "budgetmapper.serializers.models.WdmmgTreeCache.get_or_none",
        return_value=[{"a": 1}],
    )
    def test_get_budgets_uses_cache_when_available(self, get_or_none):
        bud = factories.BudgetFactory()
        expected = [{"a": 1}]
        actual = serializers.WdmmgSerializer().get_budgets(obj=bud)
        self.assertEqual(actual, expected)
        get_or_none.assert_called_once_with(bud)
