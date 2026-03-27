from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import lookup_openfoodfacts_barcode, search_edamam_recipes, search_nutritionix, search_usda


class ExternalProxyEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = serializers.JSONField()


class USDAProxyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name="q", location=OpenApiParameter.QUERY, required=True, type=OpenApiTypes.STR)],
        responses=ExternalProxyEnvelopeSerializer,
    )
    def get(self, request):
        query = request.query_params.get("q", "")
        if not query:
            return Response({"code": 400, "message": "query required", "data": None}, status=400)
        return Response({"code": 0, "message": "success", "data": search_usda(query)})


class NutritionixProxyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name="q", location=OpenApiParameter.QUERY, required=True, type=OpenApiTypes.STR)],
        responses=ExternalProxyEnvelopeSerializer,
    )
    def get(self, request):
        query = request.query_params.get("q", "")
        if not query:
            return Response({"code": 400, "message": "query required", "data": None}, status=400)
        return Response({"code": 0, "message": "success", "data": search_nutritionix(query)})


class EdamamProxyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name="q", location=OpenApiParameter.QUERY, required=True, type=OpenApiTypes.STR)],
        responses=ExternalProxyEnvelopeSerializer,
    )
    def get(self, request):
        query = request.query_params.get("q", "")
        if not query:
            return Response({"code": 400, "message": "query required", "data": None}, status=400)
        return Response({"code": 0, "message": "success", "data": search_edamam_recipes(query)})


class OpenFoodFactsBarcodeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name="code", location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.STR)],
        responses=ExternalProxyEnvelopeSerializer,
    )
    def get(self, request, code):
        if not code:
            return Response({"code": 400, "message": "barcode required", "data": None}, status=400)
        return Response({"code": 0, "message": "success", "data": lookup_openfoodfacts_barcode(code)})
