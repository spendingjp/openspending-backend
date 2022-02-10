import csv
import os
from argparse import ArgumentParser
from collections import defaultdict

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wdmmgserver.settings')
django.setup()

from budgetmapper import models

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args()

    tsukuba = models.Government.objects.get(slug="tsukuba-shi")
    cofog = models.ClassificationSystem.objects.get(slug="cofog")
    tsukuba_budget = models.Budget.objects.get(slug="tsukuba-shi-2021-nendo-yosan")
    try:
        budget = models.Budget(
            name="つくば市COFOG2021", year=2021, subtitle="", classification_system=cofog, government=tsukuba
        )
        budget.save()
    except:
        budget = models.Budget.objects.get(slug="tsukuba-shi-cofog2021")

    buf = defaultdict(list)
    with open(args.input, "r") as fin:
        reader = csv.DictReader(fin)
        for d in reader:
            target_id = models.Classification.objects.get(name=d["COFOGLevel3Ja"], code=d["COFOGLevel3"]).id
            pid = None
            for i in range(3, 14, 2):
                pid = models.Classification.objects.get(
                    parent=pid, code=d[reader.fieldnames[i]], name=d[reader.fieldnames[i + 1]]
                )
            buf[target_id].append(pid.id)
    for k, v in buf.items():
        x = models.MappedBudgetItem(
            budget=budget,
            classification=models.Classification.objects.get(id=k),
            mapped_budget=tsukuba_budget,
        )
        x.save()
        x.mapped_classifications.set([models.Classification.objects.get(id=vv) for vv in v])
        x.save()
