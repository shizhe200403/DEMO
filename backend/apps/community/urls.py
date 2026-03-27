from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CommentModerationViewSet, ContentReportViewSet, PostViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"content-reports", ContentReportViewSet, basename="content-report")

urlpatterns = router.urls + [
    path("comments/<int:pk>/", CommentModerationViewSet.as_view({"delete": "destroy"}), name="comment-hide"),
]
