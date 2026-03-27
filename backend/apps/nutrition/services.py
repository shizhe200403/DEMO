from decimal import Decimal
from datetime import date

from apps.accounts.models import User
from apps.recipes.models import Recipe
from apps.recipes.utils import get_recipe_nutrition_summary


def calculate_recipe_nutrition(recipe: Recipe, portion_multiplier: Decimal = Decimal("1")):
    summary = get_recipe_nutrition_summary(recipe)
    if summary is None:
        return {
            "energy": Decimal("0"),
            "protein": Decimal("0"),
            "fat": Decimal("0"),
            "carbohydrate": Decimal("0"),
        }

    multiplier = Decimal(str(portion_multiplier))
    return {
        "energy": (summary.per_serving_energy or Decimal("0")) * multiplier,
        "protein": (summary.per_serving_protein or Decimal("0")) * multiplier,
        "fat": (summary.per_serving_fat or Decimal("0")) * multiplier,
        "carbohydrate": (summary.per_serving_carbohydrate or Decimal("0")) * multiplier,
    }


def analyze_user_nutrition(user: User):
    profile = getattr(user, "profile", None)
    health = getattr(user, "health_condition", None)

    height = getattr(profile, "height_cm", None) or Decimal("0")
    weight = getattr(profile, "weight_kg", None) or Decimal("0")
    bmi = None
    if height and weight:
        bmi = weight / ((height / Decimal("100")) ** 2)

    goal_hint = "保持均衡饮食"
    if health:
        if getattr(health, "has_diabetes", False):
            goal_hint = "优先控制碳水与添加糖摄入"
        elif getattr(health, "has_hypertension", False):
            goal_hint = "优先控制钠摄入"
        elif getattr(health, "has_hyperlipidemia", False):
            goal_hint = "优先控制脂肪摄入"

    gender = getattr(profile, "gender", "") or ""
    birthday = getattr(profile, "birthday", None)
    activity_level = getattr(profile, "activity_level", "") or "medium"

    age = None
    if birthday:
        today = date.today()
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

    def _activity_factor(level: str) -> Decimal:
        mapping = {
            "low": Decimal("1.2"),
            "medium": Decimal("1.45"),
            "high": Decimal("1.7"),
            "very_high": Decimal("1.9"),
        }
        return mapping.get(level, Decimal("1.45"))

    calorie_target = None
    protein_target = None

    if age and height and weight:
        if gender.lower() in {"male", "m", "男"}:
            bmr = Decimal("10") * weight + Decimal("6.25") * height - Decimal("5") * Decimal(age) + Decimal("5")
        else:
            bmr = Decimal("10") * weight + Decimal("6.25") * height - Decimal("5") * Decimal(age) - Decimal("161")
        calorie_target = (bmr * _activity_factor(activity_level)).quantize(Decimal("1"))
    elif weight:
        fallback_mapping = {
            "low": Decimal("28"),
            "medium": Decimal("32"),
            "high": Decimal("36"),
            "very_high": Decimal("40"),
        }
        calorie_target = (weight * fallback_mapping.get(activity_level, Decimal("32"))).quantize(Decimal("1"))

    if weight:
        base_protein = Decimal("1.2") * weight
        if health and getattr(health, "has_diabetes", False):
            base_protein = Decimal("1.4") * weight
        elif health and getattr(health, "has_hyperlipidemia", False):
            base_protein = Decimal("1.3") * weight
        protein_target = base_protein.quantize(Decimal("0.1"))

    return {
        "bmi": bmi,
        "goal_hint": goal_hint,
        "calorie_target": calorie_target,
        "protein_target": protein_target,
    }
