import csv
import operator
from functools import reduce
from io import BytesIO, StringIO

from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, viewsets
from rest_framework.pagination import CursorPagination

from . import models, serializers


class ItemOrderPagination(CursorPagination):
    page_size = 10
    ordering = "item_order"


class CreatedAtPagination(CursorPagination):
    page_size = 10
    ordering = "-created_at"


class UpdatedAtPagination(CursorPagination):
    page_size = 10
    ordering = "-updated_at"


class MultipleFieldLookupMixin(object):
    # refs: https://stackoverflow.com/a/38462137
    def get_object(self):
        queryset = self.get_queryset()  # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {}
        for field in self.lookup_fields:
            filter[field] = self.kwargs[self.param_field_name_in_path]
        q = reduce(operator.or_, (Q(x) for x in filter.items()))
        return get_object_or_404(queryset, q)


class IconImageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.IconImage.objects.all()
    pagination_class = CreatedAtPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.IconImageRetrieveSerializeer
        return serializers.IconImageListSerializer


class GovernmentViewSet(viewsets.ModelViewSet):
    queryset = models.Government.objects.all()
    serializer_class = serializers.GovernmentSerializer
    pagination_class = CreatedAtPagination


class ClassificationSystemViewSet(MultipleFieldLookupMixin, viewsets.ModelViewSet):
    queryset = models.ClassificationSystem.objects.all()
    serializer_class = serializers.ClassificationSystemSerializer
    pagination_class = CreatedAtPagination
    lookup_fields = ("pk", "slug")
    param_field_name_in_path = "pk"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.ClassificationSystemDetailSerializer
        return serializers.ClassificationSystemSerializer


class MappedgBudgetCandidateView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.ClassificationSystemSerializer
    pagination_class = CreatedAtPagination

    def get_queryset(self):
        budget = get_object_or_404(models.BasicBudget.objects, pk=self.kwargs["budget_pk"])
        return models.ClassificationSystem.objects.exclude(
            pk__in=models.BasicBudget.objects.filter(
                government_value=budget.government_value, year_value=budget.year_value
            ).values("classification_system")
        )


class ClassificationViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return models.Classification.objects.filter(classification_system=self.kwargs["classification_system_pk"])

    pagination_class = ItemOrderPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.ClassificationListItemSerializer
        return serializers.ClassificationSerializer


class BudgetFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if "sourceBudget" in request.query_params:
            return queryset.filter(
                Q(
                    pk__in=models.MappedBudget.objects.filter(
                        **dict(
                            {}
                            if "classificationSystem" not in request.query_params
                            else {"classification_system": request.query_params["classificationSystem"]},
                            source_budget=request.query_params.get("sourceBudget"),
                        )
                    ).values("id")
                )
            )
        basic_qs = models.BasicBudget.objects
        if "government" in request.query_params:
            basic_qs = basic_qs.filter(government_value_id=request.query_params["government"])
        if "year" in request.query_params:
            try:
                basic_qs = basic_qs.filter(year_value=int(request.query_params["year"]))
            except ValueError:
                return queryset.filter(pk=None)
        ids = list(d["id"] for d in basic_qs.values("id"))
        ids += list(d["id"] for d in models.MappedBudget.objects.filter(source_budget__in=ids).values("id"))
        return queryset.filter(Q(pk__in=ids))


class BudgetViewSet(MultipleFieldLookupMixin, viewsets.ModelViewSet):
    queryset = models.BudgetBase.objects.all()
    pagination_class = CreatedAtPagination
    filter_backends = [BudgetFilter]
    lookup_fields = ("pk", "slug")
    param_field_name_in_path = "pk"

    def get_serializer_class(self):
        if "pk" not in self.kwargs and "slug" not in self.kwargs:
            if self.action == "create":
                if "source_budget" in self.request.data:
                    return serializers.MappedBudgetSerializer
                return serializers.BasicBudgetCreateUpdateSerializer
            return serializers.BudgetListSerializer
        bud = self.get_object()
        if isinstance(bud, models.BasicBudget):
            if self.action == "retrieve":
                return serializers.BasicBudgetRetrieveSerializer
            return serializers.BasicBudgetSerializer
        if self.action == "retrieve":
            return serializers.MappedBudgetRetrieveSerializer
        return serializers.MappedBudgetSerializer


class BudgetItemViewSet(viewsets.ModelViewSet):
    pagination_class = CreatedAtPagination

    def get_serializer_class(self):
        bud = get_object_or_404(models.BudgetBase.objects, pk=self.kwargs["budget_pk"])
        if isinstance(bud, models.BasicBudget):
            if self.action == "retrieve":
                return serializers.AtomicBudgetItemRetrieveSerializer
            if self.action in {"create", "update", "partial_update"}:
                self.request.data["budget"] = self.kwargs["budget_pk"]
                return serializers.AtomicBudgetItemCreateUpdateSerializer
            return serializers.AtomicBudgetItemListSerializer
        else:
            if self.action == "retrieve":
                return serializers.MappedBudgetItemRetrieveSerializer
            if self.action in {"create", "update", "partial_update"}:
                self.request.data["budget"] = self.kwargs["budget_pk"]
                return serializers.MappedBudgetItemCreateUpdateSerializer
            return serializers.MappedBudgetItemListSerializer

    def get_queryset(self):
        return models.BudgetItemBase.objects.filter(budget=self.kwargs["budget_pk"])


class WdmmgView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = models.BudgetBase.objects.all()
    pagination_class = CreatedAtPagination
    serializer_class = serializers.WdmmgSerializer
    lookup_field = "slug"


def download_xlsx_template_view(request):
    blob = models.Blob.objects.get(id="Jm3YrwfxRJaNbayG7mJNCm")
    return FileResponse(models.BlobReader(blob), as_attachment=True, filename=blob.name)


def download_csv_view(request, budget_id):
    budget = get_object_or_404(models.BudgetBase, pk=budget_id)
    level_names = (
        budget.classification_system.level_names if budget.classification_system.level_names is not None else []
    )
    data = list(budget.iterate_items())
    max_level = max(len(d["classifications"]) for d in data)
    level_names += list(f"level_{i}" for i in range(len(level_names), max_level, 1))
    buf = StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(sum(([ln, f"{ln}名称"] for ln in level_names), []) + ["金額"])
    for d in data:
        writer.writerow(
            sum(([c.code, c.name] for c in d["classifications"]), [])
            + [["", ""] for i in range(len(d["classifications"]), max_level, 1)]
            + [d["budget_item"].amount if d["budget_item"] is not None else 0]
        )

    return FileResponse(BytesIO(buf.getvalue().encode("utf-8")), as_attachment=True, filename=f"{budget.slug}.csv")


def icon_view(request, icon_slug_or_id):
    icon = None
    try:
        icon = models.IconImage.objects.get(slug=icon_slug_or_id)
    except models.IconImage.DoesNotExist:
        icon = get_object_or_404(models.IconImage, id=icon_slug_or_id)

    return HttpResponse(icon.body, content_type=f"image/{icon.image_type}")
