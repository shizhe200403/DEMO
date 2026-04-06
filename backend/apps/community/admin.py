from django.contrib import admin

from .models import ContentReport, Post, PostComment, SensitiveWordRule

admin.site.register(Post)
admin.site.register(PostComment)
admin.site.register(ContentReport)


@admin.register(SensitiveWordRule)
class SensitiveWordRuleAdmin(admin.ModelAdmin):
    list_display = ("word", "action", "is_active", "updated_at")
    list_filter = ("action", "is_active")
    search_fields = ("word", "note")
