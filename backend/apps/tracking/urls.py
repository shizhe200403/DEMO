from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import HealthGoalViewSet, MealRecordViewSet, UserBehaviorTrackView

router = DefaultRouter()
router.register(r"meal-records", MealRecordViewSet, basename="meal-record")
router.register(r"health-goals", HealthGoalViewSet, basename="health-goal")

urlpatterns = router.urls
urlpatterns += [
    path("events/track/", UserBehaviorTrackView.as_view(), name="event-track"),
]
