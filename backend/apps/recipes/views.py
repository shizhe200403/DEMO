from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.operation_logs import build_change_entries, create_admin_operation_log, is_admin_operator, snapshot_model_fields
from apps.common.views import EnvelopeModelViewSet
from .bootstrap import ensure_builtin_recipes
from .models import Ingredient, Recipe, UserFavoriteRecipe
from .serializers import IngredientSerializer, RecipeSerializer
from .utils import get_recipe_nutrition_summary
from apps.tracking.models import UserBehavior


RECIPE_BULK_FIELD_LABELS = {
    "status": "发布状态",
    "audit_status": "审核结论",
}


class RecipeBulkRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    action = serializers.ChoiceField(choices=[("approve", "approve"), ("reject", "reject"), ("archive", "archive")])


class RecipeBulkResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="RecipeBulkData",
        fields={
            "updated_count": serializers.IntegerField(),
            "ids": serializers.ListField(child=serializers.IntegerField()),
            "action": serializers.CharField(),
        },
    )


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
        if is_admin_operator(request.user):
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
        if not is_admin_operator(self.request.user):
            raise PermissionDenied("只有管理员或审核员可以维护食材库")
        return [permission() for permission in self.permission_classes]




class RecipeBulkActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not is_admin_operator(request.user):
            raise PermissionDenied("只有管理员或审核员可以批量处理菜谱")
        serializer = RecipeBulkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = list(dict.fromkeys(serializer.validated_data["ids"]))
        action_name = serializer.validated_data["action"]
        recipes = list(Recipe.objects.filter(id__in=ids).order_by("id"))
        found_ids = [recipe.id for recipe in recipes]

        for recipe in recipes:
            before = snapshot_model_fields(recipe, ["status", "audit_status"])
            if action_name == "approve":
                recipe.audit_status = "approved"
                recipe.status = "published"
            elif action_name == "reject":
                recipe.audit_status = "rejected"
            else:
                recipe.status = "archived"
            recipe.save(update_fields=["status", "audit_status", "updated_at"])
            create_admin_operation_log(
                actor=request.user,
                module="recipes",
                action="bulk_moderate_recipe",
                target_type="recipe",
                target_id=recipe.id,
                target_label=recipe.title,
                summary=f"批量处理了菜谱《{recipe.title}》",
                changes=build_change_entries(before, snapshot_model_fields(recipe, ["status", "audit_status"]), RECIPE_BULK_FIELD_LABELS, section="菜谱处理"),
                metadata={"created_by_id": recipe.created_by_id, "bulk_action": action_name},
            )

        create_admin_operation_log(
            actor=request.user,
            module="recipes",
            action="bulk_moderate_recipe",
            target_type="recipe_batch",
            target_label=f"{len(found_ids)} 份菜谱",
            summary=f"批量执行菜谱{action_name}，共处理 {len(found_ids)} 份",
            metadata={"ids": found_ids, "requested_ids": ids, "action": action_name},
        )
        return Response(
            {"code": 0, "message": "success", "data": {"updated_count": len(found_ids), "ids": found_ids, "action": action_name}},
            status=status.HTTP_200_OK,
        )


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

        if is_admin_operator(user):
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
        fields = list(serializer.validated_data.keys())
        before = snapshot_model_fields(instance, fields)
        serializer.save()
        if is_admin_operator(self.request.user):
            create_admin_operation_log(
                actor=self.request.user,
                module="recipes",
                action="update_recipe",
                target_type="recipe",
                target_id=instance.id,
                target_label=instance.title,
                summary=f"更新了菜谱《{instance.title}》的内容与审核状态",
                changes=build_change_entries(
                    before,
                    snapshot_model_fields(instance, fields),
                    {
                        "title": "菜谱标题",
                        "description": "菜谱描述",
                        "portion_size": "分量说明",
                        "servings": "份数",
                        "difficulty": "难度",
                        "cook_time_minutes": "烹饪时长",
                        "prep_time_minutes": "准备时长",
                        "meal_type": "餐次",
                        "taste_tags": "口味标签",
                        "cuisine_tags": "菜系标签",
                        "status": "发布状态",
                        "source_type": "来源类型",
                        "source_name": "来源名称",
                        "audit_status": "审核结论",
                    },
                    section="菜谱处理",
                ),
                metadata={"created_by_id": instance.created_by_id},
            )

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def upload_cover(self, request, pk=None):
        recipe = self.get_object()
        if recipe.created_by != request.user and not (request.user.is_staff or request.user.is_superuser):
            return Response({"code": 1, "message": "无权限"}, status=status.HTTP_403_FORBIDDEN)
        file = request.FILES.get("cover")
        if not file:
            return Response({"code": 1, "message": "请选择图片文件"}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > 10 * 1024 * 1024:
            return Response({"code": 1, "message": "图片大小不能超过 10MB"}, status=status.HTTP_400_BAD_REQUEST)
        if not file.content_type.startswith("image/"):
            return Response({"code": 1, "message": "只支持图片格式"}, status=status.HTTP_400_BAD_REQUEST)
        import os, uuid
        from django.core.files.storage import default_storage
        ext = os.path.splitext(file.name)[1].lower() or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        path = default_storage.save(os.path.join("recipe_covers", filename), file)
        cover_image_url = f"/media/{path}"
        recipe.cover_image_url = cover_image_url
        recipe.save(update_fields=["cover_image_url"])
        return Response({"code": 0, "message": "封面已更新", "cover_image_url": cover_image_url})

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
        before = snapshot_model_fields(instance, ["status"])
        instance.status = "archived"
        instance.save(update_fields=["status", "updated_at"])
        if is_admin_operator(request.user):
            create_admin_operation_log(
                actor=request.user,
                module="recipes",
                action="archive_recipe",
                target_type="recipe",
                target_id=instance.id,
                target_label=instance.title,
                summary=f"归档了菜谱《{instance.title}》",
                changes=build_change_entries(before, snapshot_model_fields(instance, ["status"]), {"status": "发布状态"}, section="菜谱处理"),
                metadata={"created_by_id": instance.created_by_id},
            )
        return Response({"code": 0, "message": "success", "data": {"archived": True}}, status=status.HTTP_200_OK)
