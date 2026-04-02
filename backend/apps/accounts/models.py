from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("user", "User"),
        ("admin", "Admin"),
        ("auditor", "Auditor"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("disabled", "Disabled"),
        ("pending", "Pending"),
    ]

    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="user")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="active")
    nickname = models.CharField(max_length=64, blank=True, default="")
    signature = models.CharField(max_length=255, blank=True, default="")
    avatar_url = models.TextField(blank=True, default="")
    security_question = models.CharField(max_length=128, blank=True, default="")
    security_answer_hash = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "app_user"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    gender = models.CharField(max_length=16, blank=True, default="")
    birthday = models.DateField(null=True, blank=True)
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    target_weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    activity_level = models.CharField(max_length=32, blank=True, default="")
    occupation = models.CharField(max_length=64, blank=True, default="")
    budget_level = models.CharField(max_length=32, blank=True, default="")
    cooking_skill = models.CharField(max_length=32, blank=True, default="")
    meal_preference = models.CharField(max_length=64, blank=True, default="")
    diet_type = models.CharField(max_length=64, blank=True, default="")
    is_outdoor_eating_frequent = models.BooleanField(default=False)
    household_size = models.IntegerField(default=1)

    class Meta:
        db_table = "user_profile"


class UserHealthCondition(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="health_condition")
    has_allergy = models.BooleanField(default=False)
    allergy_tags = models.JSONField(default=list, blank=True)
    avoid_food_tags = models.JSONField(default=list, blank=True)
    religious_restriction = models.CharField(max_length=64, blank=True, default="")
    has_hypertension = models.BooleanField(default=False)
    has_diabetes = models.BooleanField(default=False)
    has_hyperlipidemia = models.BooleanField(default=False)
    is_pregnant = models.BooleanField(default=False)
    is_lactating = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "user_health_condition"
