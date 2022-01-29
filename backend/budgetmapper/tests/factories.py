import random

import factory
from budgetmapper import models
from factory import fuzzy
from factory.django import DjangoModelFactory


class GovernmentFactory(DjangoModelFactory):
    class Meta:
        model = models.Government

    name = fuzzy.FuzzyText(suffix="市")


class ClassificationLevelNameListFactory(DjangoModelFactory):
    class Meta:
        model = models.ClassificationLevelNameList

    names = ["款", "項", "目", "事業", "節", "節細"]


class ClassificationSystemFactory(DjangoModelFactory):
    class Meta:
        model = models.ClassificationSystem

    name = fuzzy.FuzzyText(suffix="予算")
    level_names = factory.SubFactory(ClassificationLevelNameListFactory)


class ClassificationFactory(DjangoModelFactory):
    class Meta:
        model = models.Classification

    name = fuzzy.FuzzyText(length=5, suffix="費")
    code = factory.LazyFunction(lambda: None if random.randint(0, 2) % 2 else str(random.randint(1, 15)))
    classification_system = factory.SubFactory(ClassificationSystemFactory)
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

    amount = fuzzy.FuzzyInteger(1000, high=1000000, step=1000)
    budget = factory.SubFactory(BudgetFactory)
    classification = factory.SubFactory(ClassificationFactory)
