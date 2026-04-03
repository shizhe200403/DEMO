from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ("order_no", "user", "plan_type", "amount", "status", "trade_no", "plan_end", "created_at")
    list_filter   = ("status", "plan_type")
    search_fields = ("order_no", "trade_no", "user__username")
    readonly_fields = ("order_no", "trade_no", "plan_start", "plan_end", "created_at", "updated_at")
    ordering      = ("-created_at",)
