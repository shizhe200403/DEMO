"""
management command: seed_demo_data

用法：
  python manage.py seed_demo_data          # 跳过已存在的数据
  python manage.py seed_demo_data --reset  # 清空后重建（危险！只用于开发）

创建：
  - 5 个演示用户（demo01~demo05，密码 Demo@1234）
  - 20 条菜谱（含营养数据，3 条 Pro 专属）
  - 10 条社区帖子
  - 用户行为记录（点赞、浏览）—— 让推荐算法有真实数据可算
  - 2 周饮食记录历史（让首页"今日摄入"有数据）
  - 每个用户 1 个健康目标
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()

# ── 菜谱数据 ────────────────────────────────────────────────────────────────
RECIPES_DATA = [
    # title, description, meal_type, cook_time, difficulty, taste_tags, cuisine_tags,
    # energy, protein, fat, carb, is_premium
    ("番茄炒鸡蛋", "家常必备，营养均衡，10分钟搞定", "lunch", 10, "easy",
     ["light", "healthy"], ["chinese"], 210, 14, 8, 22, False),
    ("燕麦牛奶粥", "高纤低脂早餐，饱腹感强", "breakfast", 8, "easy",
     ["light", "healthy"], ["healthy_style"], 280, 12, 5, 48, False),
    ("清蒸鲈鱼", "低脂高蛋白，适合减脂期", "dinner", 25, "medium",
     ["light", "low_fat"], ["chinese"], 180, 28, 4, 2, False),
    ("鸡胸肉沙拉", "高蛋白轻食，健身必备", "lunch", 15, "easy",
     ["light", "high_protein"], ["western"], 320, 35, 8, 18, False),
    ("全麦三明治", "快手早餐，蛋白质丰富", "breakfast", 5, "easy",
     ["quick", "high_protein"], ["western"], 380, 22, 10, 48, False),
    ("红烧牛肉", "经典家常菜，铁质丰富", "dinner", 60, "hard",
     ["spicy"], ["chinese"], 520, 32, 28, 15, False),
    ("蒸蛋羹", "嫩滑低脂，老少皆宜", "breakfast", 15, "easy",
     ["light", "healthy"], ["chinese"], 150, 12, 7, 5, False),
    ("绿茶荞麦面", "低GI主食，适合控糖", "lunch", 12, "easy",
     ["light", "low_fat"], ["japanese"], 340, 12, 2, 68, False),
    ("西蓝花炒虾仁", "维C+蛋白质双补充", "dinner", 15, "easy",
     ["healthy", "high_protein"], ["chinese"], 220, 25, 6, 12, False),
    ("希腊酸奶碗", "益生菌+蛋白质，早餐首选", "breakfast", 3, "easy",
     ["light", "high_protein"], ["western"], 250, 18, 6, 30, False),
    ("五谷杂粮饭", "复合碳水，膳食纤维丰富", "lunch", 30, "easy",
     ["healthy"], ["chinese"], 350, 10, 3, 72, False),
    ("黑椒牛排", "高蛋白增肌餐", "dinner", 20, "medium",
     ["high_protein"], ["western"], 480, 42, 22, 8, False),
    ("紫薯南瓜粥", "富含β胡萝卜素，护眼抗氧化", "breakfast", 20, "easy",
     ["healthy", "light"], ["chinese"], 210, 5, 1, 45, False),
    ("凉拌黄瓜", "清爽低卡，适合夏日", "lunch", 8, "easy",
     ["light", "low_fat"], ["chinese"], 40, 2, 0, 8, False),
    ("蒜蓉蒸扇贝", "高蛋白低脂，鲜味十足", "dinner", 12, "easy",
     ["light", "high_protein"], ["chinese"], 120, 16, 3, 4, False),
    ("蓝莓燕麦杯", "花青素+膳食纤维，抗氧化早餐", "breakfast", 5, "easy",
     ["healthy", "high_protein"], ["western"], 290, 10, 5, 52, False),
    ("豆腐鱼头汤", "补钙健脑，低卡滋补", "dinner", 35, "medium",
     ["light", "healthy"], ["chinese"], 280, 24, 10, 8, False),
    # Pro 专属菜谱
    ("营养师定制减脂套餐", "精准控热量，蛋白优先，专属配方", "lunch", 20, "medium",
     ["high_protein", "low_fat"], ["healthy_style"], 450, 48, 10, 30, True),
    ("运动员增肌餐盘", "三阶段补充蛋白方案，搭配时机指南", "dinner", 30, "medium",
     ["high_protein"], ["western"], 680, 62, 20, 45, True),
    ("抗炎抗氧化膳食计划", "地中海饮食结合东方草本，专业配方", "lunch", 25, "medium",
     ["healthy", "light"], ["mediterranean"], 380, 22, 14, 42, True),
]

COMMUNITY_POSTS = [
    ("减脂一个月总结", "坚持低碳饮食+运动，体重下降了4kg，分享一下我的饮食记录方法…"),
    ("推荐：清蒸鲈鱼超简单做法", "之前觉得清蒸鱼很难，试了几次发现其实很简单，关键是火候…"),
    ("早餐党必看：燕麦的10种吃法", "吃了半年燕麦，总结出这些不腻的搭配，冬天加点姜丝超暖胃…"),
    ("高蛋白饮食两个月后的变化", "坚持每天蛋白质120g+，体脂下降显著，分享我的食物选择清单…"),
    ("月报：三月份营养数据复盘", "这个月能量缺口保持在每天400kcal左右，蛋白完成率90%…"),
    ("购物清单：常备食材推荐", "每周固定采购这些食材，既省钱又营养均衡，菜市场就能搞定…"),
    ("糖友饮食心得", "血糖管理两年，低GI饮食已经成为习惯，来分享一些实用小技巧…"),
    ("健身餐vs普通餐的营养对比", "用这个系统分析了一下，发现差距比想象中大，数据截图在里面…"),
    ("素食一周挑战记录", "纯素七天，蛋白质来源成最大挑战，最后靠豆腐+坚果补上了缺口…"),
    ("推荐：AI营养师真的好用！", "问了它几个问题，给的建议比我以前自己查资料靠谱多了…"),
]

HEALTH_GOALS = [
    ("weight_loss", 65, 72),
    ("muscle_gain", 75, 68),
    ("blood_sugar_control", None, None),
    ("fat_control", None, None),
    ("protein_up", 120, 80),
]

USER_CONFIGS = [
    # username, nickname, gender, height, weight, diet_type, meal_preference, activity_level
    ("demo01", "小张同学", "male", 175, 72, "balanced", "light_home", "medium"),
    ("demo02", "健身达人", "male", 180, 82, "high_protein", "high_protein_fitness", "high"),
    ("demo03", "轻食爱好者", "female", 162, 55, "low_fat", "light_home", "medium"),
    ("demo04", "糖友小王", "male", 168, 78, "low_sugar", "quick_meal", "low"),
    ("demo05", "营养研究生", "female", 165, 58, "balanced", "light_home", "medium"),
]


class Command(BaseCommand):
    help = "填充演示数据（菜谱、用户、社区帖子、行为记录）"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="先清空再重建（开发用）")

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()
        self._seed_recipes()
        users = self._seed_users()
        self._seed_community(users)
        self._seed_behaviors(users)
        self._seed_meal_records(users)
        self._seed_health_goals(users)
        self.stdout.write(self.style.SUCCESS("演示数据填充完成！"))

    # ── 清空 ─────────────────────────────────────────────────────────────
    def _reset(self):
        from apps.community.models import Post, PostComment
        from apps.recipes.models import Recipe
        from apps.tracking.models import MealRecord, UserBehavior

        self.stdout.write("清空演示数据…")
        User.objects.filter(username__startswith="demo").delete()
        Recipe.objects.filter(source_type="seed").delete()
        self.stdout.write("完成")

    # ── 菜谱 ─────────────────────────────────────────────────────────────
    def _seed_recipes(self):
        from apps.recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeNutritionSummary, RecipeStep

        admin = User.objects.filter(is_superuser=True).first()
        created = 0
        for (title, desc, meal_type, cook_time, difficulty,
             taste_tags, cuisine_tags, energy, protein, fat, carb, is_premium) in RECIPES_DATA:

            if Recipe.objects.filter(title=title).exists():
                continue

            recipe = Recipe.objects.create(
                title=title,
                description=desc,
                meal_type=meal_type,
                cook_time_minutes=cook_time,
                prep_time_minutes=max(5, cook_time // 3),
                difficulty=difficulty,
                taste_tags=taste_tags,
                cuisine_tags=cuisine_tags,
                servings=2,
                portion_size="2人份",
                status="published",
                audit_status="approved",
                source_type="seed",
                is_premium=is_premium,
                created_by=admin,
            )

            RecipeStep.objects.create(recipe=recipe, step_no=1, content=f"准备食材，处理干净备用。")
            RecipeStep.objects.create(recipe=recipe, step_no=2, content=f"按照{difficulty}难度步骤烹饪，注意火候控制。")
            RecipeStep.objects.create(recipe=recipe, step_no=3, content=f"出锅装盘，即可享用。")

            RecipeNutritionSummary.objects.create(
                recipe=recipe,
                per_serving_energy=Decimal(str(energy)),
                per_serving_protein=Decimal(str(protein)),
                per_serving_fat=Decimal(str(fat)),
                per_serving_carbohydrate=Decimal(str(carb)),
                calculation_method="seed_data",
            )

            # 简单食材
            ing_name = title.split("炒")[0] if "炒" in title else title[:2] + "食材"
            ing, _ = Ingredient.objects.get_or_create(
                canonical_name=ing_name,
                defaults={"category": meal_type, "default_unit": "克", "is_common": True},
            )
            RecipeIngredient.objects.create(recipe=recipe, ingredient=ing, amount=Decimal("200"), unit="克", is_main=True)
            created += 1

        self.stdout.write(f"  菜谱：新增 {created} 条（跳过已存在）")

    # ── 用户 ─────────────────────────────────────────────────────────────
    def _seed_users(self):
        from apps.accounts.models import UserHealthCondition, UserProfile
        from datetime import date

        users = []
        for i, (username, nickname, gender, height, weight, diet_type, meal_pref, activity) in enumerate(USER_CONFIGS):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "nickname": nickname,
                    "email": f"{username}@demo.health",
                    "is_active": True,
                    "plan": "pro" if i == 1 else "free",  # demo02 是 Pro
                },
            )
            if created:
                user.set_password("Demo@1234")
                user.save()

            # UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.gender = gender
            profile.height_cm = Decimal(str(height))
            profile.weight_kg = Decimal(str(weight))
            profile.diet_type = diet_type
            profile.meal_preference = meal_pref
            profile.activity_level = activity
            profile.birthday = date(1995 + i, 3 + i, 10 + i)
            profile.save()

            # UserHealthCondition
            hc, _ = UserHealthCondition.objects.get_or_create(user=user)
            if i == 3:  # demo04 糖友
                hc.has_diabetes = True
                hc.save()
            users.append(user)

        self.stdout.write(f"  用户：已准备 {len(users)} 个演示账号（密码 Demo@1234）")
        return users

    # ── 社区帖子 ─────────────────────────────────────────────────────────
    def _seed_community(self, users):
        from apps.community.models import Post, PostLike

        created = 0
        for i, (title, content) in enumerate(COMMUNITY_POSTS):
            author = users[i % len(users)]
            if Post.objects.filter(title=title).exists():
                continue
            post = Post.objects.create(
                user=author,
                title=title,
                content=content,
                status="published",
                audit_status="approved",
            )
            # 其他用户点赞
            for j, liker in enumerate(users):
                if liker != author and j % 2 == 0:
                    PostLike.objects.get_or_create(user=liker, post=post)
            created += 1

        self.stdout.write(f"  社区：新增 {created} 条帖子")

    # ── 用户行为（让推荐有数据）──────────────────────────────────────────
    def _seed_behaviors(self, users):
        from apps.recipes.models import Recipe, UserFavoriteRecipe
        from apps.tracking.models import UserBehavior

        recipes = list(Recipe.objects.filter(status="published", audit_status="approved"))
        if not recipes:
            return

        created = 0
        for user in users:
            # 每人随机浏览 8~12 个菜谱
            viewed = random.sample(recipes, min(10, len(recipes)))
            for recipe in viewed:
                _, c = UserBehavior.objects.get_or_create(
                    user=user, recipe=recipe, behavior_type="view",
                    defaults={"context_scene": "home", "behavior_value": Decimal("1")},
                )
                if c:
                    created += 1

            # 收藏 3~5 个
            favorites = random.sample(viewed, min(4, len(viewed)))
            for recipe in favorites:
                UserFavoriteRecipe.objects.get_or_create(user=user, recipe=recipe)
                UserBehavior.objects.get_or_create(
                    user=user, recipe=recipe, behavior_type="favorite",
                    defaults={"context_scene": "recipe"},
                )

        self.stdout.write(f"  行为记录：新增 {created} 条浏览记录")

    # ── 饮食记录（2周历史）───────────────────────────────────────────────
    def _seed_meal_records(self, users):
        from apps.recipes.models import Recipe
        from apps.tracking.models import MealRecord, MealRecordItem

        recipes = list(Recipe.objects.filter(status="published", audit_status="approved",
                                              source_type="seed").exclude(is_premium=True))
        if not recipes:
            return

        today = date.today()
        created = 0
        for user in users[:3]:  # 只为前3个用户生成记录（节省时间）
            for days_ago in range(1, 15):
                record_date = today - timedelta(days=days_ago)
                for meal_type in ["breakfast", "lunch", "dinner"]:
                    if random.random() < 0.75:  # 75% 概率当天记录该餐次
                        mr, mr_created = MealRecord.objects.get_or_create(
                            user=user, record_date=record_date, meal_type=meal_type,
                            defaults={"source_type": "seed"},
                        )
                        if mr_created:
                            recipe = random.choice(recipes)
                            ns = getattr(recipe, "nutrition_summary", None)
                            MealRecordItem.objects.create(
                                meal_record=mr,
                                recipe=recipe,
                                ingredient_name_snapshot=recipe.title,
                                amount=Decimal("1"),
                                unit="份",
                                energy=ns.per_serving_energy if ns else None,
                                protein=ns.per_serving_protein if ns else None,
                                fat=ns.per_serving_fat if ns else None,
                                carbohydrate=ns.per_serving_carbohydrate if ns else None,
                            )
                            created += 1

        self.stdout.write(f"  饮食记录：新增 {created} 条")

    # ── 健康目标 ──────────────────────────────────────────────────────────
    def _seed_health_goals(self, users):
        from apps.tracking.models import HealthGoal

        today = date.today()
        created = 0
        for i, user in enumerate(users):
            goal_type, target, current = HEALTH_GOALS[i % len(HEALTH_GOALS)]
            if HealthGoal.objects.filter(user=user, goal_type=goal_type).exists():
                continue
            HealthGoal.objects.create(
                user=user,
                goal_type=goal_type,
                target_value=Decimal(str(target)) if target else None,
                current_value=Decimal(str(current)) if current else None,
                start_date=today - timedelta(days=30),
                target_date=today + timedelta(days=60),
                status="active",
                description=f"演示目标 - {goal_type}",
            )
            created += 1

        self.stdout.write(f"  健康目标：新增 {created} 条")
