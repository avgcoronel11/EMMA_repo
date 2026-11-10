"""URL routes for planes API endpoints."""

from django.urls import path

from backend.apps.planes.api.views import PlanDetailView, PlanListCreateView


app_name = "planes"

urlpatterns = [
    path("", PlanListCreateView.as_view(), name="plan-list-create"),
    path("<int:plan_id>/", PlanDetailView.as_view(), name="plan-detail"),
]
