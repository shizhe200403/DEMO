from decimal import Decimal

from rest_framework import serializers

from apps.recipes.models import Recipe


class RecipeNutritionCalculateSerializer(serializers.Serializer):
    recipe_id = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    portion_multiplier = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, default=Decimal("1"))
    include_condiments = serializers.BooleanField(required=False, default=True)


class NutritionAnalysisSerializer(serializers.Serializer):
    bmi = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    goal_hint = serializers.CharField()
    calorie_target = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    protein_target = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)

