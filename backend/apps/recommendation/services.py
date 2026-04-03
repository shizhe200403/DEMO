"""
混合推荐引擎 — hybrid_v1

算法组成（满分 10.0）：
  1. 协同过滤（CF）  权重 40%：基于用户行为矩阵的 User-User 余弦相似度
  2. 内容推荐（CB）  权重 30%：菜谱标签特征向量与用户画像向量的余弦相似度
  3. 规则打分（Rule）权重 30%：营养目标、时间、已有数据的加权规则

冷启动策略：
  - CF 无法计算时（新用户/无行为），CF 得分降级为 0，CB + Rule 补足
  - 整体无推荐结果时，fallback 到纯规则打分（保留原有 score_recipe）
"""
from __future__ import annotations

import math
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.db.models import Count, Q

from apps.recipes.bootstrap import ensure_builtin_recipes
from apps.recipes.models import Recipe, UserFavoriteRecipe
from apps.recipes.utils import get_recipe_nutrition_summary
from apps.tracking.models import MealRecordItem, UserBehavior

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
CF_WEIGHT = 0.40
CB_WEIGHT = 0.30
RULE_WEIGHT = 0.30

# 行为权重：正向行为越重越好
BEHAVIOR_WEIGHTS: Dict[str, float] = {
    "favorite": 5.0,
    "rate": 4.0,
    "click": 2.0,
    "view": 1.0,
    "stay": 1.5,
    "share": 3.0,
    "ignore": -1.0,
}

# 内容特征维度（标签 key → 向量 index 映射，运行时动态构建）
_TAG_INDEX_CACHE: Optional[Dict[str, int]] = None


# ---------------------------------------------------------------------------
# 用户约束（过敏 / 忌口）
# ---------------------------------------------------------------------------
def _get_user_constraints(user):
    health = getattr(user, "health_condition", None)
    profile = getattr(user, "profile", None)
    allergy_tags = set(getattr(health, "allergy_tags", None) or [])
    avoid_food_tags = set(getattr(health, "avoid_food_tags", None) or [])
    meal_preference = getattr(profile, "meal_preference", "") or ""
    diet_type = getattr(profile, "diet_type", "") or ""
    return allergy_tags, avoid_food_tags, meal_preference, diet_type


def _recipe_conflicts(recipe, allergy_tags, avoid_food_tags) -> bool:
    if not allergy_tags and not avoid_food_tags:
        return False
    recipe_text = " ".join(
        [
            recipe.title or "",
            recipe.description or "",
            " ".join(recipe.taste_tags or []),
            " ".join(recipe.cuisine_tags or []),
        ]
    ).lower()
    for tag in allergy_tags | avoid_food_tags:
        if str(tag).lower() and str(tag).lower() in recipe_text:
            return True
    return False


# ---------------------------------------------------------------------------
# 1. 协同过滤（User-User Cosine Similarity）
# ---------------------------------------------------------------------------

def _build_user_recipe_matrix(all_recipes_ids: List[int]) -> Dict[int, Dict[int, float]]:
    """
    构建 user → {recipe_id: score} 稀疏矩阵。
    数据来源：UserBehavior（浏览/收藏/点击）、UserFavoriteRecipe、MealRecordItem。
    """
    matrix: Dict[int, Dict[int, float]] = defaultdict(lambda: defaultdict(float))

    # UserBehavior 行为
    for beh in UserBehavior.objects.filter(recipe_id__in=all_recipes_ids).values(
        "user_id", "recipe_id", "behavior_type"
    ):
        w = BEHAVIOR_WEIGHTS.get(beh["behavior_type"], 0.5)
        matrix[beh["user_id"]][beh["recipe_id"]] += w

    # 显式收藏
    for fav in UserFavoriteRecipe.objects.filter(recipe_id__in=all_recipes_ids).values(
        "user_id", "recipe_id"
    ):
        matrix[fav["user_id"]][fav["recipe_id"]] += BEHAVIOR_WEIGHTS["favorite"]

    # 饮食记录（曾经吃过 → 软正向）
    for item in MealRecordItem.objects.filter(recipe_id__in=all_recipes_ids).values(
        "meal_record__user_id", "recipe_id"
    ):
        matrix[item["meal_record__user_id"]][item["recipe_id"]] += 1.0

    return dict(matrix)


def _cosine_sim(vec_a: Dict[int, float], vec_b: Dict[int, float]) -> float:
    """稀疏向量余弦相似度。"""
    dot = sum(vec_a.get(k, 0.0) * v for k, v in vec_b.items())
    norm_a = math.sqrt(sum(v * v for v in vec_a.values())) or 1e-9
    norm_b = math.sqrt(sum(v * v for v in vec_b.values())) or 1e-9
    return dot / (norm_a * norm_b)


def compute_cf_scores(
    user,
    all_recipe_ids: List[int],
    matrix: Dict[int, Dict[int, float]],
    top_k_users: int = 20,
) -> Dict[int, float]:
    """
    对 user 计算协同过滤分数。
    返回 {recipe_id: cf_score}，分数已归一化到 [0, 1]。
    """
    user_vec = matrix.get(user.pk, {})
    if not user_vec:
        return {}  # 冷启动，无行为数据

    # 与其他用户计算相似度
    similarities: List[Tuple[float, int]] = []
    for other_uid, other_vec in matrix.items():
        if other_uid == user.pk:
            continue
        sim = _cosine_sim(user_vec, other_vec)
        if sim > 0.01:
            similarities.append((sim, other_uid))

    similarities.sort(reverse=True)
    top_users = similarities[:top_k_users]
    if not top_users:
        return {}

    # 加权求和：相似用户对未看过菜谱的评分
    cf_scores: Dict[int, float] = defaultdict(float)
    sim_sum: Dict[int, float] = defaultdict(float)
    seen = set(user_vec.keys())

    for sim, other_uid in top_users:
        for recipe_id, rating in matrix[other_uid].items():
            if recipe_id not in seen:  # 只推荐用户未互动过的
                cf_scores[recipe_id] += sim * rating
                sim_sum[recipe_id] += sim

    # 归一化
    raw = {rid: cf_scores[rid] / sim_sum[rid] for rid in cf_scores if sim_sum[rid] > 0}
    if not raw:
        return {}
    max_val = max(raw.values()) or 1.0
    return {rid: v / max_val for rid, v in raw.items()}


# ---------------------------------------------------------------------------
# 2. 内容推荐（Content-Based Tag Vectors）
# ---------------------------------------------------------------------------

ALL_TAGS = [
    # 菜系
    "chinese", "western", "japanese", "korean", "sichuan", "cantonese",
    # 口味
    "spicy", "light", "sweet", "sour", "salty", "healthy", "low_fat",
    # 高蛋白
    "high_protein", "protein",
    # 餐型
    "breakfast", "lunch", "dinner", "snack",
    # 烹饪
    "quick", "slow", "steamed", "fried", "grilled",
    # 场景
    "low_sugar", "low_salt", "vegetarian", "vegan",
]

_TAG_TO_IDX = {t: i for i, t in enumerate(ALL_TAGS)}
_N_TAGS = len(ALL_TAGS)


def _recipe_feature_vector(recipe) -> List[float]:
    """将菜谱转为固定维度的特征向量。"""
    vec = [0.0] * _N_TAGS
    tags = set((recipe.taste_tags or []) + (recipe.cuisine_tags or []))
    for tag in tags:
        idx = _TAG_TO_IDX.get(tag.lower())
        if idx is not None:
            vec[idx] = 1.0
    # 餐型
    if recipe.meal_type:
        idx = _TAG_TO_IDX.get(recipe.meal_type.lower())
        if idx is not None:
            vec[idx] = 1.0
    # 营养特征（阈值信号）
    summary = get_recipe_nutrition_summary(recipe)
    if summary:
        protein = float(summary.per_serving_protein or 0)
        fat = float(summary.per_serving_fat or 0)
        if protein >= 15:
            idx = _TAG_TO_IDX.get("high_protein")
            if idx is not None:
                vec[idx] = min(vec[idx] + protein / 30.0, 1.0)
        if fat <= 10:
            idx = _TAG_TO_IDX.get("low_fat")
            if idx is not None:
                vec[idx] = 1.0
    return vec


def _user_preference_vector(user) -> List[float]:
    """
    从用户画像、健康目标、历史收藏构建偏好向量。
    """
    vec = [0.0] * _N_TAGS
    profile = getattr(user, "profile", None)
    diet_type = getattr(profile, "diet_type", "") or ""
    meal_preference = getattr(profile, "meal_preference", "") or ""

    # 饮食类型映射
    diet_map = {
        "high_protein": ["high_protein", "protein"],
        "low_fat": ["low_fat", "light"],
        "low_sugar": ["low_sugar", "light"],
        "balanced": ["healthy", "light"],
        "vegetarian": ["vegetarian", "light"],
        "vegan": ["vegan", "vegetarian"],
    }
    for tag in diet_map.get(diet_type, []):
        idx = _TAG_TO_IDX.get(tag)
        if idx is not None:
            vec[idx] = 1.0

    # 餐食偏好
    pref_map = {
        "light_home": ["light", "healthy"],
        "quick_meal": ["quick"],
        "high_protein_fitness": ["high_protein", "protein"],
        "low_fat_diet": ["low_fat", "light"],
    }
    for tag in pref_map.get(meal_preference, []):
        idx = _TAG_TO_IDX.get(tag)
        if idx is not None:
            vec[idx] = min(vec[idx] + 0.8, 1.0)

    # 历史收藏的菜谱特征加权
    fav_recipe_ids = list(
        UserFavoriteRecipe.objects.filter(user=user).values_list("recipe_id", flat=True)[:50]
    )
    if fav_recipe_ids:
        fav_recipes = Recipe.objects.filter(id__in=fav_recipe_ids).select_related("nutrition_summary")
        for r in fav_recipes:
            r_vec = _recipe_feature_vector(r)
            for i, v in enumerate(r_vec):
                vec[i] += v * 0.3  # 软融合
        # 归一化
        max_v = max(vec) or 1.0
        vec = [v / max_v for v in vec]

    return vec


def _vec_cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1e-9
    norm_b = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (norm_a * norm_b)


def compute_cb_scores(user, recipes) -> Dict[int, float]:
    """
    计算内容推荐分数。返回 {recipe_id: cb_score}，已归一化到 [0, 1]。
    """
    user_vec = _user_preference_vector(user)
    if all(v == 0.0 for v in user_vec):
        return {}

    raw = {}
    for recipe in recipes:
        r_vec = _recipe_feature_vector(recipe)
        sim = _vec_cosine(user_vec, r_vec)
        if sim > 0:
            raw[recipe.id] = sim

    if not raw:
        return {}
    max_val = max(raw.values()) or 1.0
    return {rid: v / max_val for rid, v in raw.items()}


# ---------------------------------------------------------------------------
# 3. 规则打分（保留原有逻辑，归一化到 [0, 1]）
# ---------------------------------------------------------------------------
RULE_MAX = 8.0  # 规则最高分（与原 score_recipe 上限对齐）


def score_recipe(recipe, user=None):
    """原有规则打分（兼容旧接口）。"""
    score = Decimal("0")
    tags = set((recipe.taste_tags or []) + (recipe.cuisine_tags or []))

    if recipe.status != "published" or recipe.audit_status != "approved":
        return Decimal("-100")

    if user and user.is_authenticated:
        allergy, avoid, _, _ = _get_user_constraints(user)
        if _recipe_conflicts(recipe, allergy, avoid):
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

        recent_views = UserBehavior.objects.filter(
            user=user, recipe=recipe, behavior_type="view"
        ).count()
        score += Decimal(str(min(recent_views * 0.2, 1.0)))

        meal_record_count = MealRecordItem.objects.filter(
            meal_record__user=user, recipe=recipe
        ).count()
        if meal_record_count:
            score += Decimal("0.6")

        profile = getattr(user, "profile", None)
        meal_preference = getattr(profile, "meal_preference", "") or ""
        diet_type = getattr(profile, "diet_type", "") or ""
        recipe_text = " ".join(
            [recipe.title or "", " ".join(recipe.taste_tags or []), " ".join(recipe.cuisine_tags or [])]
        ).lower()
        if meal_preference and meal_preference.lower() in recipe_text:
            score += Decimal("0.4")
        if (
            diet_type == "high_protein"
            and hasattr(recipe, "nutrition_summary")
            and recipe.nutrition_summary
            and (recipe.nutrition_summary.per_serving_protein or Decimal("0")) >= Decimal("15")
        ):
            score += Decimal("0.8")
        if (
            diet_type == "low_fat"
            and hasattr(recipe, "nutrition_summary")
            and recipe.nutrition_summary
            and (recipe.nutrition_summary.per_serving_fat or Decimal("0")) <= Decimal("15")
        ):
            score += Decimal("0.8")
        if diet_type == "low_sugar" and "sugar" not in tags and "dessert" not in tags:
            score += Decimal("0.4")

    return score


def compute_rule_scores(user, recipes) -> Dict[int, float]:
    """规则打分，归一化到 [0, 1]。"""
    raw = {}
    for recipe in recipes:
        s = float(score_recipe(recipe, user))
        if s > -50:
            raw[recipe.id] = max(s, 0.0)
    if not raw:
        return {}
    max_val = max(raw.values()) or 1.0
    return {rid: v / max_val for rid, v in raw.items()}


# ---------------------------------------------------------------------------
# 推荐原因文本生成
# ---------------------------------------------------------------------------

def _build_reason(recipe, user, cf_score: float, cb_score: float, rule_score: float) -> str:
    reasons = []
    tags = set((recipe.taste_tags or []) + (recipe.cuisine_tags or []))

    # CF 信号
    if cf_score > 0.5:
        reasons.append("口味相近的用户都喜欢")
    elif cf_score > 0.2:
        reasons.append("与你相似的用户有互动")

    # CB 信号
    if cb_score > 0.7:
        reasons.append("非常符合你的饮食偏好")
    elif cb_score > 0.4:
        reasons.append("符合你的饮食偏好")

    # 营养 / 标签信号
    if "high_protein" in tags or "protein" in tags:
        reasons.append("高蛋白食材")
    if "light" in tags or "low_fat" in tags:
        reasons.append("低脂轻食")
    if recipe.meal_type == "breakfast":
        reasons.append("适合早餐")
    if recipe.cook_time_minutes and recipe.cook_time_minutes <= 20:
        reasons.append("快手菜")

    if user and user.is_authenticated:
        fav_count = UserFavoriteRecipe.objects.filter(recipe=recipe).count()
        if fav_count >= 3:
            reasons.append(f"已有 {fav_count} 人收藏")

    return "；".join(reasons) if reasons else "根据你的健康画像推荐"


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def build_recommendations(user=None, limit: int = 10) -> List[dict]:
    """
    混合推荐入口。
    优先读取预计算缓存（RecommendedRecipe），缓存不存在时实时计算。
    """
    from apps.recommendation.models import RecommendedRecipe

    # --- 读缓存 ---
    if user and user.is_authenticated:
        cached = list(
            RecommendedRecipe.objects.filter(user=user)
            .order_by("rank")[:limit]
        )
        if cached:
            recipe_ids = [c.recipe_id for c in cached]
            recipe_map = {
                r.id: r
                for r in Recipe.objects.filter(id__in=recipe_ids).select_related("nutrition_summary")
            }
            result = []
            for c in cached:
                if c.recipe_id in recipe_map:
                    result.append(
                        {
                            "recipe_id": c.recipe_id,
                            "title": recipe_map[c.recipe_id].title,
                            "score": c.score,
                            "reason_text": c.reason_text,
                        }
                    )
            if result:
                return result

    # --- 实时计算（冷启动 / 缓存未命中）---
    return _compute_hybrid(user, limit)


def _compute_hybrid(user, limit: int = 10) -> List[dict]:
    """实时混合推荐计算。"""
    ensure_builtin_recipes()

    recipes = list(
        Recipe.objects.select_related("nutrition_summary")
        .filter(status="published", audit_status="approved")
        .annotate(favorite_count=Count("favorited_by"))
    )

    if not recipes:
        return []

    # 过滤过敏/忌口
    if user and user.is_authenticated:
        allergy, avoid, _, _ = _get_user_constraints(user)
        recipes = [r for r in recipes if not _recipe_conflicts(r, allergy, avoid)]

    all_recipe_ids = [r.id for r in recipes]

    # 协同过滤
    matrix = _build_user_recipe_matrix(all_recipe_ids)
    cf_scores = compute_cf_scores(user, all_recipe_ids, matrix) if user and user.is_authenticated else {}

    # 内容推荐
    cb_scores = compute_cb_scores(user, recipes) if user and user.is_authenticated else {}

    # 规则打分
    rule_scores = compute_rule_scores(user, recipes)

    # 混合加权
    all_ids = set(all_recipe_ids)
    hybrid: Dict[int, float] = {}
    for rid in all_ids:
        cf = cf_scores.get(rid, 0.0)
        cb = cb_scores.get(rid, 0.0)
        rule = rule_scores.get(rid, 0.0)

        # 冷启动时 CF 权重转移到 Rule
        if not cf_scores:
            score = cb * (CB_WEIGHT + CF_WEIGHT / 2) + rule * (RULE_WEIGHT + CF_WEIGHT / 2)
        else:
            score = cf * CF_WEIGHT + cb * CB_WEIGHT + rule * RULE_WEIGHT

        if score > 0:
            hybrid[rid] = score

    sorted_ids = sorted(hybrid.keys(), key=lambda x: hybrid[x], reverse=True)[:limit]

    recipe_map = {r.id: r for r in recipes}
    result = []
    for rid in sorted_ids:
        recipe = recipe_map.get(rid)
        if not recipe:
            continue
        cf_s = cf_scores.get(rid, 0.0)
        cb_s = cb_scores.get(rid, 0.0)
        rule_s = rule_scores.get(rid, 0.0)
        result.append(
            {
                "recipe_id": rid,
                "title": recipe.title,
                "score": round(hybrid[rid], 4),
                "reason_text": _build_reason(recipe, user, cf_s, cb_s, rule_s),
            }
        )

    return result


def compute_and_cache_for_user(user) -> int:
    """
    为单个用户计算混合推荐并写入 RecommendedRecipe 缓存。
    返回缓存条数。
    """
    from apps.recommendation.models import RecommendedRecipe

    results = _compute_hybrid(user, limit=20)
    if not results:
        return 0

    RecommendedRecipe.objects.filter(user=user).delete()
    objs = [
        RecommendedRecipe(
            user=user,
            recipe_id=item["recipe_id"],
            rank=rank + 1,
            score=item["score"],
            reason_text=item["reason_text"],
            algo_version="hybrid_v1",
        )
        for rank, item in enumerate(results)
    ]
    RecommendedRecipe.objects.bulk_create(objs)
    return len(objs)
