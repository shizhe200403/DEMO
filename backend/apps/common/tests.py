import shutil
import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.accounts.models import UserHealthCondition, UserProfile
from apps.common.models import AdminOperationLog
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

    def _response_items(self, response):
        data = response.data["data"]
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        return data

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

    def test_admin_can_list_and_update_users(self):
        admin_user = self._create_user(username="admin_user", email="admin@example.com", phone="13800000002")
        admin_user.role = "admin"
        admin_user.save(update_fields=["role"])
        managed_user = self._create_user(username="carol", email="carol@example.com", phone="13800000003")

        self._login("admin@example.com")

        list_response = self.client.get("/api/v1/accounts/admin/users/?keyword=carol")
        self.assertEqual(list_response.status_code, 200)
        items = list_response.data["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["username"], "carol")

        detail_response = self.client.patch(
            f"/api/v1/accounts/admin/users/{managed_user.id}/",
            {
                "account": {"nickname": "Carol Ops", "status": "disabled"},
                "profile": {"diet_type": "high_protein", "activity_level": "high"},
                "health_condition": {"has_hypertension": True},
            },
            format="json",
        )
        self.assertEqual(detail_response.status_code, 200)

        managed_user.refresh_from_db()
        managed_user.profile.refresh_from_db()
        managed_user.health_condition.refresh_from_db()
        self.assertEqual(managed_user.nickname, "Carol Ops")
        self.assertEqual(managed_user.status, "disabled")
        self.assertFalse(managed_user.is_active)
        self.assertEqual(managed_user.profile.diet_type, "high_protein")
        self.assertTrue(managed_user.health_condition.has_hypertension)

    def test_disabled_user_cannot_login_refresh_or_access_with_existing_token(self):
        admin_user = self._create_user(username="disableops", email="disableops@example.com", phone="13800000004")
        admin_user.role = "admin"
        admin_user.is_staff = True
        admin_user.save(update_fields=["role", "is_staff"])
        managed_user = self._create_user(username="eve", email="eve@example.com", phone="13800000005")

        user_client = self.client_class()
        login_response = user_client.post(
            "/api/v1/accounts/login/",
            {"account": "eve@example.com", "password": "Password123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.data["data"]["access"]
        refresh_token = login_response.data["data"]["refresh"]

        self._login("disableops@example.com")
        disable_response = self.client.patch(
            f"/api/v1/accounts/admin/users/{managed_user.id}/",
            {"account": {"status": "disabled"}},
            format="json",
        )
        self.assertEqual(disable_response.status_code, 200)

        managed_user.refresh_from_db()
        self.assertEqual(managed_user.status, "disabled")
        self.assertFalse(managed_user.is_active)

        relogin_response = user_client.post(
            "/api/v1/accounts/login/",
            {"account": "eve@example.com", "password": "Password123!"},
            format="json",
        )
        self.assertEqual(relogin_response.status_code, 400)

        user_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me_response = user_client.get("/api/v1/accounts/me/")
        self.assertEqual(me_response.status_code, 401)

        user_client.credentials()
        refresh_response = user_client.post(
            "/api/v1/accounts/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 401)

    def test_admin_bulk_disable_users_syncs_is_active(self):
        admin_user = self._create_user(username="bulkops", email="bulkops@example.com", phone="13800000006")
        admin_user.role = "admin"
        admin_user.is_staff = True
        admin_user.save(update_fields=["role", "is_staff"])
        managed_user = self._create_user(username="frank", email="frank@example.com", phone="13800000007")

        self._login("bulkops@example.com")
        response = self.client.post(
            "/api/v1/accounts/admin/users/bulk/",
            {"ids": [managed_user.id], "status": "disabled"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        managed_user.refresh_from_db()
        self.assertEqual(managed_user.status, "disabled")
        self.assertFalse(managed_user.is_active)

    def test_regular_user_cannot_access_admin_user_endpoints(self):
        self._create_user()
        self._login("alice")

        response = self.client.get("/api/v1/accounts/admin/users/")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_moderate_community_content(self):
        admin_user = self._create_user(username="ops", email="ops@example.com", phone="13800000009")
        admin_user.role = "admin"
        admin_user.is_staff = True
        admin_user.save(update_fields=["role", "is_staff"])

        author = self._create_user(username="writer", email="writer@example.com", phone="13800000010")
        reporter = self._create_user(username="reader", email="reader@example.com", phone="13800000011")

        post = Post.objects.create(
            user=author,
            title="Need Review",
            content="This post still needs moderation.",
            status="published",
            audit_status="pending",
        )
        PostComment.objects.create(post=post, user=reporter, content="Looks risky", status="hidden")
        report = ContentReport.objects.create(
            reporter=reporter,
            target_type="post",
            target_id=post.id,
            reason="misleading nutrition claim",
        )

        self._login("ops@example.com")

        post_list_response = self.client.get("/api/v1/community/admin/posts/")
        self.assertEqual(post_list_response.status_code, 200)
        post_items = post_list_response.data["data"]["items"]
        self.assertEqual(post_items[0]["audit_status"], "pending")
        self.assertEqual(post_items[0]["hidden_comment_count"], 1)
        self.assertEqual(post_items[0]["report_count"], 1)

        post_detail_response = self.client.patch(
            f"/api/v1/community/admin/posts/{post.id}/",
            {"audit_status": "approved", "status": "published", "title": "Reviewed Post"},
            format="json",
        )
        self.assertEqual(post_detail_response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.audit_status, "approved")
        self.assertEqual(post.title, "Reviewed Post")

        report_list_response = self.client.get("/api/v1/community/admin/reports/")
        self.assertEqual(report_list_response.status_code, 200)
        report_items = report_list_response.data["data"]["items"]
        self.assertEqual(report_items[0]["target_post_title"], "Reviewed Post")

        report_detail_response = self.client.patch(
            f"/api/v1/community/admin/reports/{report.id}/",
            {"status": "processed"},
            format="json",
        )
        self.assertEqual(report_detail_response.status_code, 200)
        report.refresh_from_db()
        self.assertEqual(report.status, "processed")
        self.assertEqual(report.processed_by_id, admin_user.id)
        self.assertIsNotNone(report.processed_at)

    def test_regular_user_cannot_access_admin_community_endpoints(self):
        self._create_user()
        self._login("alice")

        post_response = self.client.get("/api/v1/community/admin/posts/")
        report_response = self.client.get("/api/v1/community/admin/reports/")

        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(report_response.status_code, 403)

    def test_admin_can_view_operations_report_overview(self):
        admin_user = self._create_user(username="opsreport", email="opsreport@example.com", phone="13800000013")
        admin_user.role = "admin"
        admin_user.is_staff = True
        admin_user.save(update_fields=["role", "is_staff"])

        normal_user = self._create_user(username="tracked", email="tracked@example.com", phone="13800000014")
        recipe = self._create_recipe_bundle(normal_user, title="Ops Recipe")
        recipe.audit_status = "pending"
        recipe.save(update_fields=["audit_status"])

        post = Post.objects.create(
            user=normal_user,
            title="Ops Post",
            content="Need moderation",
            status="published",
            audit_status="pending",
        )
        PostComment.objects.create(post=post, user=normal_user, content="Hidden risk", status="hidden")
        ContentReport.objects.create(reporter=normal_user, target_type="post", target_id=post.id, reason="ops review")

        MealRecord.objects.create(user=normal_user, record_date=date.today(), meal_type="lunch")
        ReportTask.objects.create(user=normal_user, report_type="weekly", status="completed")

        self._login("opsreport@example.com")

        response = self.client.get("/api/v1/reports/admin/overview/")
        self.assertEqual(response.status_code, 200)
        summary = response.data["data"]["summary"]
        self.assertGreaterEqual(summary["users_total"], 2)
        self.assertGreaterEqual(summary["recipes_pending"], 1)
        self.assertGreaterEqual(summary["posts_pending"], 1)
        self.assertGreaterEqual(summary["pending_reports"], 1)
        self.assertGreaterEqual(summary["hidden_comments"], 1)
        self.assertGreaterEqual(summary["meal_records_last_7_days"], 1)
        self.assertGreaterEqual(summary["report_tasks_completed"], 1)
        self.assertGreaterEqual(len(response.data["data"]["recent_tasks"]), 1)

    def test_regular_user_cannot_access_operations_report_overview(self):
        self._create_user()
        self._login("alice")

        response = self.client.get("/api/v1/reports/admin/overview/")
        self.assertEqual(response.status_code, 403)

    def test_admin_actions_are_written_to_operation_logs(self):
        admin_user = self._create_user(username="auditops", email="auditops@example.com", phone="13800000015")
        admin_user.role = "admin"
        admin_user.is_staff = True
        admin_user.save(update_fields=["role", "is_staff"])

        managed_user = self._create_user(username="dora", email="dora@example.com", phone="13800000016")
        recipe = self._create_recipe_bundle(managed_user, title="Audit Recipe")
        post = Post.objects.create(
            user=managed_user,
            title="Needs Review",
            content="Waiting for moderation",
            status="published",
            audit_status="pending",
        )
        comment = PostComment.objects.create(post=post, user=managed_user, content="Unsafe note", status="visible")
        report = ContentReport.objects.create(reporter=managed_user, target_type="post", target_id=post.id, reason="audit this")

        self._login("auditops@example.com")

        user_response = self.client.patch(
            f"/api/v1/accounts/admin/users/{managed_user.id}/",
            {"account": {"nickname": "Dora Updated", "status": "disabled"}},
            format="json",
        )
        self.assertEqual(user_response.status_code, 200)

        recipe_response = self.client.patch(
            f"/api/v1/recipes/{recipe.id}/",
            {"audit_status": "rejected", "status": "draft"},
            format="json",
        )
        self.assertEqual(recipe_response.status_code, 200)

        post_response = self.client.patch(
            f"/api/v1/community/admin/posts/{post.id}/",
            {"audit_status": "approved", "title": "Reviewed Needs Review"},
            format="json",
        )
        self.assertEqual(post_response.status_code, 200)

        comment_response = self.client.delete(f"/api/v1/comments/{comment.id}/")
        self.assertEqual(comment_response.status_code, 200)

        report_response = self.client.patch(
            f"/api/v1/community/admin/reports/{report.id}/",
            {"status": "processed"},
            format="json",
        )
        self.assertEqual(report_response.status_code, 200)

        logs_response = self.client.get("/api/v1/admin/operation-logs/?page_size=10")
        self.assertEqual(logs_response.status_code, 200)
        items = logs_response.data["data"]["items"]
        self.assertGreaterEqual(len(items), 5)
        summaries = [item["summary"] for item in items]
        modules = {item["module"] for item in items}
        self.assertIn("users", modules)
        self.assertIn("recipes", modules)
        self.assertIn("community", modules)
        self.assertTrue(any("Dora Updated" in summary or "dora" in summary for summary in summaries))
        self.assertTrue(any("Audit Recipe" in summary for summary in summaries))
        self.assertTrue(any("举报" in summary for summary in summaries))
        self.assertGreaterEqual(AdminOperationLog.objects.count(), 5)

        user_log_response = self.client.get(f"/api/v1/admin/operation-logs/?target_type=user&target_id={managed_user.id}")
        self.assertEqual(user_log_response.status_code, 200)
        user_items = user_log_response.data["data"]["items"]
        self.assertEqual(len(user_items), 1)
        self.assertEqual(user_items[0]["target_type"], "user")

        post_related_response = self.client.get(f"/api/v1/admin/operation-logs/?related_target_type=post&related_target_id={post.id}")
        self.assertEqual(post_related_response.status_code, 200)
        post_items = post_related_response.data["data"]["items"]
        self.assertGreaterEqual(len(post_items), 3)
        self.assertTrue(any(item["action"] == "moderate_post" for item in post_items))
        self.assertTrue(any(item["action"] == "hide_comment" for item in post_items))
        self.assertTrue(any(item["action"] == "review_report" for item in post_items))

    def test_regular_user_cannot_access_operation_logs(self):
        self._create_user()
        self._login("alice")

        response = self.client.get("/api/v1/admin/operation-logs/")
        self.assertEqual(response.status_code, 403)

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

        favorites_response = self.client.get("/api/v1/recipes/favorites/")
        self.assertEqual(favorites_response.status_code, 200)
        favorite_ids = [item["id"] for item in favorites_response.data["data"]]
        self.assertIn(recipe.id, favorite_ids)

    def test_recipe_library_bootstraps_starter_data(self):
        self._create_user()
        self._login("alice")

        response = self.client.get("/api/v1/recipes/")
        self.assertEqual(response.status_code, 200)
        items = self._response_items(response)
        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0]["status"], "published")
        self.assertEqual(items[0]["audit_status"], "approved")
        self.assertIsNotNone(items[0]["nutrition_summary"])

    def test_archived_recipe_does_not_reappear_in_list(self):
        user = self._create_user()
        self._login("alice")
        recipe = self._create_recipe_bundle(user, title="Will Be Archived")

        delete_response = self.client.delete(f"/api/v1/recipes/{recipe.id}/")
        self.assertEqual(delete_response.status_code, 200)

        recipe.refresh_from_db()
        self.assertEqual(recipe.status, "archived")

        list_response = self.client.get("/api/v1/recipes/")
        self.assertEqual(list_response.status_code, 200)
        items = self._response_items(list_response)
        recipe_ids = [item["id"] for item in items]
        self.assertNotIn(recipe.id, recipe_ids)

    def test_archived_starter_recipe_is_not_bootstrapped_again(self):
        user = self._create_user(username="admin_user", email="admin@example.com", phone="13800000002")
        user.role = "admin"
        user.save(update_fields=["role"])
        self._login("admin@example.com")

        list_response = self.client.get("/api/v1/recipes/")
        self.assertEqual(list_response.status_code, 200)
        items = self._response_items(list_response)
        starter_recipe_id = items[0]["id"]

        delete_response = self.client.delete(f"/api/v1/recipes/{starter_recipe_id}/")
        self.assertEqual(delete_response.status_code, 200)

        refresh_response = self.client.get("/api/v1/recipes/")
        self.assertEqual(refresh_response.status_code, 200)
        refreshed_items = self._response_items(refresh_response)
        refreshed_ids = [item["id"] for item in refreshed_items]
        self.assertNotIn(starter_recipe_id, refreshed_ids)

    def test_user_can_create_recipe_with_freeform_ingredients(self):
        self._create_user()
        self._login("alice")

        response = self.client.post(
            "/api/v1/recipes/",
            {
                "title": "自制鸡胸沙拉",
                "description": "用户自己上传的工作日晚餐",
                "meal_type": "lunch",
                "difficulty": "easy",
                "portion_size": "1 份",
                "servings": 1,
                "cook_time_minutes": 12,
                "prep_time_minutes": 8,
                "ingredients": [
                    {"ingredient_name": "鸡胸肉", "amount": 150, "unit": "g", "is_main": True},
                    {"ingredient_name": "生菜", "amount": 80, "unit": "g", "is_main": False},
                ],
                "steps": [
                    {"step_no": 1, "content": "鸡胸肉煎熟切片。"},
                    {"step_no": 2, "content": "和生菜拌匀后装盘。"},
                ],
                "nutrition_input": {
                    "per_serving_energy": 320,
                    "per_serving_protein": 28,
                    "per_serving_fat": 9,
                    "per_serving_carbohydrate": 18,
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        recipe_id = response.data["data"]["id"]
        recipe = Recipe.objects.get(id=recipe_id)
        self.assertEqual(recipe.created_by.username, "alice")
        self.assertEqual(recipe.source_type, "user_upload")
        self.assertEqual(recipe.status, "published")
        self.assertEqual(recipe.audit_status, "approved")
        self.assertTrue(RecipeNutritionSummary.objects.filter(recipe_id=recipe_id).exists())
        self.assertEqual(RecipeStep.objects.filter(recipe_id=recipe_id).count(), 2)
        self.assertEqual(recipe.recipe_ingredients.count(), 2)
        self.assertTrue(Ingredient.objects.filter(canonical_name="鸡胸肉").exists())

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

            task_list_response = self.client.get("/api/v1/reports/tasks/")
            self.assertEqual(task_list_response.status_code, 200)
            self.assertEqual(task_list_response.data["data"][0]["report_type"], "weekly")
            self.assertEqual(task_list_response.data["data"][0]["status"], "completed")

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

    def test_community_flow(self):
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
        self.assertEqual(comment_response.data["data"]["user_info"]["display_name"], "alice")

        report_response = self.client.post(
            f"/api/v1/posts/{post_id}/report/",
            {"reason": "spam"},
            format="json",
        )
        self.assertEqual(report_response.status_code, 201)
        self.assertEqual(ContentReport.objects.count(), 1)

        PostComment.objects.filter(post_id=post_id).update(status="hidden")
        post_list_response = self.client.get("/api/v1/posts/")
        self.assertEqual(post_list_response.status_code, 200)
        listed_post = (post_list_response.data["data"].get("items") or post_list_response.data["data"])[0]
        self.assertEqual(listed_post["user_info"]["display_name"], "alice")
        self.assertEqual(listed_post["comments"], [])
