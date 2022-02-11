import json
import os
from argparse import ArgumentParser

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wdmmgserver.settings')
django.setup()

from budgetmapper import models

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args()
    with open(args.input, "r") as fin:
        data = json.load(fin)["data"]

    try:
        tsukuba = models.Government.objects.get(slug="tsukuba-shi")
    except models.Government.DoesNotExist:
        tsukuba = models.Government(name="つくば市", latitude=36.0825081, longitude=140.1107132)
        tsukuba.save()
    try:
        tsukuba2021cs = models.ClassificationSystem.objects.get(slug="tsukuba-shi-2021-nendo-yosan")
        models.Classification.objects.filter(classification_system=tsukuba2021cs).delete()
    except models.ClassificationSystem.DoesNotExist:
        tsukuba2021cs = models.ClassificationSystem(name="つくば市2021年度予算")
        tsukuba2021cs.save()
    try:
        budget = models.Budget.objects.get(slug="tsukuba-shi-2021-nendo-yosan")
        models.BudgetItemBase.objects.filter(budget=budget).delete()
    except models.Budget.DoesNotExist:
        budget = models.Budget(
            name="つくば市2021年度予算", year=2021, subtitle="", classification_system=tsukuba2021cs, government=tsukuba
        )
        budget.save()

    def recreg(data, parent=None):
        inst = models.Classification(
            code=data["code"], name=data["name"], classification_system=tsukuba2021cs, parent=parent
        )
        inst.save()
        if "children" in data:
            for d in data["children"]:
                recreg(d, parent=inst)
        else:
            models.AtomicBudgetItem(budget=budget, value=data["value"], classification=inst).save()

    for d in data:
        recreg(d)
