import django_filters.rest_framework as drf_filters
from django.http import FileResponse
from django_filters import rest_framework as filters
from rest_framework import viewsets
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


class ClassificationViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return models.Classification.objects.filter(classification_system=self.kwargs['classification_system_pk'])

    serializer_class = serializers.ClassificationSerializer
    pagination_class = CreatedAtPagination


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = models.Budget.objects.all()
    pagination_class = CreatedAtPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.BudgetDetailSerializer
        return serializers.BudgetSerializer


def download_xlsx_template_view(request):
    blob = models.Blob.objects.get(id="Jm3YrwfxRJaNbayG7mJNCm")
    return FileResponse(models.BlobReader(blob), as_attachment=True, filename=blob.name)
