"""
Celery 异步任务：推荐预计算。

任务调度由 Celery Beat 触发（settings.CELERY_BEAT_SCHEDULE）：
  - precompute_all_recommendations：每天凌晨 2:00 为所有活跃用户重算推荐缓存
  - precompute_single_user_recommendations：按需（用户登录/行为变化后）刷新单用户缓存
"""
import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from .services import compute_and_cache_for_user

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def precompute_all_recommendations(self):
    """
    为所有活跃用户预计算推荐并写入缓存。
    跳过超管/运营账号（is_staff=True）。
    """
    users = User.objects.filter(is_active=True, is_staff=False).only("id", "pk")
    total = 0
    errors = 0
    for user in users:
        try:
            count = compute_and_cache_for_user(user)
            total += count
        except Exception as exc:
            errors += 1
            logger.warning("推荐预计算失败 user_id=%s: %s", user.pk, exc)
    logger.info("推荐预计算完成：%d 条，%d 个用户出错", total, errors)
    return {"cached": total, "errors": errors}


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def precompute_single_user_recommendations(self, user_id: int):
    """
    为单个用户刷新推荐缓存（行为事件触发时调用）。
    """
    try:
        user = User.objects.get(pk=user_id)
        count = compute_and_cache_for_user(user)
        logger.debug("用户 %d 推荐缓存已刷新：%d 条", user_id, count)
        return count
    except User.DoesNotExist:
        logger.warning("precompute_single_user_recommendations: user %d 不存在", user_id)
        return 0
    except Exception as exc:
        logger.error("单用户推荐预计算失败 user_id=%d: %s", user_id, exc)
        raise self.retry(exc=exc)
