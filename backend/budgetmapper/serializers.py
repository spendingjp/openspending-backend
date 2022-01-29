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


class ClassificationLevelNameListDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClassificationLevelNameList
        fields = ("id", "names", "created_at", "updated_at")


class ClassificationLevelNameListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClassificationLevelNameList
        fields = ("names",)


class ClassificationSystemSerializer(serializers.ModelSerializer):
    level_names = ClassificationLevelNameListSerializer()

    class Meta:
        model = models.ClassificationSystem
        fields = ("id", "slug", "name", "level_names", "created_at", "updated_at")


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
