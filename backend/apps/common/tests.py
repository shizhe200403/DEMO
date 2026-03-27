import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.accounts.models import UserHealthCondition, UserProfile
from apps.community.models import ContentReport, Post, PostComment
from apps.recipes.models import Ingredient, Recipe, RecipeNutritionSummary, RecipeStep, UserFavoriteRecipe
from apps.reports.models import ReportTask
from apps.tracking.models import HealthGoal, HealthGoalProgress, MealRecord, MealRecordItem, UserBehavior


User = get_user_model()


class ProductApiSmokeTests(APITestCase):
    def _create_user(self, username="alice", email="alice@example.com", phone="13800000000", password="Password123!"):
        user = User.objects.create_user(username=username, email=email, phone=phone, password=password)
        UserProfile.objects.create(user=user)
        UserHealthCondition.objects.create(user=user)
        return user

    def _login(self, account, password="Password123!"):
        response = self.client.post("/api/v1/accounts/login/", {"account": account, "password": password}, format="json")
        self.assertEqual(response.status_code, 200)
        token = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return response

    def _create_recipe_bundle(self, user, title="Steamed Egg"):
        ingredient = Ingredient.objects.create(canonical_name="egg", category="protein", default_unit="pcs")
        recipe = Recipe.objects.create(
            title=title,
            description="Simple and high protein breakfast",
            portion_size="1 serving",
            servings=1,
            difficulty="easy",
            cook_time_minutes=10,
            prep_time_minutes=5,
            meal_type="breakfast",
            taste_tags=["light"],
            cuisine_tags=["home-style"],
            status="published",
            source_type="local",
            audit_status="approved",
            created_by=user,
        )
        RecipeStep.objects.create(recipe=recipe, step_no=1, content="Beat the eggs.")
        RecipeStep.objects.create(recipe=recipe, step_no=2, content="Steam for 8 minutes.")
        RecipeNutritionSummary.objects.create(
            recipe=recipe,
            per_serving_energy=120,
            per_serving_protein=18,
            per_serving_fat=6,
            per_serving_carbohydrate=4,
            per_serving_fiber=1,
            per_serving_sodium=200,
            per_serving_calcium=50,
            per_serving_iron=1,
            per_serving_vitamin_a=1,
            per_serving_vitamin_c=1,
            calculation_method="manual",
        )
        recipe.recipe_ingredients.create(ingredient=ingredient, amount=2, unit="pcs", is_main=True)
        return recipe

    def test_register_login_and_profile_update(self):
        register_response = self.client.post(
            "/api/v1/accounts/register/",
            {
                "username": "bob",
                "email": "bob@example.com",
                "phone": "13800000001",
                "password": "Password123!",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, 200)
        self.assertTrue(UserProfile.objects.filter(user__username="bob").exists())
        self.assertTrue(UserHealthCondition.objects.filter(user__username="bob").exists())

        login_response = self.client.post(
            "/api/v1/accounts/login/",
            {"account": "bob@example.com", "password": "Password123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        phone_login_response = self.client.post(
            "/api/v1/accounts/login/",
            {"account": "13800000001", "password": "Password123!"},
            format="json",
        )
        self.assertEqual(phone_login_response.status_code, 200)

        profile_response = self.client.put(
            "/api/v1/accounts/me/full-profile/",
            {
                "account": {"nickname": "Bobby"},
                "profile": {"height_cm": 175, "weight_kg": 68, "diet_type": "high_protein"},
                "health_condition": {"has_diabetes": True, "allergy_tags": ["peanut"], "notes": "test"},
            },
            format="json",
        )
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data["data"]["account"]["nickname"], "Bobby")
        self.assertTrue(profile_response.data["data"]["health_condition"]["has_diabetes"])

        nutrition_response = self.client.get("/api/v1/nutrition/analysis/")
        self.assertEqual(nutrition_response.status_code, 200)
        self.assertIsNotNone(nutrition_response.data["data"]["calorie_target"])
        self.assertIsNotNone(nutrition_response.data["data"]["protein_target"])

    def test_recipe_recommendation_and_favorite_flow(self):
        user = self._create_user()
        self._login("alice")
        recipe = self._create_recipe_bundle(user)

        recommendation_response = self.client.get("/api/v1/recommendations/home/")
        self.assertEqual(recommendation_response.status_code, 200)
        recommended_ids = [item["recipe_id"] for item in recommendation_response.data["data"]]
        self.assertIn(recipe.id, recommended_ids)

        explain_response = self.client.get(f"/api/v1/recommendations/explain/{recipe.id}/")
        self.assertEqual(explain_response.status_code, 200)
        self.assertIn("reason_text", explain_response.data["data"])

        nutrition_response = self.client.get(f"/api/v1/recipes/{recipe.id}/nutrition/")
        self.assertEqual(nutrition_response.status_code, 200)
        self.assertEqual(nutrition_response.data["data"]["per_serving_protein"], "18.0000")

        favorite_response = self.client.post(f"/api/v1/recipes/{recipe.id}/favorite/")
        self.assertEqual(favorite_response.status_code, 200)
        self.assertTrue(UserFavoriteRecipe.objects.filter(user__username="alice", recipe=recipe).exists())
        self.assertTrue(UserBehavior.objects.filter(user__username="alice", recipe=recipe, behavior_type="favorite").exists())

    def test_meal_record_statistics_and_report_generation(self):
        user = self._create_user()
        self._login("alice")
        recipe = self._create_recipe_bundle(user, title="Protein Bowl")

        meal_response = self.client.post(
            "/api/v1/meal-records/",
            {
                "record_date": "2026-03-26",
                "meal_type": "lunch",
                "source_type": "manual",
                "note": "office lunch",
                "items": [{"recipe_id": recipe.id, "amount": 1, "unit": "serving"}],
            },
            format="json",
        )
        self.assertEqual(meal_response.status_code, 201)
        self.assertEqual(MealRecord.objects.count(), 1)
        self.assertEqual(MealRecordItem.objects.count(), 1)
        self.assertEqual(meal_response.data["data"]["items"][0]["recipe_title"], "Protein Bowl")

        stats_response = self.client.get("/api/v1/meal-records/statistics/?period=week")
        self.assertEqual(stats_response.status_code, 200)
        self.assertIsNotNone(stats_response.data["data"]["summary"])
        self.assertGreaterEqual(len(stats_response.data["data"]["trend"]), 1)

        temp_media = tempfile.mkdtemp(prefix="nutrition-tests-")
        self.addCleanup(lambda: shutil.rmtree(temp_media, ignore_errors=True))
        with override_settings(MEDIA_ROOT=temp_media):
            weekly_response = self.client.get("/api/v1/reports/weekly/")
            self.assertEqual(weekly_response.status_code, 200)
            file_url = weekly_response.data["data"]["file_url"]
            report_path = Path(temp_media) / "reports" / Path(file_url).name
            self.assertTrue(report_path.exists())
            self.assertTrue(ReportTask.objects.filter(user__username="alice", report_type="weekly").exists())

    def test_health_goal_progress_flow(self):
        self._create_user()
        self._login("alice")

        goal_response = self.client.post(
            "/api/v1/health-goals/",
            {
                "goal_type": "weight_loss",
                "target_value": 65,
                "current_value": 68,
                "start_date": "2026-03-26",
                "target_date": "2026-06-26",
                "description": "Reduce weight gradually",
            },
            format="json",
        )
        self.assertEqual(goal_response.status_code, 201)
        goal_id = goal_response.data["data"]["id"]

        progress_response = self.client.post(
            f"/api/v1/health-goals/{goal_id}/progress/",
            {"progress_date": "2026-03-27", "progress_value": 67.5, "note": "first week"},
            format="json",
        )
        self.assertEqual(progress_response.status_code, 201)
        self.assertEqual(HealthGoal.objects.count(), 1)
        self.assertEqual(HealthGoalProgress.objects.count(), 1)

        list_response = self.client.get(f"/api/v1/health-goals/{goal_id}/progress/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data["data"]), 1)

    def test_community_and_external_proxy_flow(self):
        self._create_user()
        self._login("alice")

        post_response = self.client.post(
            "/api/v1/posts/",
            {"title": "Healthy Lunch", "content": "This bowl is easy and low fat."},
            format="json",
        )
        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(Post.objects.count(), 1)
        post_id = post_response.data["data"]["id"]

        comment_response = self.client.post(
            f"/api/v1/posts/{post_id}/comments/",
            {"content": "Looks great."},
            format="json",
        )
        self.assertEqual(comment_response.status_code, 201)
        self.assertEqual(PostComment.objects.count(), 1)

        report_response = self.client.post(
            f"/api/v1/posts/{post_id}/report/",
            {"reason": "spam"},
            format="json",
        )
        self.assertEqual(report_response.status_code, 201)
        self.assertEqual(ContentReport.objects.count(), 1)

        usda_response = self.client.get("/api/v1/external/usda/search/?q=rice")
        self.assertEqual(usda_response.status_code, 200)
        self.assertTrue(usda_response.data["data"]["degraded"])

        barcode_response = self.client.get("/api/v1/external/openfoodfacts/barcode/0000000000000/")
        self.assertEqual(barcode_response.status_code, 200)
        self.assertTrue(barcode_response.data["data"]["degraded"])
