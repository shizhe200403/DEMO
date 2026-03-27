from django.db import transaction

from .models import Ingredient, Recipe, RecipeIngredient, RecipeNutritionSummary, RecipeStep


STARTER_RECIPES = [
    {
        "title": "鸡胸藜麦能量碗",
        "description": "鸡胸肉、藜麦和时蔬搭配的一碗餐，适合工作日午餐和健身后补充蛋白。",
        "meal_type": "lunch",
        "difficulty": "easy",
        "cook_time_minutes": 18,
        "prep_time_minutes": 10,
        "portion_size": "1 碗",
        "taste_tags": ["high_protein", "light", "healthy"],
        "cuisine_tags": ["轻食", "减脂"],
        "ingredients": [
            ("鸡胸肉", "protein", "200", "g", True),
            ("藜麦", "grain", "80", "g", True),
            ("西兰花", "vegetable", "120", "g", False),
            ("玉米粒", "vegetable", "60", "g", False),
        ],
        "steps": [
            "鸡胸肉切块，撒少量黑胡椒和盐，煎熟备用。",
            "藜麦煮熟后沥干，与西兰花和玉米焯熟备用。",
            "把鸡胸肉、藜麦和配菜装碗，淋少量橄榄油即可。",
        ],
        "nutrition": {"per_serving_energy": "428", "per_serving_protein": "34", "per_serving_fat": "11", "per_serving_carbohydrate": "39"},
    },
    {
        "title": "番茄牛肉意面",
        "description": "偏家常风格的高饱腹晚餐，兼顾蛋白和碳水，适合作为晚餐主食。",
        "meal_type": "dinner",
        "difficulty": "medium",
        "cook_time_minutes": 25,
        "prep_time_minutes": 12,
        "portion_size": "1 盘",
        "taste_tags": ["protein", "balanced"],
        "cuisine_tags": ["家常", "西式"],
        "ingredients": [
            ("牛里脊", "protein", "120", "g", True),
            ("意面", "grain", "90", "g", True),
            ("番茄", "vegetable", "180", "g", True),
            ("洋葱", "vegetable", "60", "g", False),
        ],
        "steps": [
            "意面煮至八分熟备用。",
            "牛肉快速翻炒变色，加入洋葱和番茄丁炒出酱汁。",
            "加入意面拌匀，小火收汁后出锅。",
        ],
        "nutrition": {"per_serving_energy": "512", "per_serving_protein": "29", "per_serving_fat": "14", "per_serving_carbohydrate": "62"},
    },
    {
        "title": "希腊酸奶水果杯",
        "description": "准备时间短，适合作为早餐或训练后的加餐，蛋白足、负担轻。",
        "meal_type": "breakfast",
        "difficulty": "easy",
        "cook_time_minutes": 8,
        "prep_time_minutes": 5,
        "portion_size": "1 杯",
        "taste_tags": ["high_protein", "quick", "light"],
        "cuisine_tags": ["早餐", "清爽"],
        "ingredients": [
            ("希腊酸奶", "dairy", "200", "g", True),
            ("蓝莓", "fruit", "50", "g", False),
            ("香蕉", "fruit", "80", "g", False),
            ("燕麦片", "grain", "25", "g", False),
        ],
        "steps": [
            "酸奶倒入杯中作为底层。",
            "加入切片香蕉、蓝莓和燕麦片。",
            "搅拌后即可食用。",
        ],
        "nutrition": {"per_serving_energy": "286", "per_serving_protein": "21", "per_serving_fat": "6", "per_serving_carbohydrate": "34"},
    },
    {
        "title": "清蒸鳕鱼西兰花",
        "description": "蛋白质稳定、整体清淡，适合晚餐或控脂阶段使用。",
        "meal_type": "dinner",
        "difficulty": "easy",
        "cook_time_minutes": 16,
        "prep_time_minutes": 8,
        "portion_size": "1 份",
        "taste_tags": ["high_protein", "light", "low_fat"],
        "cuisine_tags": ["清蒸", "家常"],
        "ingredients": [
            ("鳕鱼", "protein", "180", "g", True),
            ("西兰花", "vegetable", "150", "g", True),
            ("胡萝卜", "vegetable", "60", "g", False),
        ],
        "steps": [
            "鳕鱼洗净后放姜片去腥，上锅蒸熟。",
            "西兰花和胡萝卜焯水备用。",
            "把鱼和蔬菜装盘，淋少量蒸鱼豉油即可。",
        ],
        "nutrition": {"per_serving_energy": "248", "per_serving_protein": "32", "per_serving_fat": "6", "per_serving_carbohydrate": "14"},
    },
    {
        "title": "金枪鱼玉米沙拉",
        "description": "适合午间轻食或晚间简餐，准备快，蛋白和纤维都比较友好。",
        "meal_type": "lunch",
        "difficulty": "easy",
        "cook_time_minutes": 12,
        "prep_time_minutes": 6,
        "portion_size": "1 盘",
        "taste_tags": ["high_protein", "light", "quick"],
        "cuisine_tags": ["沙拉", "轻食"],
        "ingredients": [
            ("金枪鱼罐头", "protein", "120", "g", True),
            ("生菜", "vegetable", "120", "g", True),
            ("玉米粒", "vegetable", "80", "g", False),
            ("小番茄", "vegetable", "90", "g", False),
        ],
        "steps": [
            "生菜洗净沥干，小番茄对半切开。",
            "把金枪鱼、玉米和蔬菜放入大碗。",
            "加入少量油醋汁拌匀即可。",
        ],
        "nutrition": {"per_serving_energy": "318", "per_serving_protein": "26", "per_serving_fat": "9", "per_serving_carbohydrate": "25"},
    },
    {
        "title": "燕麦香蕉坚果杯",
        "description": "适合作为早餐或运动前补能量，准备简单，饱腹感强。",
        "meal_type": "breakfast",
        "difficulty": "easy",
        "cook_time_minutes": 10,
        "prep_time_minutes": 5,
        "portion_size": "1 杯",
        "taste_tags": ["quick", "balanced"],
        "cuisine_tags": ["早餐", "能量补给"],
        "ingredients": [
            ("燕麦片", "grain", "45", "g", True),
            ("香蕉", "fruit", "100", "g", True),
            ("牛奶", "dairy", "220", "ml", True),
            ("坚果", "fat", "15", "g", False),
        ],
        "steps": [
            "燕麦和牛奶一起加热 3 到 5 分钟。",
            "加入香蕉片和少量坚果。",
            "拌匀后即可食用。",
        ],
        "nutrition": {"per_serving_energy": "332", "per_serving_protein": "13", "per_serving_fat": "10", "per_serving_carbohydrate": "48"},
    },
]


@transaction.atomic
def ensure_builtin_recipes():
    if Recipe.objects.filter(status="published", audit_status="approved").exists():
        return

    for item in STARTER_RECIPES:
        recipe, created = Recipe.objects.get_or_create(
            title=item["title"],
            source_type="builtin",
            defaults={
                "description": item["description"],
                "portion_size": item["portion_size"],
                "servings": 1,
                "difficulty": item["difficulty"],
                "cook_time_minutes": item["cook_time_minutes"],
                "prep_time_minutes": item["prep_time_minutes"],
                "meal_type": item["meal_type"],
                "taste_tags": item["taste_tags"],
                "cuisine_tags": item["cuisine_tags"],
                "status": "published",
                "audit_status": "approved",
                "source_name": "system-starter",
            },
        )

        if not created:
            continue

        for index, step_content in enumerate(item["steps"], start=1):
            RecipeStep.objects.create(recipe=recipe, step_no=index, content=step_content)

        for ingredient_name, category, amount, unit, is_main in item["ingredients"]:
            ingredient, _ = Ingredient.objects.get_or_create(
                canonical_name=ingredient_name,
                defaults={"category": category, "default_unit": unit},
            )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount,
                unit=unit,
                is_main=is_main,
            )

        RecipeNutritionSummary.objects.update_or_create(recipe=recipe, defaults=item["nutrition"])
