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
            name="RecommendedRecipe",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recipe_id", models.IntegerField()),
                ("rank", models.PositiveSmallIntegerField()),
                ("score", models.FloatField(default=0.0)),
                ("reason_text", models.CharField(default="", max_length=512)),
                ("algo_version", models.CharField(default="hybrid_v1", max_length=32)),
                ("computed_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recommended_recipes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "recommended_recipe", "ordering": ["user_id", "rank"]},
        ),
        migrations.AddIndex(
            model_name="recommendedrecipe",
            index=models.Index(fields=["user_id", "rank"], name="recommended_recipe_user_rank_idx"),
        ),
    ]
