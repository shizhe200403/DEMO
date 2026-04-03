from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.recipes.urls")),
    path("api/v1/", include("apps.tracking.urls")),
    path("api/v1/", include("apps.recommendation.urls")),
    path("api/v1/", include("apps.nutrition.urls")),
    path("api/v1/", include("apps.community.urls")),
    path("api/v1/", include("apps.reports.urls")),
    path("api/v1/assistant/", include("apps.assistant.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
