from django.urls import include, path
from rest_framework_nested import routers

from . import views

router = routers.DefaultRouter(trailing_slash='/?')
router.register(r"governments", views.GovernmentViewSet)
router.register(r"classifiaction-systems", views.ClassificationSystemViewSet)
router.register(r"budgets", views.BudgetViewSet)

classification_system_router = routers.NestedDefaultRouter(
    router, r"classifiaction-systems", lookup=r"classification_system"
)
classification_system_router.register(
    r"classifications", views.ClassificationViewSet, basename="classification-system-classification"
)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/', include(classification_system_router.urls)),
    path('transfer/xlsx_template', views.download_xlsx_template_view),
]
