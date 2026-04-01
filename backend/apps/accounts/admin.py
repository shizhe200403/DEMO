from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "phone", "nickname", "role", "is_staff", "is_superuser", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "phone", "nickname")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("扩展信息", {"fields": ("phone", "nickname", "signature", "avatar_url", "role", "status")}),
    )
