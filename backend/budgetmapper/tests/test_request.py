import csv
import io
from codecs import getreader

from django.test import Client, TestCase

from . import factories


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
