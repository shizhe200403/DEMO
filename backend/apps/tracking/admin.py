from django.contrib import admin

from .models import HealthGoal, HealthGoalProgress, MealRecord, MealRecordItem, UserBehavior

admin.site.register(MealRecord)
admin.site.register(MealRecordItem)
admin.site.register(HealthGoal)
admin.site.register(HealthGoalProgress)
admin.site.register(UserBehavior)
