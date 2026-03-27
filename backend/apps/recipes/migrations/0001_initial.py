from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Ingredient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("canonical_name", models.CharField(max_length=128, unique=True)),
                ("alias_names", models.JSONField(blank=True, default=list)),
                ("category", models.CharField(blank=True, default="", max_length=64)),
                ("default_unit", models.CharField(blank=True, default="", max_length=32)),
                ("is_common", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "ingredient",
                "ordering": ["canonical_name"],
            },
        ),
        migrations.CreateModel(
            name="Recipe",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=255)),
                ("cover_image_url", models.TextField(blank=True, default="")),
                ("description", models.TextField(blank=True, default="")),
                ("portion_size", models.CharField(blank=True, default="", max_length=64)),
                ("servings", models.IntegerField(default=1)),
                ("difficulty", models.CharField(blank=True, default="", max_length=32)),
                ("cook_time_minutes", models.IntegerField(blank=True, null=True)),
                ("prep_time_minutes", models.IntegerField(blank=True, null=True)),
                ("meal_type", models.CharField(blank=True, default="", max_length=32)),
                ("taste_tags", models.JSONField(blank=True, default=list)),
                ("cuisine_tags", models.JSONField(blank=True, default=list)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published"), ("archived", "Archived")], default="draft", max_length=32)),
                ("source_type", models.CharField(default="local", max_length=32)),
                ("source_name", models.CharField(blank=True, default="", max_length=128)),
                ("audit_status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=32)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_recipes", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "recipe",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="RecipeStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("step_no", models.PositiveIntegerField()),
                ("content", models.TextField()),
                ("step_image_url", models.TextField(blank=True, default="")),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="steps", to="recipes.recipe")),
            ],
            options={
                "db_table": "recipe_step",
                "ordering": ["step_no"],
            },
        ),
        migrations.AddConstraint(
            model_name="recipestep",
            constraint=models.UniqueConstraint(fields=("recipe", "step_no"), name="uq_recipe_step"),
        ),
        migrations.CreateModel(
            name="RecipeIngredient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=4, max_digits=12)),
                ("unit", models.CharField(max_length=32)),
                ("is_main", models.BooleanField(default=False)),
                ("remark", models.CharField(blank=True, default="", max_length=255)),
                ("ingredient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recipe_links", to="recipes.ingredient")),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recipe_ingredients", to="recipes.recipe")),
            ],
            options={
                "db_table": "recipe_ingredient",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="RecipeNutritionSummary",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("per_serving_energy", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("per_serving_protein", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("per_serving_fat", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("per_serving_carbohydrate", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("per_serving_fiber", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("per_serving_sodium", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("per_serving_calcium", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("per_serving_iron", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("per_serving_vitamin_a", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("per_serving_vitamin_c", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("calculation_method", models.CharField(blank=True, default="", max_length=64)),
                ("calculated_at", models.DateTimeField(auto_now_add=True)),
                ("recipe", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="nutrition_summary", to="recipes.recipe")),
            ],
            options={
                "db_table": "recipe_nutrition_summary",
            },
        ),
        migrations.CreateModel(
            name="UserFavoriteRecipe",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorited_by", to="recipes.recipe")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorite_recipes", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "user_favorite_recipe",
            },
        ),
        migrations.AddConstraint(
            model_name="userfavoriterecipe",
            constraint=models.UniqueConstraint(fields=("user", "recipe"), name="uq_user_favorite_recipe"),
        ),
    ]

