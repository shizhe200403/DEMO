from django.urls import path

from .views import ExplainRecommendationView, HomeRecommendationView, ProfileRecommendationView

urlpatterns = [
    path("recommendations/home/", HomeRecommendationView.as_view(), name="recommendations-home"),
    path("recommendations/by-profile/", ProfileRecommendationView.as_view(), name="recommendations-by-profile"),
    path("recommendations/explain/<int:recipe_id>/", ExplainRecommendationView.as_view(), name="recommendations-explain"),
]

