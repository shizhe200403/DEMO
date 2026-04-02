from django.utils import timezone
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from apps.common.operation_logs import (
    IsAdminOperatorPermission,
    build_change_entries,
    create_admin_operation_log,
    is_admin_operator,
    snapshot_model_fields,
)
from apps.common.views import EnvelopeModelViewSet
from .models import ContentReport, Post, PostComment, PostLike, CommentLike
from .serializers import (
    AdminContentReportDetailSerializer,
    AdminContentReportListSerializer,
    AdminContentReportUpdateSerializer,
    AdminPostDetailSerializer,
    AdminPostListSerializer,
    AdminPostUpdateSerializer,
    ContentReportSerializer,
    PostCommentSerializer,
    PostSerializer,
)


REPORT_FIELD_LABELS = {
    "status": "举报状态",
    "priority": "优先级",
    "assigned_to": "指派处理人",
    "internal_note": "内部备注",
    "follow_up_at": "跟进时间",
    "processed_by": "处理人",
    "processed_at": "处理时间",
}
POST_FIELD_LABELS = {
    "status": "帖子状态",
    "audit_status": "审核结论",
}


def user_display(user):
    if not user:
        return None
    return user.nickname or user.username


def snapshot_report_fields(report):
    return {
        "status": report.status,
        "priority": report.priority,
        "assigned_to": user_display(report.assigned_to),
        "internal_note": report.internal_note,
        "follow_up_at": report.follow_up_at.isoformat() if report.follow_up_at else None,
        "processed_by": user_display(report.processed_by),
        "processed_at": report.processed_at.isoformat() if report.processed_at else None,
    }


class IsAdminModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return IsAdminOperatorPermission().has_permission(request, view)


class AdminPostBulkRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    action = serializers.ChoiceField(choices=[("approve", "approve"), ("reject", "reject"), ("archive", "archive")])


class AdminPostBulkResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminPostBulkData",
        fields={
            "updated_count": serializers.IntegerField(),
            "ids": serializers.ListField(child=serializers.IntegerField()),
            "action": serializers.CharField(),
        },
    )


class AdminReportBulkRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    action = serializers.ChoiceField(choices=[("processed", "processed"), ("rejected", "rejected")])


class AdminReportBulkResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminReportBulkData",
        fields={
            "updated_count": serializers.IntegerField(),
            "ids": serializers.ListField(child=serializers.IntegerField()),
            "action": serializers.CharField(),
        },
    )




class AdminCommunityPostBulkActionView(APIView):
    permission_classes = [IsAdminModerator]

    @transaction.atomic
    @extend_schema(request=AdminPostBulkRequestSerializer, responses=AdminPostBulkResponseSerializer)
    def post(self, request):
        serializer = AdminPostBulkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = list(dict.fromkeys(serializer.validated_data["ids"]))
        action_name = serializer.validated_data["action"]
        posts = list(Post.objects.filter(id__in=ids).order_by("id"))
        found_ids = [post.id for post in posts]

        for post in posts:
            before = snapshot_model_fields(post, ["status", "audit_status"])
            if action_name == "approve":
                post.audit_status = "approved"
                post.status = "published"
            elif action_name == "reject":
                post.audit_status = "rejected"
            else:
                post.status = "archived"
            post.save(update_fields=["status", "audit_status", "updated_at"])
            create_admin_operation_log(
                actor=request.user,
                module="community",
                action="bulk_moderate_post",
                target_type="post",
                target_id=post.id,
                target_label=post.title,
                summary=f"批量处理了帖子《{post.title}》",
                changes=build_change_entries(before, snapshot_model_fields(post, ["status", "audit_status"]), POST_FIELD_LABELS, section="帖子处理"),
                metadata={"author_id": post.user_id, "bulk_action": action_name, "related_target_type": "post", "related_target_id": post.id},
            )

        create_admin_operation_log(
            actor=request.user,
            module="community",
            action="bulk_moderate_post",
            target_type="post_batch",
            target_label=f"{len(found_ids)} 条帖子",
            summary=f"批量执行帖子{action_name}，共处理 {len(found_ids)} 条",
            metadata={"ids": found_ids, "requested_ids": ids, "action": action_name},
        )
        return Response(
            {"code": 0, "message": "success", "data": {"updated_count": len(found_ids), "ids": found_ids, "action": action_name}},
            status=status.HTTP_200_OK,
        )


class AdminCommunityReportBulkActionView(APIView):
    permission_classes = [IsAdminModerator]

    @transaction.atomic
    @extend_schema(request=AdminReportBulkRequestSerializer, responses=AdminReportBulkResponseSerializer)
    def post(self, request):
        serializer = AdminReportBulkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = list(dict.fromkeys(serializer.validated_data["ids"]))
        action_name = serializer.validated_data["action"]
        reports = list(ContentReport.objects.select_related("reporter", "processed_by", "assigned_to").filter(id__in=ids).order_by("id"))
        found_ids = [report.id for report in reports]

        for report in reports:
            before = snapshot_report_fields(report)
            report.status = action_name
            report.processed_by = request.user
            report.processed_at = timezone.now()
            report.save(update_fields=["status", "processed_by", "processed_at", "updated_at"])
            create_admin_operation_log(
                actor=request.user,
                module="community",
                action="bulk_review_report",
                target_type="content_report",
                target_id=report.id,
                target_label=f"举报 #{report.id}",
                summary=f"批量更新了举报 #{report.id} 的处理结果",
                changes=build_change_entries(before, snapshot_report_fields(report), REPORT_FIELD_LABELS, section="举报处理"),
                metadata={
                    "reporter_id": report.reporter_id,
                    "assigned_to_id": report.assigned_to_id,
                    "priority": report.priority,
                    "target_type": report.target_type,
                    "target_id": report.target_id,
                    "bulk_action": action_name,
                    "related_target_type": report.target_type,
                    "related_target_id": report.target_id,
                },
            )

        create_admin_operation_log(
            actor=request.user,
            module="community",
            action="bulk_review_report",
            target_type="content_report_batch",
            target_label=f"{len(found_ids)} 条举报",
            summary=f"批量执行举报{action_name}，共处理 {len(found_ids)} 条",
            metadata={"ids": found_ids, "requested_ids": ids, "action": action_name},
        )
        return Response(
            {"code": 0, "message": "success", "data": {"updated_count": len(found_ids), "ids": found_ids, "action": action_name}},
            status=status.HTTP_200_OK,
        )


class PostViewSet(EnvelopeModelViewSet):
    queryset = Post.objects.none()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Post.objects.none()
        user = self.request.user
        return Post.objects.select_related(
            "user", "linked_recipe"
        ).prefetch_related(
            "comments", "comments__user", "comments__likes",
            "likes",
            "linked_recipe__steps", "linked_recipe__recipe_ingredients", "linked_recipe__recipe_ingredients__ingredient",
        ).filter(
            models.Q(status="published") | models.Q(user=user)
        )

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        post = serializer.instance
        if post.user_id != self.request.user.id and not is_admin_operator(self.request.user):
            raise PermissionDenied("只有作者或管理员可以编辑帖子")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.user_id != request.user.id and not is_admin_operator(request.user):
            return Response({"code": 403, "message": "forbidden", "data": None}, status=403)
        post.status = "archived"
        post.save(update_fields=["status", "updated_at"])
        return Response({"code": 0, "message": "success", "data": {"archived": True}})

    @action(detail=True, methods=["post"])
    def comments(self, request, pk=None):
        post = self.get_object()
        serializer = PostCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = PostComment.objects.create(post=post, user=request.user, **serializer.validated_data)
        return Response({"code": 0, "message": "success", "data": PostCommentSerializer(comment).data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def report(self, request, pk=None):
        post = self.get_object()
        serializer = ContentReportSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        report = serializer.save(target_type="post", target_id=post.id)
        return Response({"code": 0, "message": "success", "data": ContentReportSerializer(report).data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def upload_cover(self, request, pk=None):
        post = self.get_object()
        if post.user_id != request.user.id:
            return Response({"code": 1, "message": "只有作者可以上传封面"}, status=status.HTTP_403_FORBIDDEN)
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
        path = default_storage.save(os.path.join("post_covers", filename), file)
        cover_image_url = f"/media/{path}"
        post.cover_image_url = cover_image_url
        post.save(update_fields=["cover_image_url"])
        return Response({"code": 0, "message": "封面已更新", "cover_image_url": cover_image_url})

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        post = self.get_object()
        like_obj, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if not created:
            like_obj.delete()
            like_count = PostLike.objects.filter(post_id=post.pk).count()
            return Response({"code": 0, "message": "success", "data": {"liked": False, "like_count": like_count}})
        like_count = PostLike.objects.filter(post_id=post.pk).count()
        return Response({"code": 0, "message": "success", "data": {"liked": True, "like_count": like_count}}, status=status.HTTP_201_CREATED)


class CommentLikeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(PostComment, id=comment_id)
        like_obj, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
        if not created:
            like_obj.delete()
            like_count = CommentLike.objects.filter(comment_id=comment.pk).count()
            return Response({"code": 0, "message": "success", "data": {"liked": False, "like_count": like_count}})
        like_count = CommentLike.objects.filter(comment_id=comment.pk).count()
        return Response({"code": 0, "message": "success", "data": {"liked": True, "like_count": like_count}}, status=status.HTTP_201_CREATED)


@extend_schema_view(
    destroy=extend_schema(
        responses=inline_serializer(
            name="EnvelopeCommentModerationSerializer",
            fields={
                "code": serializers.IntegerField(),
                "message": serializers.CharField(),
                "data": serializers.JSONField(),
            },
        )
    )
)
class CommentImageUploadView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(PostComment, id=comment_id)
        if comment.user_id != request.user.id:
            return Response({"code": 1, "message": "只有评论作者可以上传图片"}, status=status.HTTP_403_FORBIDDEN)
        file = request.FILES.get("image")
        if not file:
            return Response({"code": 1, "message": "请选择图片文件"}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > 5 * 1024 * 1024:
            return Response({"code": 1, "message": "图片大小不能超过 5MB"}, status=status.HTTP_400_BAD_REQUEST)
        if not file.content_type.startswith("image/"):
            return Response({"code": 1, "message": "只支持图片格式"}, status=status.HTTP_400_BAD_REQUEST)
        import os, uuid
        from django.core.files.storage import default_storage
        ext = os.path.splitext(file.name)[1].lower() or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        path = default_storage.save(os.path.join("comment_images", filename), file)
        image_url = f"/media/{path}"
        comment.image_url = image_url
        comment.save(update_fields=["image_url"])
        return Response({"code": 0, "message": "图片已上传", "image_url": image_url})


class CommentModerationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, pk=None):
        comment = PostComment.objects.filter(id=pk).first()
        if comment is None:
            return Response({"code": 404, "message": "not found", "data": None}, status=404)
        # 评论作者可以删除自己的评论
        if comment.user_id == request.user.id:
            comment.delete()
            return Response({"code": 0, "message": "success", "data": {"deleted": True}})
        if not is_admin_operator(request.user):
            return Response({"code": 403, "message": "forbidden", "data": None}, status=403)
        before_status = snapshot_model_fields(comment, ["status"])
        comment.status = "hidden"
        comment.save(update_fields=["status", "updated_at"])
        create_admin_operation_log(
            actor=request.user,
            module="community",
            action="hide_comment",
            target_type="comment",
            target_id=comment.id,
            target_label=f"评论 #{comment.id}",
            summary=f"隐藏了帖子《{comment.post.title}》下的一条评论",
            changes=build_change_entries(before_status, snapshot_model_fields(comment, ["status"]), {"status": "评论状态"}, section="评论处理"),
            metadata={
                "post_id": comment.post_id,
                "post_title": comment.post.title,
                "related_target_type": "post",
                "related_target_id": comment.post_id,
            },
        )
        return Response({"code": 0, "message": "success", "data": {"hidden": True}})


class ContentReportViewSet(EnvelopeModelViewSet):
    queryset = ContentReport.objects.none()
    serializer_class = ContentReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return ContentReport.objects.none()
        return ContentReport.objects.filter(reporter=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class AdminPostPagination(PageNumberPagination):
    page_size = 12
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
                    "items": data,
                },
            }
        )


class AdminContentReportPagination(AdminPostPagination):
    pass


class AdminPostListEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminPostListData",
        fields={
            "count": serializers.IntegerField(),
            "next": serializers.CharField(allow_null=True),
            "previous": serializers.CharField(allow_null=True),
            "items": AdminPostListSerializer(many=True),
        },
    )


class AdminPostDetailEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = AdminPostDetailSerializer()


class AdminContentReportListEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminContentReportListData",
        fields={
            "count": serializers.IntegerField(),
            "next": serializers.CharField(allow_null=True),
            "previous": serializers.CharField(allow_null=True),
            "items": AdminContentReportListSerializer(many=True),
        },
    )


class AdminContentReportDetailEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = AdminContentReportDetailSerializer()


class AdminCommunityPostListView(APIView):
    permission_classes = [IsAdminModerator]
    pagination_class = AdminPostPagination

    @extend_schema(responses=AdminPostListEnvelopeSerializer)
    def get(self, request):
        queryset = Post.objects.select_related("user").prefetch_related("comments").order_by("-updated_at", "-id")

        keyword = request.query_params.get("keyword", "").strip()
        status_value = request.query_params.get("status", "").strip()
        audit_status = request.query_params.get("audit_status", "").strip()
        author = request.query_params.get("author", "").strip()

        if keyword:
            queryset = queryset.filter(models.Q(title__icontains=keyword) | models.Q(content__icontains=keyword))
        if status_value:
            queryset = queryset.filter(status=status_value)
        if audit_status:
            queryset = queryset.filter(audit_status=audit_status)
        if author:
            queryset = queryset.filter(
                models.Q(user__username__icontains=author)
                | models.Q(user__nickname__icontains=author)
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AdminPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminCommunityPostDetailView(APIView):
    permission_classes = [IsAdminModerator]

    def get_object(self, post_id):
        return get_object_or_404(Post.objects.select_related("user").prefetch_related("comments__user"), pk=post_id)

    @extend_schema(responses=AdminPostDetailEnvelopeSerializer)
    def get(self, request, post_id):
        post = self.get_object(post_id)
        serializer = AdminPostDetailSerializer(post)
        return Response({"code": 0, "message": "success", "data": serializer.data})

    @extend_schema(request=AdminPostUpdateSerializer, responses=AdminPostDetailEnvelopeSerializer)
    def patch(self, request, post_id):
        post = self.get_object(post_id)
        fields = list(request.data.keys())
        before = snapshot_model_fields(post, fields)
        serializer = AdminPostUpdateSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        create_admin_operation_log(
            actor=request.user,
            module="community",
            action="moderate_post",
            target_type="post",
            target_id=post.id,
            target_label=post.title,
            summary=f"更新了帖子《{post.title}》的审核与发布状态",
            changes=build_change_entries(
                before,
                snapshot_model_fields(post, fields),
                {
                    "title": "帖子标题",
                    "content": "帖子正文",
                    "cover_image_url": "封面图",
                    "status": "帖子状态",
                    "audit_status": "审核结论",
                },
                section="帖子处理",
            ),
            metadata={
                "author_id": post.user_id,
                "related_target_type": "post",
                "related_target_id": post.id,
            },
        )
        detail = AdminPostDetailSerializer(post)
        return Response({"code": 0, "message": "success", "data": detail.data}, status=status.HTTP_200_OK)


class AdminContentReportListView(APIView):
    permission_classes = [IsAdminModerator]
    pagination_class = AdminContentReportPagination

    @extend_schema(responses=AdminContentReportListEnvelopeSerializer)
    def get(self, request):
        queryset = ContentReport.objects.select_related("reporter", "processed_by", "assigned_to").order_by("-created_at", "-id")

        keyword = request.query_params.get("keyword", "").strip()
        status_value = request.query_params.get("status", "").strip()
        target_type = request.query_params.get("target_type", "").strip()
        priority = request.query_params.get("priority", "").strip()
        assigned_to = request.query_params.get("assigned_to", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if priority:
            queryset = queryset.filter(priority=priority)
        if assigned_to == "unassigned":
            queryset = queryset.filter(assigned_to__isnull=True)
        elif assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        if keyword:
            queryset = queryset.filter(
                models.Q(reason__icontains=keyword)
                | models.Q(internal_note__icontains=keyword)
                | models.Q(reporter__username__icontains=keyword)
                | models.Q(reporter__nickname__icontains=keyword)
                | models.Q(assigned_to__username__icontains=keyword)
                | models.Q(assigned_to__nickname__icontains=keyword)
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AdminContentReportListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminContentReportDetailView(APIView):
    permission_classes = [IsAdminModerator]

    def get_object(self, report_id):
        return get_object_or_404(ContentReport.objects.select_related("reporter", "processed_by", "assigned_to"), pk=report_id)

    @extend_schema(responses=AdminContentReportDetailEnvelopeSerializer)
    def get(self, request, report_id):
        report = self.get_object(report_id)
        serializer = AdminContentReportDetailSerializer(report)
        return Response({"code": 0, "message": "success", "data": serializer.data})

    @extend_schema(request=AdminContentReportUpdateSerializer, responses=AdminContentReportDetailEnvelopeSerializer)
    def patch(self, request, report_id):
        report = self.get_object(report_id)
        before = snapshot_report_fields(report)
        serializer = AdminContentReportUpdateSerializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        status_value = serializer.validated_data.get("status", report.status)
        update_kwargs = {}
        if status_value in {"processed", "rejected"}:
            update_kwargs["processed_by"] = request.user
            update_kwargs["processed_at"] = timezone.now()
        elif "status" in serializer.validated_data and status_value == "pending":
            update_kwargs["processed_by"] = None
            update_kwargs["processed_at"] = None
        report = serializer.save(**update_kwargs)
        create_admin_operation_log(
            actor=request.user,
            module="community",
            action="review_report",
            target_type="content_report",
            target_id=report.id,
            target_label=f"举报 #{report.id}",
            summary=f"更新了举报 #{report.id} 的处理协作信息",
            changes=build_change_entries(
                before,
                snapshot_report_fields(report),
                REPORT_FIELD_LABELS,
                section="举报处理",
            ),
            metadata={
                "reporter_id": report.reporter_id,
                "assigned_to_id": report.assigned_to_id,
                "priority": report.priority,
                "target_type": report.target_type,
                "target_id": report.target_id,
                "related_target_type": report.target_type,
                "related_target_id": report.target_id,
            },
        )
        detail = AdminContentReportDetailSerializer(report)
        return Response({"code": 0, "message": "success", "data": detail.data}, status=status.HTTP_200_OK)
