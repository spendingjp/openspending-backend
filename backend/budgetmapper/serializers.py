from django.db import IntegrityError
from rest_framework import serializers, status
from rest_framework.views import Response, exception_handler

from . import models


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    print(exc)
    print(context)

    if isinstance(exc, IntegrityError) and not response:
        response = Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return response


class IconImageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IconImage
        fields = ("id", "name", "slug", "created_at", "updated_at")


class IconImageRetrieveSerializeer(serializers.ModelSerializer):
    data_uri = serializers.SerializerMethodField()

    class Meta:
        model = models.IconImage
        fields = ("id", "name", "slug", "data_uri", "created_at", "updated_at")

    def get_data_uri(self, obj: models.IconImage):
        return obj.to_data_uri()


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
        fields = ("id", "code", "name", "icon", "classification_system", "parent", "created_at", "updated_at")


class ClassificationListItemSerializer(serializers.ModelSerializer):
    classification_system = ClassificationSystemSerializer()

    class Meta:
        model = models.Classification
        fields = ("id", "code", "name", "icon", "classification_system", "parent", "created_at", "updated_at")


class ClassificationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Classification
        fields = ("id", "name", "code")


class BudgetItemSerializer(serializers.ModelSerializer):
    classification = ClassificationSummarySerializer()

    class Meta:
        model = models.BudgetItemBase
        fields = ("id", "classification", "created_at", "updated_at")


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


class BudgetRetrieveSerializer(serializers.ModelSerializer):
    classification_system = ClassificationSystemSerializer()
    government = GovernmentSerializer()

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


class AtomicBudgetItemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AtomicBudgetItem
        fields = ("id", "budget", "classification", "value", "created_at", "updated_at")


class AtomicBudgetItemRetrieveSerializer(serializers.ModelSerializer):
    budget = BudgetSerializer()
    classification = ClassificationSerializer()

    class Meta:
        model = models.AtomicBudgetItem
        fields = ("id", "budget", "classification", "value", "created_at", "updated_at")


class AtomicBudgetItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AtomicBudgetItem
        fields = ("id", "budget", "classification", "value", "created_at", "updated_at")


class MappedBudgetItemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MappedBudgetItem
        fields = (
            "id",
            "budget",
            "classification",
            "mapped_budget",
            "mapped_classifications",
            "created_at",
            "updated_at",
        )


class MappedBudgetItemRetrieveSerializer(serializers.ModelSerializer):
    classification = ClassificationSerializer()
    mapped_classifications = ClassificationSerializer(many=True)
    mapped_budget = BudgetSerializer()
    budget = BudgetSerializer()

    class Meta:
        model = models.MappedBudgetItem
        fields = (
            "id",
            "budget",
            "classification",
            "mapped_budget",
            "mapped_classifications",
            "created_at",
            "updated_at",
        )


class MappedBudgetItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MappedBudgetItem
        fields = (
            "id",
            "budget",
            "mapped_budget",
            "classification",
            "mapped_classifications",
            "created_at",
            "updated_at",
        )


class BudgetNodeSerializer(serializers.ModelSerializer):
    icon_slug = serializers.SerializerMethodField()

    class Meta:
        model = models.Classification
        fields = ("id", "name", "code", "icon_slug")

    def get_icon_slug(self, obj: models.Classification):
        return obj.icon.slug if obj.icon is not None else models.IconImage.get_default_icon().slug

    def to_representation(self, instance):
        is_leaf = True
        children = []
        for c in instance.direct_children:
            children.append(BudgetNodeSerializer(instance=c, context={"budget": self.context["budget"]}).data)
            is_leaf = False
        if is_leaf:
            amount = self.context["budget"].get_amount_of(instance)
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
        res = models.WdmmgTreeCache.get_or_none(obj)
        if res is None:
            res = [
                BudgetNodeSerializer(instance=c, context={"budget": obj}).data for c in obj.classification_system.roots
            ]
            models.WdmmgTreeCache.cache_tree(res, obj)
        return res
