from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ContentReport, Post, PostComment

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "nickname", "avatar_url", "display_name"]

    def get_display_name(self, obj):
        return obj.nickname or obj.username


class PostCommentSerializer(serializers.ModelSerializer):
    user_info = UserBriefSerializer(source="user", read_only=True)

    class Meta:
        model = PostComment
        fields = ["id", "user", "user_info", "content", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at", "user"]


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    user_info = UserBriefSerializer(source="user", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "user_info",
            "title",
            "content",
            "cover_image_url",
            "status",
            "audit_status",
            "comments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "audit_status", "created_at", "updated_at", "comments"]

    def get_comments(self, obj):
        comments = obj.comments.filter(status="visible").select_related("user")
        return PostCommentSerializer(comments, many=True).data

    def create(self, validated_data):
        return Post.objects.create(user=self.context["request"].user, **validated_data)


class ContentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentReport
        fields = ["id", "target_type", "target_id", "reason", "status", "processed_by", "processed_at", "created_at"]
        read_only_fields = ["id", "status", "processed_by", "processed_at", "created_at"]
        extra_kwargs = {
            "target_type": {"required": False},
            "target_id": {"required": False},
        }

    def create(self, validated_data):
        return ContentReport.objects.create(reporter=self.context["request"].user, **validated_data)
