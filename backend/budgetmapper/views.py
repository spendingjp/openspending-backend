import csv
from io import BytesIO, StringIO

import django_filters.rest_framework as drf_filters
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import exceptions, mixins, viewsets
from rest_framework.pagination import CursorPagination

from . import models, serializers


class CreatedAtPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at'


class UpdatedAtPagination(CursorPagination):
    page_size = 10
    ordering = '-updated_at'


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
        return models.Classification.objects.filter(classification_system=self.kwargs['classification_system_pk'])

    serializer_class = serializers.ClassificationSerializer
    pagination_class = CreatedAtPagination


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

    def destroy(self, request, budget_pk, pk=None):
        if isinstance(self.get_queryset().first(), models.MappedBudgetItem):
            return super(BudgetItemViewSet, self).destroy(request, budget_pk=budget_pk, pk=pk)
        raise exceptions.MethodNotAllowed(self.action)

    def get_serializer_class(self):
        if self.action == "create":
            if "amount" in self.request.data:
                raise exceptions.MethodNotAllowed("create")
            if "mapped_budget" in self.request.data and "mapped_classifications" in self.request.data:
                self.request.data["budget"] = self.kwargs["budget_pk"]
                return serializers.MappedBudgetItemCreateUpdateSerializer
        if isinstance(self.get_queryset().first(), models.MappedBudgetItem):
            if self.action == "retrieve":
                return serializers.MappedBudgetItemDetailSerializer
            if self.action in {"update", "partial_update"}:
                return serializers.MappedBudgetItemCreateUpdateSerializer
            return serializers.MappedBudgetItemSerializer
        if self.action in {"update", "partial_update"}:
            raise exceptions.MethodNotAllowed(self.action)
        return serializers.BudgetItemSerializer

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
            + [d["budget_item"].value if d["budget_item"] is not None else 0]
        )

    return FileResponse(BytesIO(buf.getvalue().encode("utf-8")), as_attachment=True, filename=f"{budget.slug}.csv")
