import csv
from io import BytesIO, StringIO

from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.pagination import CursorPagination

from . import models, serializers


class CreatedAtPagination(CursorPagination):
    page_size = 10
    ordering = "-created_at"


class UpdatedAtPagination(CursorPagination):
    page_size = 10
    ordering = "-updated_at"


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


class ClassificationSystemViewSet(viewsets.ModelViewSet):
    queryset = models.ClassificationSystem.objects.all()
    serializer_class = serializers.ClassificationSystemSerializer
    pagination_class = CreatedAtPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.ClassificationSystemDetailSerializer
        return serializers.ClassificationSystemSerializer


class ClassificationViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return models.Classification.objects.filter(classification_system=self.kwargs["classification_system_pk"])

    pagination_class = CreatedAtPagination

    def get_serializer_class(self):
        if self.action == "list" or self.action == "retrieve":
            return serializers.ClassificationListItemSerializer
        return serializers.ClassificationSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = models.Budget.objects.all()
    pagination_class = CreatedAtPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ("government", "year")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.BudgetDetailSerializer
        return serializers.BudgetSerializer


class BudgetItemViewSet(viewsets.ModelViewSet):
    pagination_class = CreatedAtPagination

    def get_serializer_class(self):
        if self.action == "create":
            self.request.data["budget"] = self.kwargs["budget_pk"]
            if "mapped_budget" in self.request.data and "mapped_classifications" in self.request.data:
                return serializers.MappedBudgetItemCreateUpdateSerializer
            return serializers.AtomicBudgetItemCreateUpdateSerializer
        if isinstance(self.get_queryset().first(), models.MappedBudgetItem):
            if self.action == "retrieve":
                return serializers.MappedBudgetItemRetrieveSerializer
            if self.action in {"update", "partial_update"}:
                return serializers.MappedBudgetItemCreateUpdateSerializer
            return serializers.MappedBudgetItemListSerializer
        if self.action == "retrieve":
            return serializers.AtomicBudgetItemRetrieveSerializer
        if self.action in {"update", "partial_update"}:
            return serializers.AtomicBudgetItemCreateUpdateSerializer
        return serializers.AtomicBudgetItemListSerializer

    def get_queryset(self):
        return models.BudgetItemBase.objects.filter(budget=self.kwargs["budget_pk"])


class WdmmgView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = models.Budget.objects.all()
    pagination_class = CreatedAtPagination
    serializer_class = serializers.WdmmgSerializer
    lookup_field = "slug"


def download_xlsx_template_view(request):
    blob = models.Blob.objects.get(id="Jm3YrwfxRJaNbayG7mJNCm")
    return FileResponse(models.BlobReader(blob), as_attachment=True, filename=blob.name)


def download_csv_view(request, budget_id):
    budget = get_object_or_404(models.Budget, pk=budget_id)
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
        pass

    if icon is None:
        icon = get_object_or_404(models.IconImage, id=icon_slug_or_id)

    return HttpResponse(icon.body, content_type=f"image/{icon.image_type}")
