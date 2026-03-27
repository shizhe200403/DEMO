from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recipes.models import Recipe

from .services import build_recommendations, score_recipe


class RecommendationItemSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()
    title = serializers.CharField()
    score = serializers.FloatField()
    reason_text = serializers.CharField()


class EnvelopeRecommendationListSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = RecommendationItemSerializer(many=True)


class ExplainRecommendationDataSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()
    title = serializers.CharField()
    score = serializers.FloatField()
    reason_text = serializers.CharField()


class EnvelopeExplainRecommendationSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ExplainRecommendationDataSerializer()


class HomeRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=EnvelopeRecommendationListSerializer)
    def get(self, request):
        data = build_recommendations(request.user, limit=10)
        return Response({"code": 0, "message": "success", "data": data})


class ProfileRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=EnvelopeRecommendationListSerializer)
    def get(self, request):
        data = build_recommendations(request.user, limit=20)
        return Response({"code": 0, "message": "success", "data": data})


class ExplainRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name="recipe_id", location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT)],
        responses=EnvelopeExplainRecommendationSerializer,
    )
    def get(self, request, recipe_id):
        recipe = Recipe.objects.select_related("nutrition_summary").filter(id=recipe_id).first()
        if recipe is None:
            return Response({"code": 404, "message": "recipe not found", "data": None}, status=404)

        score = score_recipe(recipe, request.user)
        reasons = build_recommendations(request.user, limit=50)
        reason_text = next((item["reason_text"] for item in reasons if item["recipe_id"] == recipe.id), "根据你的画像和历史行为推荐")
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "recipe_id": recipe.id,
                    "title": recipe.title,
                    "score": float(score),
                    "reason_text": reason_text,
                },
            }
        )
