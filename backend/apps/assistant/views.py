import json

from django.db.models import F
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from django.http import StreamingHttpResponse
from rest_framework import permissions, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .context import build_user_context
from .llm import analyze_food_image, stream_chat
from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    FoodImageAnalysisRequestSerializer,
    FoodImageAnalysisResponseSerializer,
    MessageSerializer,
)


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def conversations(request):
    if request.method == "POST":
        conv = Conversation.objects.create(user=request.user)
        return Response({"code": 0, "message": "success", "data": ConversationSerializer(conv).data}, status=status.HTTP_201_CREATED)
    qs = Conversation.objects.filter(user=request.user)[:20]
    return Response({"code": 0, "message": "success", "data": ConversationSerializer(qs, many=True).data})


@api_view(["GET", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def conversation_detail(request, pk):
    try:
        conv = Conversation.objects.get(pk=pk, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"code": 1, "message": "not found"}, status=404)
    if request.method == "DELETE":
        conv.delete()
        return Response({"code": 0, "message": "success"})
    msgs = conv.messages.all()
    return Response({"code": 0, "message": "success", "data": {
        "conversation": ConversationSerializer(conv).data,
        "messages": MessageSerializer(msgs, many=True).data,
    }})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def chat(request, pk):
    try:
        conv = Conversation.objects.get(pk=pk, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"code": 1, "message": "not found"}, status=404)

    # --- 配额检查 ---
    FREE_MONTHLY_LIMIT = 30
    user = request.user
    now = timezone.now()
    reset_needed = (
        user.ai_usage_reset_at is None
        or user.ai_usage_reset_at.year != now.year
        or user.ai_usage_reset_at.month != now.month
    )
    if reset_needed:
        user.ai_monthly_usage = 0
        user.ai_usage_reset_at = now
        user.save(update_fields=["ai_monthly_usage", "ai_usage_reset_at"])

    if user.plan == "free" and user.ai_monthly_usage >= FREE_MONTHLY_LIMIT:
        return Response(
            {"code": 429, "message": f"本月免费对话次数（{FREE_MONTHLY_LIMIT}次）已用尽，升级 Pro 版继续使用"},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    # --- 配额检查结束 ---

    user_message = (request.data.get("message") or "").strip()
    if not user_message:
        return Response({"code": 1, "message": "message is required"}, status=400)

    # Save user message
    Message.objects.create(conversation=conv, role="user", content=user_message)

    # 计数（用 F 表达式避免并发竞争）
    type(user).objects.filter(pk=user.pk).update(ai_monthly_usage=F("ai_monthly_usage") + 1)

    # Auto-title from first message
    if conv.title == "新对话":
        conv.title = user_message[:50]
        conv.save(update_fields=["title", "updated_at"])

    # Build context and history
    page_context = (request.data.get("page_context") or "").strip()
    system_prompt = build_user_context(request.user, page_context)
    history = list(conv.messages.order_by("created_at").values_list("role", "content"))
    messages = [{"role": r, "content": c} for r, c in history[-20:]]

    def event_stream():
        full_response = ""
        for chunk in stream_chat(system_prompt, messages):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        Message.objects.create(conversation=conv, role="assistant", content=full_response)
        conv.save(update_fields=["updated_at"])
        yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@extend_schema(
    request=FoodImageAnalysisRequestSerializer,
    responses=FoodImageAnalysisResponseSerializer,
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def analyze_food_photo(request):
    serializer = FoodImageAnalysisRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    image = serializer.validated_data["image"]
    if image.size > 10 * 1024 * 1024:
        return Response({"code": 1, "message": "图片大小不能超过 10MB"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        data = analyze_food_image(image.read())
    except ValueError as exc:
        return Response({"code": 1, "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_200_OK)
