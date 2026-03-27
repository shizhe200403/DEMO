from django.utils import timezone
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from apps.common.views import EnvelopeModelViewSet
from .models import ContentReport, Post, PostComment
from .serializers import ContentReportSerializer, PostCommentSerializer, PostSerializer


class PostViewSet(EnvelopeModelViewSet):
    queryset = Post.objects.none()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Post.objects.none()
        user = self.request.user
        return Post.objects.select_related("user").prefetch_related("comments", "comments__user").filter(
            models.Q(status="published") | models.Q(user=user)
        )

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        post = serializer.instance
        if post.user_id != self.request.user.id and getattr(self.request.user, "role", "") not in {"admin", "auditor"}:
            raise PermissionDenied("只有作者或管理员可以编辑帖子")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.user_id != request.user.id and getattr(request.user, "role", "") not in {"admin", "auditor"}:
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
class CommentModerationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, pk=None):
        if getattr(request.user, "role", "") not in {"admin", "auditor"}:
            return Response({"code": 403, "message": "forbidden", "data": None}, status=403)
        comment = PostComment.objects.filter(id=pk).first()
        if comment is None:
            return Response({"code": 404, "message": "not found", "data": None}, status=404)
        comment.status = "hidden"
        comment.save(update_fields=["status", "updated_at"])
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
