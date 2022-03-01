import csv
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

    abikoshi = models.Government.objects.get_or_create(
        slug="abiko-shi", defaults={"name": "我孫子市", "latitude": 35.8644, "longitude": 140.0283}
    )[0]
    orig_col_names = ("所属", "款", "項", "目", "事業", "節", "細節")

    cs = models.ClassificationSystem.objects.get_or_create(
        slug="abiko-shi-2021-nendo-yosan",
        defaults={"name": "我孫子市2021年度予算", "level_names": orig_col_names},
    )[0]
    budget = models.BasicBudget.objects.get_or_create(
        slug="abiko-shi-2021-nendo-yosan",
        defaults={
            "name": "我孫子市2021年度予算",
            "year_value": 2021,
            "government_value": abikoshi,
            "subtitle": "",
            "classification_system": cs,
        },
    )[0]
    cofog_cs = models.ClassificationSystem.objects.get(slug="cofog")
    cofog_budget = models.MappedBudget.objects.get_or_create(
        slug="abiko-shi-cofog2021",
        defaults={
            "source_budget": budget,
            "name": "我孫子市COFOG2021",
            "classification_system": cofog_cs,
        },
    )[0]
    models.DefaultBudget.objects.get_or_create(government=abikoshi, budget=cofog_budget)
    models.MappedBudgetItem.objects.filter(budget=cofog_budget).delete()
    models.AtomicBudgetItem.objects.filter(budget=budget).delete()
    models.Classification.objects.filter(classification_system=cs).delete()

    class_id_map = {}
    with open(args.input, "r") as fin:
        reader = csv.DictReader(fin)
        for d in reader:
            parent = None
            class_data = []
            for cn in orig_col_names:
                code = d[cn]
                name = d[f"{cn}名"]
                class_data += [code, name]
                class_key = tuple(class_data)
                if class_key not in class_id_map:
                    c = models.Classification.objects.create(
                        name=name, code=code, classification_system=cs, parent_id=parent
                    )
                    class_id_map[class_key] = c.id
                class_id = class_id_map[class_key]
                parent = class_id
            class_id = class_id_map[tuple(class_data)]
            abi = models.AtomicBudgetItem.objects.create(
                budget=budget, value=float(d["予算額"]), classification_id=class_id
            )
            cofog_code = d["COFOG_Level2"]
            cofog_class = models.Classification.objects.get(classification_system=cofog_cs, code=cofog_code)
            mbi = models.MappedBudgetItem.objects.get_or_create(budget=cofog_budget, classification=cofog_class)[0]
            mbi.source_classifications.set(
                list(mbi.source_classifications.all()) + [models.Classification.objects.get(pk=class_id)]
            )
            mbi.save()
