from django.conf import settings
from django.contrib.auth import models as auth_models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0001_initial"),
        ("auth", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, max_length=150, unique=True, verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name="email address")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("phone", models.CharField(blank=True, max_length=32, null=True, unique=True)),
                ("role", models.CharField(choices=[("user", "User"), ("admin", "Admin"), ("auditor", "Auditor")], default="user", max_length=32)),
                ("status", models.CharField(choices=[("active", "Active"), ("disabled", "Disabled"), ("pending", "Pending")], default="active", max_length=32)),
                ("nickname", models.CharField(blank=True, default="", max_length=64)),
                ("signature", models.CharField(blank=True, default="", max_length=255)),
                ("avatar_url", models.TextField(blank=True, default="")),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "db_table": "app_user",
                "swappable": "AUTH_USER_MODEL",
            },
            managers=[
                ("objects", auth_models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("gender", models.CharField(blank=True, default="", max_length=16)),
                ("birthday", models.DateField(blank=True, null=True)),
                ("height_cm", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("weight_kg", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("target_weight_kg", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("activity_level", models.CharField(blank=True, default="", max_length=32)),
                ("occupation", models.CharField(blank=True, default="", max_length=64)),
                ("budget_level", models.CharField(blank=True, default="", max_length=32)),
                ("cooking_skill", models.CharField(blank=True, default="", max_length=32)),
                ("meal_preference", models.CharField(blank=True, default="", max_length=64)),
                ("diet_type", models.CharField(blank=True, default="", max_length=64)),
                ("is_outdoor_eating_frequent", models.BooleanField(default=False)),
                ("household_size", models.IntegerField(default=1)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "user_profile",
            },
        ),
        migrations.CreateModel(
            name="UserHealthCondition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("has_allergy", models.BooleanField(default=False)),
                ("allergy_tags", models.JSONField(blank=True, default=list)),
                ("avoid_food_tags", models.JSONField(blank=True, default=list)),
                ("religious_restriction", models.CharField(blank=True, default="", max_length=64)),
                ("has_hypertension", models.BooleanField(default=False)),
                ("has_diabetes", models.BooleanField(default=False)),
                ("has_hyperlipidemia", models.BooleanField(default=False)),
                ("is_pregnant", models.BooleanField(default=False)),
                ("is_lactating", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True, default="")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="health_condition", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "user_health_condition",
            },
        ),
    ]

