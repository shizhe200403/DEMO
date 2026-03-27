from django.contrib import admin

from .models import ContentReport, Post, PostComment

admin.site.register(Post)
admin.site.register(PostComment)
admin.site.register(ContentReport)

