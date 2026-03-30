from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.views import EnvelopeModelViewSet
from .bootstrap import ensure_builtin_recipes
from .models import Ingredient, Recipe, UserFavoriteRecipe
from .serializers import IngredientSerializer, RecipeSerializer
from .utils import get_recipe_nutrition_summary
from apps.tracking.models import UserBehavior


class CanManageContent(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, "role", "") in {"admin", "auditor"}:
            return True
        return getattr(obj, "created_by_id", None) == request.user.id


class IngredientViewSet(EnvelopeModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [CanManageContent]
    search_fields = ["canonical_name", "category"]
    ordering_fields = ["canonical_name", "created_at"]

    def get_permissions(self):
        if getattr(self, "swagger_fake_view", False):
            return [permission() for permission in self.permission_classes]
        if self.request.method in permissions.SAFE_METHODS:
            return [permission() for permission in self.permission_classes]
        if getattr(self.request.user, "role", "") not in {"admin", "auditor"}:
            raise PermissionDenied("只有管理员或审核员可以维护食材库")
        return [permission() for permission in self.permission_classes]


class RecipeViewSet(EnvelopeModelViewSet):
    queryset = (
        Recipe.objects.select_related("created_by", "nutrition_summary")
        .prefetch_related("steps", "recipe_ingredients__ingredient")
        .all()
    )
    serializer_class = RecipeSerializer
    permission_classes = [CanManageContent]
    search_fields = ["title", "description", "meal_type", "taste_tags", "cuisine_tags"]
    ordering_fields = ["created_at", "updated_at", "cook_time_minutes"]

    def get_queryset(self):
        ensure_builtin_recipes()
        queryset = super().get_queryset().exclude(status="archived")
        user = self.request.user

        if user.is_authenticated and getattr(user, "role", "") in {"admin", "auditor"}:
            return queryset

        public_filter = Q(status="published", audit_status="approved")
        if user.is_authenticated:
            return queryset.filter(public_filter | Q(created_by=user)).distinct()
        return queryset.filter(public_filter)

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user if self.request.user.is_authenticated else None,
            status="published",
            audit_status="approved",
            source_type="user_upload",
            source_name="manual",
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        self.check_object_permissions(self.request, instance)
        serializer.save()

    @action(detail=True, methods=["get"])
    def nutrition(self, request, pk=None):
        recipe = self.get_object()
        summary = get_recipe_nutrition_summary(recipe)
        if summary is None:
            return Response({"code": 0, "message": "success", "data": None})
        return Response({"code": 0, "message": "success", "data": RecipeSerializer(recipe).data["nutrition_summary"]})

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        UserFavoriteRecipe.objects.get_or_create(user=request.user, recipe=recipe)
        UserBehavior.objects.create(user=request.user, recipe=recipe, behavior_type="favorite", context_scene="recipe")
        return Response({"code": 0, "message": "success", "data": {"favorited": True}}, status=status.HTTP_200_OK)

    @favorite.mapping.delete
    def unfavorite(self, request, pk=None):
        recipe = self.get_object()
        UserFavoriteRecipe.objects.filter(user=request.user, recipe=recipe).delete()
        return Response({"code": 0, "message": "success", "data": {"favorited": False}}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def favorites(self, request):
        queryset = (
            Recipe.objects.select_related("created_by", "nutrition_summary")
            .prefetch_related("steps", "recipe_ingredients__ingredient")
            .exclude(status="archived")
            .filter(favorited_by__user=request.user)
            .distinct()
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response({"code": 0, "message": "success", "data": serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.status = "archived"
        instance.save(update_fields=["status", "updated_at"])
        return Response({"code": 0, "message": "success", "data": {"archived": True}}, status=status.HTTP_200_OK)
