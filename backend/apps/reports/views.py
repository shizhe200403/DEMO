from datetime import date

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import permissions, status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ReportTask
from .services import generate_pdf_report, report_period


class ReportPayloadSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    file_url = serializers.CharField(allow_blank=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class EnvelopeReportPayloadSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ReportPayloadSerializer()


class ExportReportRequestSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=["weekly", "monthly"], required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class ReportTaskDataSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    status = serializers.CharField()
    file_url = serializers.CharField(allow_blank=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    generated_at = serializers.DateTimeField(allow_null=True)


class EnvelopeReportTaskSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ReportTaskDataSerializer()


def _build_report_response(user, report_type, start_date, end_date):
    task = ReportTask.objects.create(user=user, report_type=report_type, status="processing", start_date=start_date, end_date=end_date)
    try:
        file_path = generate_pdf_report(user, report_type, start_date, end_date)
        task.status = "completed"
        task.file_url = f"/media/reports/{file_path.name}"
        task.generated_at = timezone.now()
        task.save(update_fields=["status", "file_url", "generated_at", "updated_at"])
        return {
            "task_id": task.id,
            "file_url": task.file_url,
            "start_date": start_date,
            "end_date": end_date,
        }
    except Exception:
        task.status = "failed"
        task.save(update_fields=["status", "updated_at"])
        raise


class WeeklyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=EnvelopeReportPayloadSerializer)
    def get(self, request):
        try:
            start_date, end_date = report_period("weekly")
            return Response({"code": 0, "message": "success", "data": _build_report_response(request.user, "weekly", start_date, end_date)})
        except Exception:
            return Response({"code": 500, "message": "report generation failed", "data": None}, status=500)


class MonthlyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=EnvelopeReportPayloadSerializer)
    def get(self, request):
        try:
            start_date, end_date = report_period("monthly")
            return Response({"code": 0, "message": "success", "data": _build_report_response(request.user, "monthly", start_date, end_date)})
        except Exception:
            return Response({"code": 500, "message": "report generation failed", "data": None}, status=500)


class ExportReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ExportReportRequestSerializer, responses=EnvelopeReportPayloadSerializer)
    def post(self, request):
        report_type = request.data.get("report_type", "weekly")
        if report_type not in {"weekly", "monthly"}:
            report_type = "weekly"
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        if not start_date or not end_date:
            start_date, end_date = report_period(report_type)
        else:
            try:
                start_date = date.fromisoformat(str(start_date))
                end_date = date.fromisoformat(str(end_date))
            except ValueError:
                return Response({"code": 400, "message": "invalid date format", "data": None}, status=400)
        try:
            data = _build_report_response(request.user, report_type, start_date, end_date)
            return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_201_CREATED)
        except Exception:
            return Response({"code": 500, "message": "report generation failed", "data": None}, status=500)


class ReportTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name="task_id", location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT)],
        responses=EnvelopeReportTaskSerializer,
    )
    def get(self, request, task_id):
        task = ReportTask.objects.filter(id=task_id, user=request.user).first()
        if task is None:
            return Response({"code": 404, "message": "not found", "data": None}, status=404)
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "task_id": task.id,
                    "status": task.status,
                    "file_url": task.file_url,
                    "start_date": task.start_date,
                    "end_date": task.end_date,
                    "generated_at": task.generated_at,
                },
            }
        )
