"""
Celery 定时任务：检查 Pro 订单是否到期，到期后将用户降回免费版。
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="apps.payments.tasks.expire_pro_plans")
def expire_pro_plans(self):
    """将所有已到期的 paid 订单对应用户降回 free，每天凌晨执行一次。"""
    from .models import Order

    now = timezone.now()
    expired = Order.objects.filter(status="paid", plan_end__lt=now).select_related("user")
    count = 0
    for order in expired:
        order.status = "expired"
        order.save(update_fields=["status", "updated_at"])
        user = order.user
        if user and user.plan == "pro":
            # 若用户还有其他有效 paid 订单，不降级
            still_active = Order.objects.filter(
                user=user, status="paid", plan_end__gte=now
            ).exists()
            if not still_active:
                user.plan = "free"
                user.save(update_fields=["plan"])
                logger.info("User %s Pro expired, downgraded to free", user.pk)
                count += 1
    logger.info("expire_pro_plans: %d users downgraded", count)
    return count
