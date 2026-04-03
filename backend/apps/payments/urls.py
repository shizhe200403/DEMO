from django.urls import path

from .views import AlipayNotifyView, CreateOrderView, OrderDetailView, OrderListView

urlpatterns = [
    path("orders/",              OrderListView.as_view(),    name="payment-order-list"),
    path("orders/create/",       CreateOrderView.as_view(),  name="payment-order-create"),
    path("orders/<str:order_no>/", OrderDetailView.as_view(), name="payment-order-detail"),
    path("notify/",              AlipayNotifyView.as_view(), name="payment-alipay-notify"),
]
