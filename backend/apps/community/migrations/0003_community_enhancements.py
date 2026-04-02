from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0002_contentreport_collaboration_fields"),
        ("recipes", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="linked_recipe",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="community_posts",
                to="recipes.recipe",
            ),
        ),
        migrations.AddField(
            model_name="postcomment",
            name="image_url",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.CreateModel(
            name="PostLike",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="post_likes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="likes",
                        to="community.post",
                    ),
                ),
            ],
            options={"db_table": "post_like"},
        ),
        migrations.AddConstraint(
            model_name="postlike",
            constraint=models.UniqueConstraint(fields=["user", "post"], name="uq_post_like"),
        ),
    ]
