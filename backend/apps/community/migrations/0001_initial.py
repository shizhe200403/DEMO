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
            name="Post",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField()),
                ("cover_image_url", models.TextField(blank=True, default="")),
                ("status", models.CharField(choices=[("published", "Published"), ("archived", "Archived")], default="published", max_length=32)),
                ("audit_status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=32)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="posts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "post",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PostComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("content", models.TextField()),
                ("status", models.CharField(choices=[("visible", "Visible"), ("hidden", "Hidden")], default="visible", max_length=32)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="community.post")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="post_comments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "post_comment",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ContentReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("target_type", models.CharField(max_length=32)),
                ("target_id", models.BigIntegerField()),
                ("reason", models.TextField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processed", "Processed"), ("rejected", "Rejected")], default="pending", max_length=32)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("processed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="processed_reports", to=settings.AUTH_USER_MODEL)),
                ("reporter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="content_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "content_report",
                "ordering": ["-created_at"],
            },
        ),
    ]

