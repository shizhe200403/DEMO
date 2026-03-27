from rest_framework import serializers

from .models import ContentReport, Post, PostComment


class PostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ["id", "user", "content", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at", "user"]


class PostSerializer(serializers.ModelSerializer):
    comments = PostCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "user", "title", "content", "cover_image_url", "status", "audit_status", "comments", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "audit_status", "created_at", "updated_at", "comments"]

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
