from django.urls import path

from .views import EdamamProxyView, NutritionixProxyView, OpenFoodFactsBarcodeView, USDAProxyView

urlpatterns = [
    path("external/usda/search/", USDAProxyView.as_view(), name="external-usda-search"),
    path("external/nutritionix/search/", NutritionixProxyView.as_view(), name="external-nutritionix-search"),
    path("external/edamam/recipes/", EdamamProxyView.as_view(), name="external-edamam-recipes"),
    path("external/openfoodfacts/barcode/<str:code>/", OpenFoodFactsBarcodeView.as_view(), name="external-openfoodfacts-barcode"),
]

