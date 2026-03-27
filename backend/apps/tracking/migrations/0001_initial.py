from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("recipes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MealRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("record_date", models.DateField()),
                ("meal_type", models.CharField(choices=[("breakfast", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner"), ("snack", "Snack")], max_length=32)),
                ("source_type", models.CharField(choices=[("manual", "Manual"), ("copy_yesterday", "Copy Yesterday"), ("quick_add", "Quick Add"), ("scan", "Scan"), ("ai_parse", "AI Parse")], default="manual", max_length=32)),
                ("note", models.TextField(blank=True, default="")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="meal_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "meal_record",
                "ordering": ["-record_date", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="mealrecord",
            constraint=models.UniqueConstraint(fields=("user", "record_date", "meal_type"), name="uq_meal_record_unique_context"),
        ),
        migrations.CreateModel(
            name="MealRecordItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("ingredient_name_snapshot", models.CharField(blank=True, default="", max_length=255)),
                ("amount", models.DecimalField(decimal_places=4, max_digits=12)),
                ("unit", models.CharField(max_length=32)),
                ("energy", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("protein", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("fat", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("carbohydrate", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("meal_record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="tracking.mealrecord")),
                ("recipe", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="meal_record_items", to="recipes.recipe")),
            ],
            options={
                "db_table": "meal_record_item",
            },
        ),
        migrations.CreateModel(
            name="UserBehavior",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("behavior_type", models.CharField(choices=[("view", "View"), ("stay", "Stay"), ("click", "Click"), ("favorite", "Favorite"), ("rate", "Rate"), ("share", "Share"), ("ignore", "Ignore")], max_length=32)),
                ("behavior_value", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("context_scene", models.CharField(blank=True, default="", max_length=64)),
                ("recipe", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="behaviors", to="recipes.recipe")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="behaviors", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "user_behavior",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="HealthGoal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("goal_type", models.CharField(choices=[("weight_loss", "Weight Loss"), ("muscle_gain", "Muscle Gain"), ("blood_sugar_control", "Blood Sugar Control"), ("fat_control", "Fat Control"), ("protein_up", "Protein Up"), ("diet_balance", "Diet Balance")], max_length=32)),
                ("target_value", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("current_value", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("target_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("paused", "Paused"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="active", max_length=32)),
                ("description", models.TextField(blank=True, default="")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="health_goals", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "health_goal",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="HealthGoalProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("progress_date", models.DateField()),
                ("progress_value", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("note", models.TextField(blank=True, default="")),
                ("health_goal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress_records", to="tracking.healthgoal")),
            ],
            options={
                "db_table": "health_goal_progress",
                "ordering": ["-progress_date", "-created_at"],
            },
        ),
    ]

