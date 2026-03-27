from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeNutritionSummary,
    RecipeStep,
    UserFavoriteRecipe,
)
from .utils import get_recipe_nutrition_summary


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = [
            "id",
            "canonical_name",
            "alias_names",
            "category",
            "default_unit",
            "is_common",
        ]


class RecipeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeStep
        fields = ["id", "step_no", "content", "step_image_url"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        source="ingredient", queryset=Ingredient.objects.all(), write_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ["id", "ingredient", "ingredient_id", "amount", "unit", "is_main", "remark"]


class RecipeNutritionSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeNutritionSummary
        exclude = ["recipe"]


class ExternalImportStepSerializer(serializers.Serializer):
    content = serializers.CharField()


class ExternalImportIngredientSerializer(serializers.Serializer):
    name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=4, required=False)
    unit = serializers.CharField(required=False, allow_blank=True, default="serving")
    is_main = serializers.BooleanField(required=False, default=False)


class ImportExternalRecipeSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    cover_image_url = serializers.CharField(required=False, allow_blank=True, default="")
    portion_size = serializers.CharField(required=False, allow_blank=True, default="1 份")
    servings = serializers.IntegerField(required=False, default=1)
    difficulty = serializers.CharField(required=False, allow_blank=True, default="easy")
    cook_time_minutes = serializers.IntegerField(required=False, allow_null=True)
    prep_time_minutes = serializers.IntegerField(required=False, allow_null=True)
    meal_type = serializers.CharField(required=False, allow_blank=True, default="")
    taste_tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    cuisine_tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    source_name = serializers.CharField(required=False, allow_blank=True, default="external")
    source_url = serializers.CharField(required=False, allow_blank=True, default="")
    ingredients = ExternalImportIngredientSerializer(many=True, required=False, default=list)
    steps = ExternalImportStepSerializer(many=True, required=False, default=list)
    nutrition_summary = RecipeNutritionSummarySerializer(required=False, allow_null=True)


class RecipeSerializer(serializers.ModelSerializer):
    steps = RecipeStepSerializer(many=True, required=False)
    ingredients = RecipeIngredientSerializer(source="recipe_ingredients", many=True, required=False)
    nutrition_summary = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "cover_image_url",
            "description",
            "portion_size",
            "servings",
            "difficulty",
            "cook_time_minutes",
            "prep_time_minutes",
            "meal_type",
            "taste_tags",
            "cuisine_tags",
            "status",
            "source_type",
            "source_name",
            "audit_status",
            "created_by",
            "created_at",
            "updated_at",
            "steps",
            "ingredients",
            "nutrition_summary",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    @extend_schema_field(RecipeNutritionSummarySerializer(allow_null=True))
    def get_nutrition_summary(self, obj):
        summary = get_recipe_nutrition_summary(obj)
        if summary is None:
            return None
        return RecipeNutritionSummarySerializer(summary).data

    @transaction.atomic
    def create(self, validated_data):
        steps_data = validated_data.pop("steps", [])
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        nutrition_data = validated_data.pop("nutrition_summary", None)
        recipe = Recipe.objects.create(**validated_data)

        for step_data in steps_data:
            RecipeStep.objects.create(recipe=recipe, **step_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient_data)

        if nutrition_data:
            RecipeNutritionSummary.objects.update_or_create(recipe=recipe, defaults=nutrition_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        steps_data = validated_data.pop("steps", None)
        ingredients_data = validated_data.pop("recipe_ingredients", None)
        nutrition_data = validated_data.pop("nutrition_summary", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if steps_data is not None:
            instance.steps.all().delete()
            for step_data in steps_data:
                RecipeStep.objects.create(recipe=instance, **step_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(recipe=instance, **ingredient_data)

        if nutrition_data is not None:
            RecipeNutritionSummary.objects.update_or_create(recipe=instance, defaults=nutrition_data)

        return instance


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFavoriteRecipe
        fields = ["id", "user", "recipe", "created_at"]
        read_only_fields = ["user", "created_at"]
