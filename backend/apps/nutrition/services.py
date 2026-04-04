from decimal import Decimal
from datetime import date, timedelta

from django.utils import timezone

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
    def _mul(field):
        val = getattr(summary, field, None)
        return (val or Decimal("0")) * multiplier

    return {
        "energy": _mul("per_serving_energy"),
        "protein": _mul("per_serving_protein"),
        "fat": _mul("per_serving_fat"),
        "carbohydrate": _mul("per_serving_carbohydrate"),
        "fiber": _mul("per_serving_fiber"),
        "sodium": _mul("per_serving_sodium"),
        "calcium": _mul("per_serving_calcium"),
        "iron": _mul("per_serving_iron"),
        "vitamin_a": _mul("per_serving_vitamin_a"),
        "vitamin_c": _mul("per_serving_vitamin_c"),
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

    # 宏量目标（基于热量目标，参照中国居民膳食指南比例）
    fat_target = None
    carb_target = None
    if calorie_target:
        # 脂肪占热量 25-30%，取 27%；脂肪 9 kcal/g
        fat_ratio = Decimal("0.30") if (health and getattr(health, "has_hyperlipidemia", False)) else Decimal("0.27")
        fat_target = (calorie_target * fat_ratio / Decimal("9")).quantize(Decimal("0.1"))
        # 碳水占热量 50-65%，取 55%；碳水 4 kcal/g
        carb_ratio = Decimal("0.45") if (health and getattr(health, "has_diabetes", False)) else Decimal("0.55")
        carb_target = (calorie_target * carb_ratio / Decimal("4")).quantize(Decimal("0.1"))

    # 膳食纤维目标：中国 DRIs 推荐 25 g/天（糖尿病 30 g）
    fiber_target = Decimal("30") if (health and getattr(health, "has_diabetes", False)) else Decimal("25")
    # 钠限量：中国 DRIs 2000 mg/天；高血压 1500 mg/天
    sodium_limit = Decimal("1500") if (health and getattr(health, "has_hypertension", False)) else Decimal("2000")
    # 钙目标：DRIs 成人 800 mg/天（孕期 1000 mg）
    is_pregnant = health and getattr(health, "is_pregnant", False)
    calcium_target = Decimal("1000") if is_pregnant else Decimal("800")
    # 铁目标：DRIs 男 12 mg，女 20 mg（孕期 29 mg）
    is_male = gender.lower() in {"male", "m", "男"}
    if is_pregnant:
        iron_target = Decimal("29")
    elif is_male:
        iron_target = Decimal("12")
    else:
        iron_target = Decimal("20")
    # 维生素 A：DRIs 男 800 μgRAE，女 700 μgRAE
    vitamin_a_target = Decimal("800") if is_male else Decimal("700")
    # 维生素 C：DRIs 成人 100 mg/天
    vitamin_c_target = Decimal("100")

    # 近 7 天实际平均摄入与充足率
    adequacy = {}
    try:
        from apps.tracking.models import MealRecordItem
        today_date = timezone.localdate()
        seven_days_ago = today_date - timedelta(days=6)
        from django.db.models import Avg
        agg = MealRecordItem.objects.filter(
            meal_record__user=user,
            meal_record__record_date__range=(seven_days_ago, today_date),
        ).aggregate(
            avg_energy=Avg("energy"),
            avg_protein=Avg("protein"),
            avg_fat=Avg("fat"),
            avg_carbohydrate=Avg("carbohydrate"),
        )
        # 按天聚合更准确，但 Avg 已足够反映趋势
        from django.db.models import Sum, F
        daily = (
            MealRecordItem.objects.filter(
                meal_record__user=user,
                meal_record__record_date__range=(seven_days_ago, today_date),
            )
            .values(day=F("meal_record__record_date"))
            .annotate(
                day_energy=Sum("energy"),
                day_protein=Sum("protein"),
                day_fat=Sum("fat"),
                day_carb=Sum("carbohydrate"),
            )
        )
        if daily:
            n = Decimal(len(daily))
            avg_energy = sum(r["day_energy"] or Decimal("0") for r in daily) / n
            avg_protein = sum(r["day_protein"] or Decimal("0") for r in daily) / n
            avg_fat = sum(r["day_fat"] or Decimal("0") for r in daily) / n
            avg_carb = sum(r["day_carb"] or Decimal("0") for r in daily) / n

            def _rate(actual, target):
                if not target:
                    return None
                r = (actual / target * Decimal("100")).quantize(Decimal("0.1"))
                return float(min(r, Decimal("999.9")))

            adequacy = {
                "days_recorded": len(daily),
                "avg_energy": float(avg_energy.quantize(Decimal("0.1"))),
                "avg_protein": float(avg_protein.quantize(Decimal("0.1"))),
                "avg_fat": float(avg_fat.quantize(Decimal("0.1"))),
                "avg_carb": float(avg_carb.quantize(Decimal("0.1"))),
                "energy_rate": _rate(avg_energy, calorie_target),
                "protein_rate": _rate(avg_protein, protein_target),
                "fat_rate": _rate(avg_fat, fat_target),
                "carb_rate": _rate(avg_carb, carb_target),
            }
    except Exception:
        adequacy = {}

    # 膳食均衡指数（0-100）：取热量/蛋白质/脂肪/碳水四项充足率，
    # 每项满分25，超过目标1.2倍扣分（过量也不均衡）
    balance_score = None
    if adequacy and calorie_target:
        score = Decimal("0")
        for rate_key in ("energy_rate", "protein_rate", "fat_rate", "carb_rate"):
            rate = adequacy.get(rate_key)
            if rate is None:
                score += Decimal("12.5")  # 数据缺失给半分
                continue
            r = Decimal(str(rate))
            if r >= Decimal("80") and r <= Decimal("120"):
                score += Decimal("25")
            elif r >= Decimal("60") and r < Decimal("80"):
                score += Decimal("15")
            elif r > Decimal("120") and r <= Decimal("150"):
                score += Decimal("15")
            elif r >= Decimal("40") and r < Decimal("60"):
                score += Decimal("8")
            elif r > Decimal("150"):
                score += Decimal("5")
            else:
                score += Decimal("0")
        balance_score = int(score)

    return {
        "bmi": bmi,
        "goal_hint": goal_hint,
        "calorie_target": calorie_target,
        "protein_target": protein_target,
        "fat_target": fat_target,
        "carb_target": carb_target,
        "fiber_target": fiber_target,
        "sodium_limit": sodium_limit,
        "calcium_target": calcium_target,
        "iron_target": iron_target,
        "vitamin_a_target": vitamin_a_target,
        "vitamin_c_target": vitamin_c_target,
        "adequacy": adequacy,
        "balance_score": balance_score,
    }
