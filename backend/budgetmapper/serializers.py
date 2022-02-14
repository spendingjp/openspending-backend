from django.db import IntegrityError
from rest_framework import serializers, status
from rest_framework.views import Response, exception_handler

from . import models


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    print(exc)
    print(context)

    if isinstance(exc, IntegrityError) and not response:
        response = Response({"message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

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
        fields = (
            "id",
            "name",
            "slug",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        )


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


class BasicBudgetSerializer(serializers.ModelSerializer):
    government = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()

    def get_year(self, obj: models.BudgetBase):
        return obj.year

    def get_government(self, obj: models.BudgetBase):
        return obj.government.id

    class Meta:
        model = models.BasicBudget
        fields = (
            "id",
            "name",
            "slug",
            "year",
            "government",
            "subtitle",
            "classification_system",
            "created_at",
            "updated_at",
        )


class BudgetListSerializer(serializers.ModelSerializer):
    government = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()

    def get_year(self, obj: models.BudgetBase):
        return obj.year

    def get_government(self, obj: models.BudgetBase):
        return obj.government.id

    class Meta:
        model = models.BudgetBase
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

    def to_representation(self, instance: models.BudgetBase):
        if isinstance(instance, models.MappedBudget):
            return dict(
                super(BudgetListSerializer, self).to_representation(instance), source_budget=instance.source_budget.id
            )
        return super(BudgetListSerializer, self).to_representation(instance)


class BasicBudgetRetrieveSerializer(serializers.ModelSerializer):
    classification_system = ClassificationSystemSerializer()
    government = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()

    class Meta:
        model = models.BasicBudget
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

    def get_year(self, obj: models.BudgetBase):
        return obj.year

    def get_government(self, obj: models.BudgetBase):
        return GovernmentSerializer(obj.government).data


class BasicBudgetDetailSerializer(serializers.ModelSerializer):
    classification_system = ClassificationSystemSerializer()
    government = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = models.BasicBudget
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

    def get_year(self, obj: models.BudgetBase):
        return obj.year

    def get_government(self, obj: models.BudgetBase):
        return GovernmentSerializer(obj.government).data

    def get_items(self, obj):
        return BudgetItemSerializer(
            models.BudgetItemBase.objects.filter(budget=obj).prefetch_related("classification"),
            many=True,
        ).data


class BasicBudgetCreateUpdateSerializer(serializers.ModelSerializer):
    year = serializers.IntegerField()
    government = serializers.CharField()

    class Meta:
        model = models.BasicBudget
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

    def _tidy_year(self, validated_data):
        if "year" in validated_data:
            validated_data["year_value"] = validated_data["year"]
            del validated_data["year"]

    def _tidy_government(self, validated_data):
        if "government" in validated_data:
            validated_data["government_value"] = models.Government.objects.get(pk=validated_data["government"])
            del validated_data["government"]

    def create(self, validated_data):
        self._tidy_year(validated_data)
        self._tidy_government(validated_data)
        return super(BasicBudgetCreateUpdateSerializer, self).create(validated_data)

    def to_representation(self, instance):
        return dict(
            super(BasicBudgetCreateUpdateSerializer, self).to_representation(instance),
            government=instance.government.id,
        )


class MappedBudgetSerializer(serializers.ModelSerializer):
    government = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()

    def get_year(self, obj: models.BudgetBase):
        return obj.year

    def get_government(self, obj: models.BudgetBase):
        return obj.government.id

    class Meta:
        model = models.MappedBudget
        fields = (
            "id",
            "name",
            "slug",
            "year",
            "government",
            "subtitle",
            "classification_system",
            "source_budget",
            "created_at",
            "updated_at",
        )


class MappedBudgetRetrieveSerializer(serializers.ModelSerializer):
    classification_system = ClassificationSystemSerializer()
    government = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    source_budget = BasicBudgetRetrieveSerializer()

    def get_year(self, obj: models.BudgetBase):
        return obj.year

    def get_government(self, obj: models.BudgetBase):
        return GovernmentSerializer(obj.government).data

    class Meta:
        model = models.MappedBudget
        fields = (
            "id",
            "name",
            "slug",
            "year",
            "government",
            "subtitle",
            "classification_system",
            "source_budget",
            "created_at",
            "updated_at",
        )


class AtomicBudgetItemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AtomicBudgetItem
        fields = ("id", "budget", "classification", "value", "created_at", "updated_at")


class AtomicBudgetItemRetrieveSerializer(serializers.ModelSerializer):
    budget = BasicBudgetSerializer()
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
            "source_classifications",
            "created_at",
            "updated_at",
        )


class MappedBudgetItemRetrieveSerializer(serializers.ModelSerializer):
    classification = ClassificationSerializer()
    source_classifications = ClassificationSerializer(many=True)
    budget = MappedBudgetSerializer()

    class Meta:
        model = models.MappedBudgetItem
        fields = (
            "id",
            "budget",
            "classification",
            "source_classifications",
            "created_at",
            "updated_at",
        )


class MappedBudgetItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MappedBudgetItem
        fields = (
            "id",
            "budget",
            "classification",
            "source_classifications",
            "created_at",
            "updated_at",
        )


class WdmmgNodeSerializer(serializers.ModelSerializer):
    icon_id = serializers.SerializerMethodField()
    mapped_budget_items = serializers.SerializerMethodField()

    class Meta:
        model = models.Classification
        fields = ("id", "name", "code", "icon_id", "mapped_budget_items")

    def get_icon_id(self, obj: models.Classification):
        return obj.get_icon_id()

    def get_source_classifications(self, obj: models.Classification):
        return [c.id for c in obj.get_source_classifications()]

    def get_mapped_budget_items(self, obj: models.Classification):
        return [
            {"id": item.id, "source_classifications": [cls.id for cls in item.source_classifications.all()]}
            for item in obj.mapped_budget_items
        ]

    def to_representation(self, instance):
        is_leaf = True
        children = []
        for c in instance.direct_children:
            children.append(WdmmgNodeSerializer(instance=c, context={"budget": self.context["budget"]}).data)
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
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = models.BudgetBase
        fields = (
            "id",
            "name",
            "subtitle",
            "slug",
            "year",
            "created_at",
            "updated_at",
            "total_amount",
            "government",
            "budgets",
        )

    def get_total_amount(self, obj: models.BudgetBase):
        return sum((d["amount"] for d in self.get_budgets(obj)))

    def get_budgets(self, obj: models.BudgetBase):
        res = models.WdmmgTreeCache.get_or_none(obj)
        if res is None:
            res = [
                WdmmgNodeSerializer(instance=c, context={"budget": obj}).data for c in obj.classification_system.roots
            ]
            models.WdmmgTreeCache.cache_tree(res, obj)
        return res
