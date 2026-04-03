"""
支付相关 API 视图。

端点：
    POST /api/v1/payments/orders/                  创建订单，返回支付宝跳转 URL
    GET  /api/v1/payments/orders/<order_no>/       查询订单状态（前端轮询）
    POST /api/v1/payments/notify/                  支付宝异步通知（无 Auth）
    GET  /api/v1/payments/orders/                  当前用户订单列表

支付流程（电脑网页支付 PC Web）：
    1. 前端 POST /payments/orders/  → 后端创建 Order 记录，返回支付宝 pay_url
    2. 前端在新标签打开 pay_url，用户完成支付
    3. 支付宝 POST 异步通知 → verify → 升级 plan → 返回 "success"
    4. 支付宝同步跳转 return_url（前端 /payment/result?order_no=xxx）
    5. 前端 GET /payments/orders/<order_no>/ 轮询确认 status=paid
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .alipay_client import get_alipay_client
from .models import Order

User = get_user_model()
logger = logging.getLogger(__name__)

# 套餐价格（单位：元）
PLAN_PRICES = {
    "monthly": "25.00",
    "annual":  "199.00",
}

# 有效天数
PLAN_DAYS = {
    "monthly": 31,
    "annual":  366,
}


def _activate_plan(order: Order):
    """将订单对应用户升级为 Pro，并写入有效期。"""
    from datetime import timedelta

    user = order.user
    if not user:
        return
    now = timezone.now()
    order.status     = "paid"
    order.plan_start = now
    order.plan_end   = now + timedelta(days=PLAN_DAYS.get(order.plan_type, 31))
    order.save(update_fields=["status", "plan_start", "plan_end", "updated_at"])

    user.plan = "pro"
    user.ai_monthly_usage = 0
    user.save(update_fields=["plan", "ai_monthly_usage"])
    logger.info("Order %s paid → user %s upgraded to pro (until %s)", order.order_no, user.pk, order.plan_end)


class CreateOrderView(APIView):
    """POST 创建支付订单，返回支付宝跳转 URL"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_type = (request.data.get("plan_type") or "monthly").strip()
        if plan_type not in PLAN_PRICES:
            return Response({"code": 1, "message": "套餐类型无效"}, status=status.HTTP_400_BAD_REQUEST)

        # 若用户已是 Pro，且当前有效，则不允许重复购买
        if request.user.plan == "pro":
            return Response({"code": 1, "message": "您已是 Pro 用户"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client, sandbox = get_alipay_client()
        except RuntimeError as e:
            return Response({"code": 1, "message": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        amount = PLAN_PRICES[plan_type]
        order_no = Order.generate_order_no()

        order = Order.objects.create(
            user=request.user,
            order_no=order_no,
            plan_type=plan_type,
            amount=amount,
            status="pending",
        )

        notify_url = getattr(settings, "ALIPAY_NOTIFY_URL", "")
        return_url = getattr(settings, "ALIPAY_RETURN_URL", "")

        # 生成支付宝 PC 网页支付跳转参数（电脑端）
        order_string = client.api_alipay_trade_page_pay(
            out_trade_no=order_no,
            total_amount=amount,
            subject=order.subject,
            return_url=return_url,
            notify_url=notify_url,
            body=f"健康管理系统 Pro 版 - {order.get_plan_type_display()}",
        )

        if sandbox:
            gateway = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
        else:
            gateway = "https://openapi.alipay.com/gateway.do"

        pay_url = f"{gateway}?{order_string}"

        return Response({
            "code": 0,
            "message": "success",
            "data": {
                "order_no": order_no,
                "pay_url": pay_url,
                "amount": amount,
                "plan_type": plan_type,
            },
        }, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """GET 查询订单状态（前端轮询用）"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no, user=request.user)
        except Order.DoesNotExist:
            return Response({"code": 1, "message": "订单不存在"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "code": 0,
            "message": "success",
            "data": {
                "order_no": order.order_no,
                "status":   order.status,
                "plan_type": order.plan_type,
                "amount":   str(order.amount),
                "plan_end": order.plan_end.isoformat() if order.plan_end else None,
                "created_at": order.created_at.isoformat(),
            },
        })


class OrderListView(APIView):
    """GET 当前用户全部订单"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)[:20]
        data = [
            {
                "order_no":   o.order_no,
                "status":     o.status,
                "plan_type":  o.plan_type,
                "amount":     str(o.amount),
                "plan_end":   o.plan_end.isoformat() if o.plan_end else None,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ]
        return Response({"code": 0, "message": "success", "data": data})


@method_decorator(csrf_exempt, name="dispatch")
class AlipayNotifyView(APIView):
    """POST 支付宝异步通知（无 JWT 认证，验签后处理）"""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        # 从 POST 数据中提取参数（支付宝 notify 使用 form-encoded）
        data = request.POST.dict()
        signature = data.pop("sign", None)

        try:
            client, _ = get_alipay_client()
        except RuntimeError:
            logger.error("Alipay notify: client not configured")
            return Response("fail", content_type="text/plain", status=200)

        # 验签
        success = client.verify(data, signature)
        if not success:
            logger.warning("Alipay notify: signature verification failed, data=%s", data)
            return Response("fail", content_type="text/plain", status=200)

        trade_status = data.get("trade_status", "")
        out_trade_no = data.get("out_trade_no", "")
        trade_no     = data.get("trade_no", "")

        logger.info("Alipay notify: order=%s status=%s trade_no=%s", out_trade_no, trade_status, trade_no)

        if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            try:
                order = Order.objects.select_for_update().get(order_no=out_trade_no)
            except Order.DoesNotExist:
                logger.error("Alipay notify: order %s not found", out_trade_no)
                return Response("fail", content_type="text/plain", status=200)

            if order.status != "paid":
                order.trade_no = trade_no
                _activate_plan(order)

        # 必须返回 "success" 字符串，否则支付宝会反复重试通知
        return Response("success", content_type="text/plain", status=200)
