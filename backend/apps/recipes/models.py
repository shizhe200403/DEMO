from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Ingredient(TimeStampedModel):
    canonical_name = models.CharField(max_length=128, unique=True)
    alias_names = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=64, blank=True, default="")
    default_unit = models.CharField(max_length=32, blank=True, default="")
    is_common = models.BooleanField(default=True)

    class Meta:
        db_table = "ingredient"
        ordering = ["canonical_name"]

    def __str__(self) -> str:
        return self.canonical_name


class Recipe(TimeStampedModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]
    AUDIT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    title = models.CharField(max_length=255)
    cover_image_url = models.TextField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    portion_size = models.CharField(max_length=64, blank=True, default="")
    servings = models.IntegerField(default=1)
    difficulty = models.CharField(max_length=32, blank=True, default="")
    cook_time_minutes = models.IntegerField(null=True, blank=True)
    prep_time_minutes = models.IntegerField(null=True, blank=True)
    meal_type = models.CharField(max_length=32, blank=True, default="")
    taste_tags = models.JSONField(default=list, blank=True)
    cuisine_tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="draft")
    source_type = models.CharField(max_length=32, default="local")
    source_name = models.CharField(max_length=128, blank=True, default="")
    audit_status = models.CharField(max_length=32, choices=AUDIT_STATUS_CHOICES, default="pending")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_recipes",
    )

    class Meta:
        db_table = "recipe"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class RecipeStep(TimeStampedModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="steps")
    step_no = models.PositiveIntegerField()
    content = models.TextField()
    step_image_url = models.TextField(blank=True, default="")

    class Meta:
        db_table = "recipe_step"
        ordering = ["step_no"]
        constraints = [
            models.UniqueConstraint(fields=["recipe", "step_no"], name="uq_recipe_step"),
        ]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name="recipe_links")
    amount = models.DecimalField(max_digits=12, decimal_places=4)
    unit = models.CharField(max_length=32)
    is_main = models.BooleanField(default=False)
    remark = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "recipe_ingredient"
        ordering = ["id"]


class RecipeNutritionSummary(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE, related_name="nutrition_summary")
    per_serving_energy = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    per_serving_protein = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    per_serving_fat = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    per_serving_carbohydrate = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    per_serving_fiber = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    per_serving_sodium = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    per_serving_calcium = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    per_serving_iron = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    per_serving_vitamin_a = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    per_serving_vitamin_c = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    calculation_method = models.CharField(max_length=64, blank=True, default="")
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recipe_nutrition_summary"


class UserFavoriteRecipe(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_recipes")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        db_table = "user_favorite_recipe"
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"], name="uq_user_favorite_recipe"),
        ]

