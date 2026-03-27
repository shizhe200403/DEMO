from django.contrib import admin

from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeNutritionSummary,
    RecipeStep,
    UserFavoriteRecipe,
)

admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeStep)
admin.site.register(RecipeIngredient)
admin.site.register(RecipeNutritionSummary)
admin.site.register(UserFavoriteRecipe)

