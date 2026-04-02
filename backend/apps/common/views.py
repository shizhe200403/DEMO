from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AdminOperationLog
from .models import UserNotification
from .operation_logs import IsAdminOperatorPermission


class HealthCheckDataSerializer(serializers.Serializer):
    status = serializers.CharField()


class HealthCheckResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = HealthCheckDataSerializer()


class UserNotificationActorSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    username = serializers.CharField(allow_blank=True)
    nickname = serializers.CharField(allow_blank=True)
    display_name = serializers.CharField(allow_blank=True)
    avatar_url = serializers.CharField(allow_blank=True)


class UserNotificationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    notification_type = serializers.CharField()
    title = serializers.CharField()
    body = serializers.CharField()
    link_path = serializers.CharField()
    metadata = serializers.JSONField()
    created_at = serializers.DateTimeField()
    read_at = serializers.DateTimeField(allow_null=True)
    actor = UserNotificationActorSerializer(allow_null=True)


class UserNotificationEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="UserNotificationListData",
        fields={
            "unread_count": serializers.IntegerField(),
            "items": UserNotificationSerializer(many=True),
        },
    )


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses=HealthCheckResponseSerializer)
    def get(self, request):
        return Response({"code": 0, "message": "success", "data": {"status": "ok"}})


class UserNotificationListView(APIView):
    def get(self, request):
        queryset = UserNotification.objects.select_related("actor").filter(user=request.user).order_by("-created_at", "-id")[:12]
        unread_count = UserNotification.objects.filter(user=request.user, read_at__isnull=True).count()
        items = [
            {
                "id": item.id,
                "notification_type": item.notification_type,
                "title": item.title,
                "body": item.body,
                "link_path": item.link_path,
                "metadata": item.metadata,
                "created_at": item.created_at,
                "read_at": item.read_at,
                "actor": {
                    "id": item.actor_id,
                    "username": item.actor.username if item.actor else "",
                    "nickname": item.actor.nickname if item.actor else "",
                    "display_name": (item.actor.nickname or item.actor.username) if item.actor else "",
                    "avatar_url": item.actor.avatar_url if item.actor else "",
                } if item.actor_id else None,
            }
            for item in queryset
        ]
        return Response({"code": 0, "message": "success", "data": {"unread_count": unread_count, "items": items}})


class UserNotificationReadView(APIView):
    def post(self, request, notification_id):
        notification = UserNotification.objects.filter(id=notification_id, user=request.user).first()
        if notification is None:
            return Response({"code": 404, "message": "not found", "data": None}, status=404)
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at", "updated_at"])
        return Response({"code": 0, "message": "success", "data": {"read": True}})


class UserNotificationReadAllView(APIView):
    def post(self, request):
        UserNotification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now(), updated_at=timezone.now())
        return Response({"code": 0, "message": "success", "data": {"read_all": True}})


class AdminOperationLogActorSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    username = serializers.CharField(allow_blank=True)
    nickname = serializers.CharField(allow_blank=True)
    display_name = serializers.CharField(allow_blank=True)


class AdminOperationLogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    module = serializers.CharField()
    action = serializers.CharField()
    target_type = serializers.CharField(allow_blank=True)
    target_id = serializers.IntegerField(allow_null=True)
    target_label = serializers.CharField(allow_blank=True)
    summary = serializers.CharField()
    changes = serializers.JSONField()
    metadata = serializers.JSONField()
    created_at = serializers.DateTimeField()
    actor = AdminOperationLogActorSerializer()


class AdminOperationLogSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    today_total = serializers.IntegerField()
    unique_operators = serializers.IntegerField()
    user_actions = serializers.IntegerField()
    recipe_actions = serializers.IntegerField()
    community_actions = serializers.IntegerField()
    report_actions = serializers.IntegerField()


class AdminOperationLogEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminOperationLogListData",
        fields={
            "count": serializers.IntegerField(),
            "next": serializers.CharField(allow_null=True),
            "previous": serializers.CharField(allow_null=True),
            "summary": AdminOperationLogSummarySerializer(),
            "items": AdminOperationLogSerializer(many=True),
        },
    )


class AdminOperationLogPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "summary": getattr(self, "summary", {}),
                    "items": data,
                },
            }
        )


class AdminOperationLogListView(APIView):
    permission_classes = [IsAdminOperatorPermission]
    pagination_class = AdminOperationLogPagination

    @extend_schema(responses=AdminOperationLogEnvelopeSerializer)
    def get(self, request):
        queryset = AdminOperationLog.objects.select_related("actor").order_by("-created_at", "-id")

        module = request.query_params.get("module", "").strip()
        keyword = request.query_params.get("keyword", "").strip()
        actor = request.query_params.get("actor", "").strip()
        target_type = request.query_params.get("target_type", "").strip()
        target_id = request.query_params.get("target_id", "").strip()
        related_target_type = request.query_params.get("related_target_type", "").strip()
        related_target_id = request.query_params.get("related_target_id", "").strip()

        if module:
            queryset = queryset.filter(module=module)
        if keyword:
            queryset = queryset.filter(Q(summary__icontains=keyword) | Q(target_label__icontains=keyword))
        if actor:
            queryset = queryset.filter(
                Q(actor__username__icontains=actor)
                | Q(actor__nickname__icontains=actor)
            )
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if target_id:
            try:
                queryset = queryset.filter(target_id=int(target_id))
            except ValueError:
                queryset = queryset.none()
        if related_target_type and related_target_id:
            try:
                related_target_id_value = int(related_target_id)
                queryset = queryset.filter(
                    Q(target_type=related_target_type, target_id=related_target_id_value)
                    | Q(metadata__related_target_type=related_target_type, metadata__related_target_id=related_target_id_value)
                )
            except ValueError:
                queryset = queryset.none()

        today = timezone.localdate()
        summary = {
            "total": queryset.count(),
            "today_total": queryset.filter(created_at__date=today).count(),
            "unique_operators": queryset.exclude(actor=None).values("actor_id").distinct().count(),
            "user_actions": queryset.filter(module="users").count(),
            "recipe_actions": queryset.filter(module="recipes").count(),
            "community_actions": queryset.filter(module="community").count(),
            "report_actions": queryset.filter(module="reports").count(),
        }

        paginator = self.pagination_class()
        paginator.summary = summary
        page = paginator.paginate_queryset(queryset, request, view=self)
        items = [
            {
                "id": log.id,
                "module": log.module,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "target_label": log.target_label,
                "summary": log.summary,
                "changes": log.changes,
                "metadata": log.metadata,
                "created_at": log.created_at,
                "actor": {
                    "id": log.actor_id,
                    "username": log.actor.username if log.actor else "",
                    "nickname": log.actor.nickname if log.actor else "",
                    "display_name": (log.actor.nickname or log.actor.username) if log.actor else "",
                },
            }
            for log in page
        ]
        return paginator.get_paginated_response(items)


class EnvelopeModelViewSet(viewsets.ModelViewSet):
    def success_response(self, data, http_status=status.HTTP_200_OK):
        return Response({"code": 0, "message": "success", "data": data}, status=http_status)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginator = self.paginator
            return self.success_response(
                {
                    "items": serializer.data,
                    "page": paginator.page.number,
                    "page_size": paginator.get_page_size(request) or len(serializer.data),
                    "total": paginator.page.paginator.count,
                }
            )

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({"code": 0, "message": "success", "data": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return self.success_response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success_response({"deleted": True})
