from django.db import IntegrityError
from rest_framework import fields, serializers, status, validators
from rest_framework.views import Response, exception_handler

from . import models


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    print(exc)
    print(context)

    if isinstance(exc, IntegrityError) and not response:
        response = Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return response


class GovernmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Government
        fields = ("id", "name", "slug", "latitude", "longitude", "created_at", "updated_at")


class ClassificationSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClassificationSystem
        fields = ("id", "name", "slug", "level_names", "created_at", "updated_at")


class ClassificationSystemDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = models.ClassificationSystem
        fields = (
            "id",
            "name",
            "slug",
            "level_names",
            "created_at",
            "updated_at",
            "items",
        )

    def get_items(self, obj):
        return ClassificationSerializer(models.Classification.objects.filter(classification_system=obj), many=True).data


class ClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Classification
        fields = ("id", "code", "name", "classification_system", "parent", "created_at", "updated_at")


class BudgetItemSerializer(serializers.ModelSerializer):
    classification = ClassificationSerializer()

    class Meta:
        model = models.BudgetItemBase
        fields = (
            "id",
            "classification",
            "value",
        )


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Budget
        fields = (
            "id",
            "name",
            "slug",
            "year",
            "subtitle",
            "classification_system",
            "government",
            "created_at",
            "updated_at",
        )


class BudgetDetailSerializer(serializers.ModelSerializer):
    classification_system = ClassificationSystemSerializer()
    government = GovernmentSerializer()
    items = serializers.SerializerMethodField()

    class Meta:
        model = models.Budget
        fields = (
            "id",
            "name",
            "slug",
            "year",
            "subtitle",
            "classification_system",
            "government",
            "created_at",
            "updated_at",
            "items",
        )

    def get_items(self, obj):
        return BudgetItemSerializer(
            models.BudgetItemBase.objects.filter(budget=obj).prefetch_related("classification"), many=True
        ).data


class BudgetNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Classification
        fields = ("id", "name", "code")

    def to_representation(self, instance):
        is_leaf = True
        children = []
        for c in instance.direct_children:
            children.append(BudgetNodeSerializer(instance=c, context={"budget": self.context["budget"]}).data)
            is_leaf = False
        if is_leaf:
            amount = self.context["budget"].get_value_of(instance)
            children = None
        else:
            amount = sum((c["amount"] for c in children))
        return dict(super().to_representation(instance), amount=amount, children=children)


class WdmmgSerializer(serializers.ModelSerializer):
    government = GovernmentSerializer()
    budgets = serializers.SerializerMethodField()

    class Meta:
        model = models.Budget
        fields = ("id", "name", "subtitle", "slug", "year", "created_at", "updated_at", "government", "budgets")

    def get_budgets(self, obj: models.Budget):
        return [BudgetNodeSerializer(instance=c, context={"budget": obj}).data for c in obj.classification_system.roots]
