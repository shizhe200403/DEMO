from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import permissions, status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.community.models import ContentReport, Post, PostComment
from apps.recipes.models import Recipe
from apps.tracking.models import MealRecord
from .models import ReportTask
from .services import build_report_dashboard, generate_pdf_report, report_period

User = get_user_model()


class ReportPayloadSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    file_url = serializers.CharField(allow_blank=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class EnvelopeReportPayloadSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ReportPayloadSerializer()


class ExportReportRequestSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=["weekly", "monthly"], required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class ReportTaskDataSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    report_type = serializers.CharField()
    status = serializers.CharField()
    file_url = serializers.CharField(allow_blank=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    generated_at = serializers.DateTimeField(allow_null=True)


class EnvelopeReportTaskSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ReportTaskDataSerializer()


class EnvelopeReportTaskListSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ReportTaskDataSerializer(many=True)


class ReportDashboardDataSerializer(serializers.Serializer):
    generated_at = serializers.DateTimeField()
    targets = serializers.JSONField()
    period_overview = serializers.JSONField()
    headline_cards = serializers.JSONField()
    charts = serializers.JSONField()
    goals = serializers.JSONField()
    report_assets = serializers.JSONField()
    insights = serializers.JSONField()


class EnvelopeReportDashboardSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ReportDashboardDataSerializer()


class AdminUserMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    nickname = serializers.CharField(allow_blank=True)
    display_name = serializers.CharField()


class AdminRecentReportTaskSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    report_type = serializers.CharField()
    status = serializers.CharField()
    file_url = serializers.CharField(allow_blank=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    generated_at = serializers.DateTimeField(allow_null=True)
    user = AdminUserMiniSerializer()


class AdminWorkbenchLinkSerializer(serializers.Serializer):
    path = serializers.CharField()
    query = serializers.JSONField(default=dict)


class AdminQueueSummarySerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    count = serializers.IntegerField()
    tone = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    link = AdminWorkbenchLinkSerializer()


class AdminRecentWorkItemSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    tone = serializers.CharField()
    created_at = serializers.DateTimeField(allow_null=True)
    link = AdminWorkbenchLinkSerializer()


class AdminOperationsSummarySerializer(serializers.Serializer):
    users_total = serializers.IntegerField()
    users_active = serializers.IntegerField()
    users_pending = serializers.IntegerField()
    recipes_total = serializers.IntegerField()
    recipes_pending = serializers.IntegerField()
    recipes_rejected = serializers.IntegerField()
    posts_total = serializers.IntegerField()
    posts_pending = serializers.IntegerField()
    posts_rejected = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    hidden_comments = serializers.IntegerField()
    meal_records_last_7_days = serializers.IntegerField()
    active_record_users_last_7_days = serializers.IntegerField()
    report_tasks_total = serializers.IntegerField()
    report_tasks_processing = serializers.IntegerField()
    report_tasks_failed = serializers.IntegerField()
    report_tasks_completed = serializers.IntegerField()


class AdminOperationsOverviewSerializer(serializers.Serializer):
    summary = AdminOperationsSummarySerializer()
    queue_summaries = AdminQueueSummarySerializer(many=True)
    recent_work_items = AdminRecentWorkItemSerializer(many=True)
    recent_tasks = AdminRecentReportTaskSerializer(many=True)


class EnvelopeAdminOperationsOverviewSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = AdminOperationsOverviewSerializer()


class IsAdminOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, "role", "") in {"admin", "auditor"}))


def _build_report_response(user, report_type, start_date, end_date):
    task = ReportTask.objects.create(user=user, report_type=report_type, status="processing", start_date=start_date, end_date=end_date)
    try:
        file_path = generate_pdf_report(user, report_type, start_date, end_date)
        task.status = "completed"
        task.file_url = f"/media/reports/{file_path.name}"
        task.generated_at = timezone.now()
        task.save(update_fields=["status", "file_url", "generated_at", "updated_at"])
        return {
            "task_id": task.id,
            "file_url": task.file_url,
            "start_date": start_date,
            "end_date": end_date,
        }
    except Exception:
        task.status = "failed"
        task.save(update_fields=["status", "updated_at"])
        raise


def _user_display_name(user):
    return user.nickname or user.username


def _short_text(value, limit=46):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1]}…"


def _link(path, **query):
    return {
        "path": path,
        "query": {key: value for key, value in query.items() if value not in {None, ""}},
    }


class WeeklyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=EnvelopeReportPayloadSerializer)
    def get(self, request):
        try:
            start_date, end_date = report_period("weekly")
            return Response({"code": 0, "message": "success", "data": _build_report_response(request.user, "weekly", start_date, end_date)})
        except Exception:
            return Response({"code": 500, "message": "report generation failed", "data": None}, status=500)


class MonthlyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=EnvelopeReportPayloadSerializer)
    def get(self, request):
        try:
            start_date, end_date = report_period("monthly")
            return Response({"code": 0, "message": "success", "data": _build_report_response(request.user, "monthly", start_date, end_date)})
        except Exception:
            return Response({"code": 500, "message": "report generation failed", "data": None}, status=500)


class ExportReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ExportReportRequestSerializer, responses=EnvelopeReportPayloadSerializer)
    def post(self, request):
        report_type = request.data.get("report_type", "weekly")
        if report_type not in {"weekly", "monthly"}:
            report_type = "weekly"
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        if not start_date or not end_date:
            start_date, end_date = report_period(report_type)
        else:
            try:
                start_date = date.fromisoformat(str(start_date))
                end_date = date.fromisoformat(str(end_date))
            except ValueError:
                return Response({"code": 400, "message": "invalid date format", "data": None}, status=400)
        try:
            data = _build_report_response(request.user, report_type, start_date, end_date)
            return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_201_CREATED)
        except Exception:
            return Response({"code": 500, "message": "report generation failed", "data": None}, status=500)


class ReportTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name="task_id", location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT)],
        responses=EnvelopeReportTaskSerializer,
    )
    def get(self, request, task_id):
        task = ReportTask.objects.filter(id=task_id, user=request.user).first()
        if task is None:
            return Response({"code": 404, "message": "not found", "data": None}, status=404)
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "task_id": task.id,
                    "report_type": task.report_type,
                    "status": task.status,
                    "file_url": task.file_url,
                    "start_date": task.start_date,
                    "end_date": task.end_date,
                    "generated_at": task.generated_at,
                },
            }
        )


class ReportTaskListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=EnvelopeReportTaskListSerializer)
    def get(self, request):
        tasks = ReportTask.objects.filter(user=request.user).order_by("-created_at")[:10]
        data = [
            {
                "task_id": task.id,
                "report_type": task.report_type,
                "status": task.status,
                "file_url": task.file_url,
                "start_date": task.start_date,
                "end_date": task.end_date,
                "generated_at": task.generated_at,
            }
            for task in tasks
        ]
        return Response({"code": 0, "message": "success", "data": data})


class ReportDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=EnvelopeReportDashboardSerializer)
    def get(self, request):
        return Response({"code": 0, "message": "success", "data": build_report_dashboard(request.user)})


class AdminOperationsOverviewView(APIView):
    permission_classes = [IsAdminOperator]

    @extend_schema(responses=EnvelopeAdminOperationsOverviewSerializer)
    def get(self, request):
        today = timezone.localdate()
        last_week = today - timedelta(days=6)

        pending_users_qs = User.objects.filter(status="pending").order_by("-date_joined", "-id")
        pending_recipes_qs = Recipe.objects.exclude(status="archived").filter(audit_status="pending").order_by("-updated_at", "-id")
        rejected_recipes_count = Recipe.objects.exclude(status="archived").filter(audit_status="rejected").count()
        pending_posts_qs = Post.objects.exclude(status="archived").filter(audit_status="pending").order_by("-updated_at", "-id")
        rejected_posts_count = Post.objects.exclude(status="archived").filter(audit_status="rejected").count()
        pending_reports_qs = ContentReport.objects.filter(status="pending").order_by("-created_at", "-id")
        failed_tasks_qs = ReportTask.objects.select_related("user").filter(status="failed").order_by("-updated_at", "-id")
        recent_tasks_qs = ReportTask.objects.select_related("user").order_by("-created_at", "-id")[:8]

        recent_tasks = [
            {
                "task_id": task.id,
                "report_type": task.report_type,
                "status": task.status,
                "file_url": task.file_url,
                "start_date": task.start_date,
                "end_date": task.end_date,
                "generated_at": task.generated_at,
                "user": {
                    "id": task.user_id,
                    "username": task.user.username,
                    "nickname": task.user.nickname,
                    "display_name": _user_display_name(task.user),
                },
            }
            for task in recent_tasks_qs
        ]

        meal_record_stats = MealRecord.objects.filter(record_date__gte=last_week).aggregate(
            total=Count("id"),
            users=Count("user_id", distinct=True),
        )

        users_total = User.objects.count()
        users_active = User.objects.filter(status="active").count()
        users_pending = pending_users_qs.count()
        recipes_total = Recipe.objects.exclude(status="archived").count()
        recipes_pending = pending_recipes_qs.count()
        posts_total = Post.objects.exclude(status="archived").count()
        posts_pending = pending_posts_qs.count()
        pending_reports = pending_reports_qs.count()
        hidden_comments = PostComment.objects.filter(status="hidden").count()
        report_tasks_total = ReportTask.objects.count()
        report_tasks_processing = ReportTask.objects.filter(status="processing").count()
        report_tasks_failed = failed_tasks_qs.count()
        report_tasks_completed = ReportTask.objects.filter(status="completed").count()

        summary = {
            "users_total": users_total,
            "users_active": users_active,
            "users_pending": users_pending,
            "recipes_total": recipes_total,
            "recipes_pending": recipes_pending,
            "recipes_rejected": rejected_recipes_count,
            "posts_total": posts_total,
            "posts_pending": posts_pending,
            "posts_rejected": rejected_posts_count,
            "pending_reports": pending_reports,
            "hidden_comments": hidden_comments,
            "meal_records_last_7_days": meal_record_stats["total"] or 0,
            "active_record_users_last_7_days": meal_record_stats["users"] or 0,
            "report_tasks_total": report_tasks_total,
            "report_tasks_processing": report_tasks_processing,
            "report_tasks_failed": report_tasks_failed,
            "report_tasks_completed": report_tasks_completed,
        }

        queue_summaries = [
            {
                "key": "failed_report_tasks",
                "label": "失败报表任务",
                "count": report_tasks_failed,
                "tone": "risk",
                "title": "先处理报表失败任务",
                "description": "失败任务会直接影响复盘链路稳定性，最好先确认是数据问题还是生成链路问题。",
                "link": _link("/ops/reports"),
            },
            {
                "key": "pending_reports",
                "label": "待处理举报",
                "count": pending_reports,
                "tone": "warning",
                "title": "社区举报仍在积压",
                "description": "举报积压意味着风险内容仍在暴露，适合先回到社区处理结论。",
                "link": _link("/ops/community", preset="pending_reports", report_status="pending"),
            },
            {
                "key": "pending_posts",
                "label": "待审核帖子",
                "count": posts_pending,
                "tone": "warning",
                "title": "帖子审核队列待清理",
                "description": "先给帖子补齐审核结论，避免社区内容长期停在半开放状态。",
                "link": _link("/ops/community", preset="pending_posts", post_audit_status="pending"),
            },
            {
                "key": "pending_recipes",
                "label": "待审核菜谱",
                "count": recipes_pending,
                "tone": "warning",
                "title": "菜谱审核还没压平",
                "description": "这批菜谱更适合直接落到待审核视角处理，而不是停留在概览页。",
                "link": _link("/ops/recipes", preset="pending", audit_status="pending"),
            },
            {
                "key": "pending_users",
                "label": "待处理账号",
                "count": users_pending,
                "tone": "info",
                "title": "账号队列需要人工确认",
                "description": "待处理账号通常意味着资料缺口或状态异常，适合 manager 先处理。",
                "link": _link("/ops/users", preset="pending", status="pending"),
            },
        ]

        recent_work_items = []

        for task in failed_tasks_qs[:2]:
            recent_work_items.append(
                {
                    "key": f"failed-task-{task.id}",
                    "label": "失败报表",
                    "title": f"{_user_display_name(task.user)} 的{task.get_report_type_display() or task.report_type}生成失败",
                    "description": "先检查最近失败任务，确认是生成链路异常还是数据侧问题。",
                    "tone": "risk",
                    "created_at": task.updated_at,
                    "link": _link("/ops/reports"),
                }
            )

        for report in pending_reports_qs[:2]:
            recent_work_items.append(
                {
                    "key": f"pending-report-{report.id}",
                    "label": "待处理举报",
                    "title": f"举报 #{report.id} 仍待处理",
                    "description": f"{_short_text(report.reason, 40)}，建议直接进入举报队列给出处理结论。",
                    "tone": "warning",
                    "created_at": report.created_at,
                    "link": _link("/ops/community", preset="pending_reports", report_status="pending"),
                }
            )

        for post in pending_posts_qs[:2]:
            recent_work_items.append(
                {
                    "key": f"pending-post-{post.id}",
                    "label": "待审核帖子",
                    "title": _short_text(post.title or f"帖子 #{post.id}", 36),
                    "description": "帖子仍是待审核状态，适合直接落到社区页完成审核结论。",
                    "tone": "warning",
                    "created_at": post.updated_at,
                    "link": _link("/ops/community", preset="pending_posts", post_audit_status="pending"),
                }
            )

        for recipe in pending_recipes_qs[:2]:
            recent_work_items.append(
                {
                    "key": f"pending-recipe-{recipe.id}",
                    "label": "待审核菜谱",
                    "title": _short_text(recipe.title or f"菜谱 #{recipe.id}", 36),
                    "description": "菜谱还没完成审核，建议直接进入待审核视角处理。",
                    "tone": "warning",
                    "created_at": recipe.updated_at,
                    "link": _link("/ops/recipes", preset="pending", audit_status="pending"),
                }
            )

        for user in pending_users_qs[:2]:
            recent_work_items.append(
                {
                    "key": f"pending-user-{user.id}",
                    "label": "待处理账号",
                    "title": _user_display_name(user),
                    "description": "账号仍在待处理状态，适合直接进入用户队列确认资料或状态。",
                    "tone": "info",
                    "created_at": user.date_joined,
                    "link": _link("/ops/users", preset="pending", status="pending"),
                }
            )

        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "summary": summary,
                    "queue_summaries": queue_summaries,
                    "recent_work_items": recent_work_items[:8],
                    "recent_tasks": recent_tasks,
                },
            }
        )
