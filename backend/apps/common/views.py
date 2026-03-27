from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckDataSerializer(serializers.Serializer):
    status = serializers.CharField()


class HealthCheckResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = HealthCheckDataSerializer()


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses=HealthCheckResponseSerializer)
    def get(self, request):
        return Response({"code": 0, "message": "success", "data": {"status": "ok"}})


class EnvelopeModelViewSet(viewsets.ModelViewSet):
    def success_response(self, data, http_status=status.HTTP_200_OK):
        return Response({"code": 0, "message": "success", "data": data}, status=http_status)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginator = self.paginator
            return self.success_response(
                {
                    "items": serializer.data,
                    "page": paginator.page.number,
                    "page_size": paginator.get_page_size(request) or len(serializer.data),
                    "total": paginator.page.paginator.count,
                }
            )

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({"code": 0, "message": "success", "data": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return self.success_response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success_response({"deleted": True})
