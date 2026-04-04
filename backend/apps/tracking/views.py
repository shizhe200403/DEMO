from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.views import EnvelopeModelViewSet
from .models import HealthGoal, HealthGoalProgress, MealRecord, MealRecordItem
from .services import build_meal_statistics, build_meal_summary
from .serializers import HealthGoalProgressSerializer, HealthGoalSerializer, MealRecordSerializer, UserBehaviorSerializer


class OwnObjectPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class MealRecordViewSet(EnvelopeModelViewSet):
    queryset = MealRecord.objects.none()
    serializer_class = MealRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return MealRecord.objects.none()
        return MealRecord.objects.filter(user=self.request.user).prefetch_related("items", "items__recipe")

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        period = request.query_params.get("period", "week")
        end_date = timezone.localdate()
        if period == "month":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)

        data = build_meal_statistics(request.user, start_date, end_date)
        summary = build_meal_summary(request.user, start_date, end_date)
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
                    "summary": summary,
                    "trend": data,
                },
            }
        )

    @action(detail=False, methods=["get"])
    def trend(self, request):
        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=14)
        data = build_meal_statistics(request.user, start_date, end_date)
        return Response({"code": 0, "message": "success", "data": data})

    @action(detail=False, methods=["post"], url_path="copy-yesterday")
    def copy_yesterday(self, request):
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        yesterday_records = MealRecord.objects.filter(
            user=request.user, record_date=yesterday
        ).prefetch_related("items", "items__recipe")

        if not yesterday_records.exists():
            return Response(
                {"code": 1, "message": "昨日没有饮食记录，无法复制"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_ids = []
        for old_record in yesterday_records:
            new_record, created = MealRecord.objects.get_or_create(
                user=request.user,
                record_date=today,
                meal_type=old_record.meal_type,
                defaults={"source_type": "copy_yesterday", "note": old_record.note or ""},
            )
            if not created:
                # 今日该餐次已有记录，跳过
                continue
            for item in old_record.items.all():
                MealRecordItem.objects.create(
                    meal_record=new_record,
                    recipe=item.recipe,
                    ingredient_name_snapshot=item.ingredient_name_snapshot,
                    amount=item.amount,
                    unit=item.unit,
                    energy=item.energy,
                    protein=item.protein,
                    fat=item.fat,
                    carbohydrate=item.carbohydrate,
                )
            created_ids.append(new_record.id)

        if not created_ids:
            return Response(
                {"code": 1, "message": "今日对应餐次已有记录，未重复复制"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_records = MealRecord.objects.filter(id__in=created_ids).prefetch_related("items", "items__recipe")
        serializer = self.get_serializer(new_records, many=True)
        return Response({"code": 0, "message": f"已复制 {len(created_ids)} 个餐次", "data": serializer.data})


class HealthGoalViewSet(EnvelopeModelViewSet):
    queryset = HealthGoal.objects.none()
    serializer_class = HealthGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return HealthGoal.objects.none()
        return HealthGoal.objects.filter(user=self.request.user).prefetch_related("progress_records")

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=["get", "post"])
    def progress(self, request, pk=None):
        goal = self.get_object()
        if request.method.lower() == "get":
            serializer = HealthGoalProgressSerializer(goal.progress_records.all(), many=True)
            return Response({"code": 0, "message": "success", "data": serializer.data})

        serializer = HealthGoalProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        progress = HealthGoalProgress.objects.create(health_goal=goal, **serializer.validated_data)
        goal.current_value = progress.progress_value if progress.progress_value is not None else goal.current_value
        goal.save(update_fields=["current_value", "updated_at"])
        return Response({"code": 0, "message": "success", "data": HealthGoalProgressSerializer(progress).data}, status=status.HTTP_201_CREATED)


class UserBehaviorTrackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=UserBehaviorSerializer,
        responses=inline_serializer(
            name="EnvelopeUserBehaviorSerializer",
            fields={
                "code": serializers.IntegerField(),
                "message": serializers.CharField(),
                "data": UserBehaviorSerializer(),
            },
        ),
    )
    def post(self, request):
        serializer = UserBehaviorSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        behavior = serializer.save()
        # 行为变化后异步刷新该用户推荐缓存
        try:
            from apps.recommendation.tasks import precompute_single_user_recommendations
            precompute_single_user_recommendations.delay(request.user.pk)
        except Exception:
            pass  # 任务队列不可用时不影响主流程
        return Response({"code": 0, "message": "success", "data": UserBehaviorSerializer(behavior).data}, status=status.HTTP_201_CREATED)
