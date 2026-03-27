from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import NutritionAnalysisSerializer, RecipeNutritionCalculateSerializer
from .services import analyze_user_nutrition, calculate_recipe_nutrition


class RecipeNutritionResultSerializer(serializers.Serializer):
    energy = serializers.DecimalField(max_digits=12, decimal_places=4)
    protein = serializers.DecimalField(max_digits=12, decimal_places=4)
    fat = serializers.DecimalField(max_digits=12, decimal_places=4)
    carbohydrate = serializers.DecimalField(max_digits=12, decimal_places=4)


class EnvelopeRecipeNutritionSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = RecipeNutritionResultSerializer()


class EnvelopeNutritionAnalysisSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = NutritionAnalysisSerializer()


class RecipeNutritionCalculateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=RecipeNutritionCalculateSerializer, responses=EnvelopeRecipeNutritionSerializer)
    def post(self, request):
        serializer = RecipeNutritionCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.validated_data["recipe_id"]
        portion_multiplier = serializer.validated_data["portion_multiplier"]
        data = calculate_recipe_nutrition(recipe, portion_multiplier=portion_multiplier)
        return Response({"code": 0, "message": "success", "data": data})


class NutritionAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=EnvelopeNutritionAnalysisSerializer)
    def get(self, request):
        data = analyze_user_nutrition(request.user)
        return Response({"code": 0, "message": "success", "data": data})
