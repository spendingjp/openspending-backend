from django.urls import include, path
from rest_framework_nested import routers

from . import views

router = routers.DefaultRouter(trailing_slash='/?')
router.register(r"governments", views.GovernmentViewSet)
router.register(r"classification-systems", views.ClassificationSystemViewSet)
router.register(r"budgets", views.BudgetViewSet)
router.register(r"wdmmg", views.WdmmgView)
router.register(r"icon-images", views.IconImageViewSet)

classification_system_router = routers.NestedDefaultRouter(
    router, r"classification-systems", lookup=r"classification_system"
)
classification_system_router.register(
    r"classifications", views.ClassificationViewSet, basename="classification-system-classification"
)
budget_router = routers.NestedDefaultRouter(router, r"budgets", lookup="budget")
budget_router.register(r"items", views.BudgetItemViewSet, basename="budget-item")

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/', include(classification_system_router.urls)),
    path('api/v1/', include(budget_router.urls)),
    path('transfer/xlsx_template', views.download_xlsx_template_view),
    path('transfer/csv/<str:budget_id>', views.download_csv_view),
    path('icons/<str:icon_slug>', views.icon_view),
]
