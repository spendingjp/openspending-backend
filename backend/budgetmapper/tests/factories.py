import random

import factory
from budgetmapper import models
from factory import fuzzy
from factory.django import DjangoModelFactory


class GovernmentFactory(DjangoModelFactory):
    class Meta:
        model = models.Government

    name = fuzzy.FuzzyText(suffix="市")


class ClassificationSystemFactory(DjangoModelFactory):
    class Meta:
        model = models.ClassificationSystem

    name = fuzzy.FuzzyText(suffix="予算")
    level_names = ["款", "項", "目", "事業", "節", "節細"]


def get_max_item_order_plus_one():
    q = models.Classification.objects.order_by("-item_order")
    if q.count() == 0:
        return 0
    return q[0].item_order + 1


class ClassificationFactory(DjangoModelFactory):
    class Meta:
        model = models.Classification

    name = fuzzy.FuzzyText(length=5, suffix="費")
    code = factory.LazyFunction(lambda: None if random.randint(0, 2) % 2 else str(random.randint(1, 15)))
    classification_system = factory.SubFactory(ClassificationSystemFactory)
    item_order = fuzzy.FuzzyAttribute(get_max_item_order_plus_one)
    parent = None


class BudgetFactory(DjangoModelFactory):
    class Meta:
        model = models.Budget

    name = fuzzy.FuzzyText(suffix="予算")
    year = fuzzy.FuzzyInteger(1900, high=2200)
    subtitle = fuzzy.FuzzyText()
    classification_system = factory.SubFactory(ClassificationSystemFactory)
    government = factory.SubFactory(GovernmentFactory)


class AtomicBudgetItemFactory(DjangoModelFactory):
    class Meta:
        model = models.AtomicBudgetItem

    value = fuzzy.FuzzyFloat(1000.0, high=1000000.0)
    budget = factory.SubFactory(BudgetFactory)
    classification = factory.SubFactory(ClassificationFactory)


class MappedBudgetItemFactory(DjangoModelFactory):
    class Meta:
        model = models.MappedBudgetItem

    budget = factory.SubFactory(BudgetFactory)
    classification = factory.SubFactory(ClassificationFactory)
    mapped_budget = factory.SubFactory(BudgetFactory)

    @factory.post_generation
    def mapped_classifications(self, create, extracted, **kwargs):
        if create:
            for _ in range(random.randint(1, 10)):
                self.mapped_classifications.add(
                    ClassificationFactory(classification_system=self.mapped_budget.classification_system)
                )
            return


class BlobFactory(DjangoModelFactory):
    class Meta:
        model = models.Blob
