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
        cs = models.ClassificationSystem.objects.get(slug="cofog")
        models.Classification.objects.filter(classification_system=cs).delete()
    except models.ClassificationSystem.DoesNotExist:
        cs = models.ClassificationSystem(name="COFOG")
        cs.save()

    def recreg(data, parent=None):
        icon_slug = data["icon-slug"]
        if icon_slug is not None:
            try:
                icon = models.IconImage.objects.get(slug=icon_slug)
            except models.IconImage.DoesNotExist:
                icon = None
        else:
            icon = None
        inst = models.Classification(
            name=data["name"], code=data["code"], classification_system=cs, parent=parent, icon=icon
        )
        inst.save()
        if "children" in data:
            for d in data["children"]:
                recreg(d, parent=inst)

    for d in data:
        recreg(d)
