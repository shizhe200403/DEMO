from django.urls import path

from .views import NutritionAnalysisView, RecipeNutritionCalculateView

urlpatterns = [
    path("nutrition/calculate/", RecipeNutritionCalculateView.as_view(), name="nutrition-calculate"),
    path("nutrition/analysis/", NutritionAnalysisView.as_view(), name="nutrition-analysis"),
]

