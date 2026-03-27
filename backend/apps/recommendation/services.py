from decimal import Decimal

from django.db.models import Count

from apps.recipes.bootstrap import ensure_builtin_recipes
from apps.recipes.models import Recipe, UserFavoriteRecipe
from apps.recipes.utils import get_recipe_nutrition_summary
from apps.tracking.models import MealRecordItem, UserBehavior


def _get_user_constraints(user):
    health = getattr(user, "health_condition", None)
    profile = getattr(user, "profile", None)
    allergy_tags = set((getattr(health, "allergy_tags", None) or []))
    avoid_food_tags = set((getattr(health, "avoid_food_tags", None) or []))
    meal_preference = getattr(profile, "meal_preference", "") or ""
    diet_type = getattr(profile, "diet_type", "") or ""
    return allergy_tags, avoid_food_tags, meal_preference, diet_type


def _recipe_conflicts(recipe, user):
    if user is None or not user.is_authenticated:
        return False

    allergy_tags, avoid_food_tags, meal_preference, diet_type = _get_user_constraints(user)
    if not allergy_tags and not avoid_food_tags and not meal_preference and not diet_type:
        return False

    recipe_text = " ".join(
        [
            recipe.title or "",
            recipe.description or "",
            " ".join(recipe.taste_tags or []),
            " ".join(recipe.cuisine_tags or []),
            " ".join(getattr(ingredient.ingredient, "canonical_name", "") for ingredient in recipe.recipe_ingredients.all()),
            " ".join(getattr(ingredient.ingredient, "category", "") for ingredient in recipe.recipe_ingredients.all()),
        ]
    ).lower()

    for tag in allergy_tags | avoid_food_tags:
        if str(tag).lower() and str(tag).lower() in recipe_text:
            return True

    if meal_preference and meal_preference.lower() not in recipe_text and meal_preference.lower() not in {"", "all"}:
        # preference is soft, do not hard block; only lower score elsewhere
        pass

    if diet_type and diet_type.lower() in {"low_salt", "low_sugar", "high_protein", "low_fat"}:
        # handled in score adjustments
        return False

    return False


def _recipe_reason(recipe, user):
    reasons = []
    tags = set((recipe.taste_tags or []) + (recipe.cuisine_tags or []))
    if "low_fat" in tags or "low-fat" in tags:
        reasons.append("适合低脂饮食")
    if "high_protein" in tags or "protein" in tags:
        reasons.append("适合高蛋白目标")
    if recipe.meal_type == "breakfast":
        reasons.append("适合早餐场景")

    favorite_count = UserFavoriteRecipe.objects.filter(recipe=recipe).count()
    if favorite_count >= 3:
        reasons.append("社区收藏较多")

    if user.is_authenticated:
        recent_views = UserBehavior.objects.filter(user=user, recipe=recipe, behavior_type="view").count()
        if recent_views:
            reasons.append("你之前浏览过相似菜谱")

        if UserBehavior.objects.filter(user=user, recipe=recipe, behavior_type="favorite").exists():
            reasons.append("你曾收藏过相关菜谱")

    return reasons or ["根据你的画像和历史行为推荐"]


def score_recipe(recipe, user=None):
    score = Decimal("0")
    tags = set((recipe.taste_tags or []) + (recipe.cuisine_tags or []))

    if recipe.status != "published" or recipe.audit_status != "approved":
        return Decimal("-100")

    if _recipe_conflicts(recipe, user):
        return Decimal("-100")

    if recipe.meal_type == "breakfast":
        score += Decimal("1.5")
    if "light" in tags or "healthy" in tags:
        score += Decimal("1.2")
    if "high_protein" in tags or "protein" in tags:
        score += Decimal("1.0")
    if recipe.cook_time_minutes is not None and recipe.cook_time_minutes <= 20:
        score += Decimal("0.8")
    summary = get_recipe_nutrition_summary(recipe)
    if summary:
        protein = summary.per_serving_protein or Decimal("0")
        fat = summary.per_serving_fat or Decimal("0")
        if protein >= Decimal("15"):
            score += Decimal("1.0")
        if fat <= Decimal("15"):
            score += Decimal("0.5")

    if user and user.is_authenticated:
        if UserFavoriteRecipe.objects.filter(user=user, recipe=recipe).exists():
            score += Decimal("2.0")

        recent_views = UserBehavior.objects.filter(user=user, recipe=recipe, behavior_type="view").count()
        score += Decimal(str(min(recent_views * 0.2, 1.0)))

        meal_record_count = MealRecordItem.objects.filter(meal_record__user=user, recipe=recipe).count()
        if meal_record_count:
            score += Decimal("0.6")

        profile = getattr(user, "profile", None)
        meal_preference = getattr(profile, "meal_preference", "") or ""
        diet_type = getattr(profile, "diet_type", "") or ""
        recipe_text = " ".join([recipe.title or "", " ".join(recipe.taste_tags or []), " ".join(recipe.cuisine_tags or [])]).lower()
        if meal_preference and meal_preference.lower() in recipe_text:
            score += Decimal("0.4")
        if diet_type == "high_protein" and recipe.nutrition_summary and (recipe.nutrition_summary.per_serving_protein or Decimal("0")) >= Decimal("15"):
            score += Decimal("0.8")
        if diet_type == "low_fat" and recipe.nutrition_summary and (recipe.nutrition_summary.per_serving_fat or Decimal("0")) <= Decimal("15"):
            score += Decimal("0.8")
        if diet_type == "low_sugar" and "sugar" not in tags and "dessert" not in tags:
            score += Decimal("0.4")

    return score


def build_recommendations(user=None, limit=10):
    ensure_builtin_recipes()
    recipes = (
        Recipe.objects.select_related("nutrition_summary")
        .filter(status="published", audit_status="approved")
        .annotate(favorite_count=Count("favorited_by"))
        .order_by("-created_at")
    )

    scored = []
    for recipe in recipes:
        score = score_recipe(recipe, user=user)
        if score > Decimal("-50"):
            scored.append((score, recipe))

    scored.sort(key=lambda item: item[0], reverse=True)
    result = []
    for score, recipe in scored[:limit]:
        reasons = _recipe_reason(recipe, user)
        result.append(
            {
                "recipe_id": recipe.id,
                "title": recipe.title,
                "score": float(score),
                "reason_text": "；".join(reasons),
            }
        )
    return result
