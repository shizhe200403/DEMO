from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import AdminUserBulkActionView, AdminUserDetailView, AdminUserListView, AvatarUploadView, ChangePasswordView, DeleteAccountView, FullProfileView, GetSecurityQuestionView, HealthConditionView, LoginView, MeView, ProfileView, RegisterView, ResetPasswordBySecurityView, SecurityQuestionListView, SetSecurityQuestionView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("me/profile/", ProfileView.as_view(), name="me-profile"),
    path("me/health-condition/", HealthConditionView.as_view(), name="me-health-condition"),
    path("me/full-profile/", FullProfileView.as_view(), name="me-full-profile"),
    path("me/change-password/", ChangePasswordView.as_view(), name="me-change-password"),
    path("me/delete/", DeleteAccountView.as_view(), name="me-delete"),
    path("me/avatar/", AvatarUploadView.as_view(), name="me-avatar"),
    path("me/security-question/", SetSecurityQuestionView.as_view(), name="me-security-question"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("security-questions/", SecurityQuestionListView.as_view(), name="security-questions"),
    path("get-security-question/", GetSecurityQuestionView.as_view(), name="get-security-question"),
    path("reset-password/", ResetPasswordBySecurityView.as_view(), name="reset-password"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/bulk/", AdminUserBulkActionView.as_view(), name="admin-user-bulk"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
]
