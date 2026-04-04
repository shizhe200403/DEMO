import uuid

from django.conf import settings
from django.db import models


class Order(models.Model):
    """
    Pro 升级订单。每次用户发起升级创建一条记录。
    支付成功后异步通知（notify）和同步跳转（return）均更新该记录并升级 plan。
    """

    PLAN_CHOICES = [
        ("monthly", "月度套餐 ¥25"),
        ("annual",  "年度套餐 ¥199"),
    ]
    STATUS_CHOICES = [
        ("pending",   "待支付"),
        ("paid",      "已支付"),
        ("expired",   "已到期"),
        ("cancelled", "已取消"),
        ("refunded",  "已退款"),
    ]

    order_no    = models.CharField(max_length=64, unique=True, db_index=True)
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="orders",
    )
    plan_type   = models.CharField(max_length=16, choices=PLAN_CHOICES, default="monthly")
    amount      = models.DecimalField(max_digits=8, decimal_places=2)
    status      = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")

    # 支付宝返回的交易号（成功后填入）
    trade_no    = models.CharField(max_length=128, blank=True, default="")

    # 有效期（从支付成功时起算）
    plan_start  = models.DateTimeField(null=True, blank=True)
    plan_end    = models.DateTimeField(null=True, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "订单"
        verbose_name_plural = "订单"

    def __str__(self):
        return f"{self.order_no} ({self.get_status_display()})"

    @classmethod
    def generate_order_no(cls):
        """生成唯一订单号：时间戳 + UUID4 短串"""
        import time
        ts = int(time.time() * 1000)
        uid = uuid.uuid4().hex[:8].upper()
        return f"PRO{ts}{uid}"

    @property
    def subject(self):
        labels = {"monthly": "健康管理Pro月度套餐", "annual": "健康管理Pro年度套餐"}
        return labels.get(self.plan_type, "健康管理Pro套餐")
