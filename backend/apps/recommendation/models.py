from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class RecommendedRecipe(models.Model):
    """预计算推荐结果缓存表，由 Celery Beat 定时刷新。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommended_recipes",
    )
    recipe_id = models.IntegerField()
    rank = models.PositiveSmallIntegerField()
    score = models.FloatField(default=0.0)
    reason_text = models.CharField(max_length=512, default="")
    algo_version = models.CharField(max_length=32, default="hybrid_v1")
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recommended_recipe"
        ordering = ["user_id", "rank"]
        indexes = [
            models.Index(fields=["user_id", "rank"]),
        ]

    def __str__(self):
        return f"User {self.user_id} → Recipe {self.recipe_id} (rank {self.rank})"
