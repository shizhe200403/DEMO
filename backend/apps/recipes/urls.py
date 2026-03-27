from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet

router = DefaultRouter()
router.register(r"ingredients", IngredientViewSet, basename="ingredient")
router.register(r"recipes", RecipeViewSet, basename="recipe")

urlpatterns = router.urls

