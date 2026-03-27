from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.recipes.models import Recipe


class MealRecord(TimeStampedModel):
    MEAL_TYPE_CHOICES = [
        ("breakfast", "Breakfast"),
        ("lunch", "Lunch"),
        ("dinner", "Dinner"),
        ("snack", "Snack"),
    ]
    SOURCE_TYPE_CHOICES = [
        ("manual", "Manual"),
        ("copy_yesterday", "Copy Yesterday"),
        ("quick_add", "Quick Add"),
        ("scan", "Scan"),
        ("ai_parse", "AI Parse"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meal_records")
    record_date = models.DateField()
    meal_type = models.CharField(max_length=32, choices=MEAL_TYPE_CHOICES)
    source_type = models.CharField(max_length=32, choices=SOURCE_TYPE_CHOICES, default="manual")
    note = models.TextField(blank=True, default="")

    class Meta:
        db_table = "meal_record"
        ordering = ["-record_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "record_date", "meal_type"],
                name="uq_meal_record_unique_context",
            )
        ]


class MealRecordItem(TimeStampedModel):
    meal_record = models.ForeignKey(MealRecord, on_delete=models.CASCADE, related_name="items")
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True, related_name="meal_record_items")
    ingredient_name_snapshot = models.CharField(max_length=255, blank=True, default="")
    amount = models.DecimalField(max_digits=12, decimal_places=4)
    unit = models.CharField(max_length=32)
    energy = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    protein = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    fat = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    carbohydrate = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = "meal_record_item"


class UserBehavior(TimeStampedModel):
    BEHAVIOR_TYPE_CHOICES = [
        ("view", "View"),
        ("stay", "Stay"),
        ("click", "Click"),
        ("favorite", "Favorite"),
        ("rate", "Rate"),
        ("share", "Share"),
        ("ignore", "Ignore"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="behaviors")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True, blank=True, related_name="behaviors")
    behavior_type = models.CharField(max_length=32, choices=BEHAVIOR_TYPE_CHOICES)
    behavior_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    context_scene = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "user_behavior"
        ordering = ["-created_at"]


class HealthGoal(TimeStampedModel):
    GOAL_TYPE_CHOICES = [
        ("weight_loss", "Weight Loss"),
        ("muscle_gain", "Muscle Gain"),
        ("blood_sugar_control", "Blood Sugar Control"),
        ("fat_control", "Fat Control"),
        ("protein_up", "Protein Up"),
        ("diet_balance", "Diet Balance"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_goals")
    goal_type = models.CharField(max_length=32, choices=GOAL_TYPE_CHOICES)
    target_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    current_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="active")
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "health_goal"
        ordering = ["-created_at"]


class HealthGoalProgress(TimeStampedModel):
    health_goal = models.ForeignKey(HealthGoal, on_delete=models.CASCADE, related_name="progress_records")
    progress_date = models.DateField()
    progress_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    note = models.TextField(blank=True, default="")

    class Meta:
        db_table = "health_goal_progress"
        ordering = ["-progress_date", "-created_at"]
