from rest_framework import serializers
from django.db import transaction

from apps.recipes.models import Recipe
from apps.recipes.utils import get_recipe_nutrition_summary

from .models import HealthGoal, HealthGoalProgress, MealRecord, MealRecordItem, UserBehavior


class MealRecordItemSerializer(serializers.ModelSerializer):
    recipe_id = serializers.PrimaryKeyRelatedField(
        source="recipe", queryset=Recipe.objects.all(), required=False, allow_null=True
    )
    recipe_title = serializers.CharField(source="recipe.title", read_only=True)

    class Meta:
        model = MealRecordItem
        fields = [
            "id",
            "recipe_id",
            "recipe_title",
            "ingredient_name_snapshot",
            "amount",
            "unit",
            "energy",
            "protein",
            "fat",
            "carbohydrate",
        ]


class MealRecordSerializer(serializers.ModelSerializer):
    items = MealRecordItemSerializer(many=True)

    class Meta:
        model = MealRecord
        fields = ["id", "record_date", "meal_type", "source_type", "note", "items", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        with transaction.atomic():
            meal_record, _ = MealRecord.objects.get_or_create(
                user=self.context["request"].user,
                record_date=validated_data["record_date"],
                meal_type=validated_data["meal_type"],
                defaults={
                    "source_type": validated_data.get("source_type", "manual"),
                    "note": validated_data.get("note", ""),
                },
            )
            meal_record.source_type = validated_data.get("source_type", meal_record.source_type)
            meal_record.note = validated_data.get("note", meal_record.note)
            meal_record.save(update_fields=["source_type", "note", "updated_at"])
            meal_record.items.all().delete()

            for item_data in items_data:
                recipe = item_data.get("recipe")
                if recipe and not any(key in item_data for key in ("energy", "protein", "fat", "carbohydrate")):
                    summary = get_recipe_nutrition_summary(recipe)
                    if summary:
                        item_data["energy"] = summary.per_serving_energy
                        item_data["protein"] = summary.per_serving_protein
                        item_data["fat"] = summary.per_serving_fat
                        item_data["carbohydrate"] = summary.per_serving_carbohydrate
                MealRecordItem.objects.create(meal_record=meal_record, **item_data)

        return meal_record

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if items_data is not None:
                instance.items.all().delete()
                for item_data in items_data:
                    recipe = item_data.get("recipe")
                    if recipe and not any(key in item_data for key in ("energy", "protein", "fat", "carbohydrate")):
                        summary = get_recipe_nutrition_summary(recipe)
                        if summary:
                            item_data["energy"] = summary.per_serving_energy
                            item_data["protein"] = summary.per_serving_protein
                            item_data["fat"] = summary.per_serving_fat
                            item_data["carbohydrate"] = summary.per_serving_carbohydrate
                    MealRecordItem.objects.create(meal_record=instance, **item_data)

        return instance


class HealthGoalProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthGoalProgress
        fields = ["id", "progress_date", "progress_value", "note", "created_at"]
        read_only_fields = ["created_at"]


class HealthGoalSerializer(serializers.ModelSerializer):
    progress_records = HealthGoalProgressSerializer(many=True, read_only=True)

    class Meta:
        model = HealthGoal
        fields = [
            "id",
            "goal_type",
            "target_value",
            "current_value",
            "start_date",
            "target_date",
            "status",
            "description",
            "progress_records",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        return HealthGoal.objects.create(user=self.context["request"].user, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserBehaviorSerializer(serializers.ModelSerializer):
    recipe_id = serializers.PrimaryKeyRelatedField(
        source="recipe", queryset=Recipe.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = UserBehavior
        fields = ["id", "recipe_id", "behavior_type", "behavior_value", "context_scene", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        return UserBehavior.objects.create(user=self.context["request"].user, **validated_data)
