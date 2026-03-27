from .models import RecipeNutritionSummary


def get_recipe_nutrition_summary(recipe):
    try:
        return recipe.nutrition_summary
    except RecipeNutritionSummary.DoesNotExist:
        return None

