"""apps/app_materials/views.py"""
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response

from .serializers import BeamDeflectionInputSerializer


class MaterialsPageView(TemplateView):
    template_name = 'app_materials/index.html'


class BeamDeflectionView(APIView):
    """POST /api/materials/beam-deflection/ — Euler-Bernoulli beam analysis."""

    def post(self, request, *args, **kwargs):
        from .services import BeamDeflectionService

        serializer = BeamDeflectionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid beam parameters.",
                code="validation_error",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = BeamDeflectionService(**serializer.to_service_kwargs())
            result = service.compute()
        except ValueError as exc:
            return error_response(
                message=str(exc),
                code="calculation_error",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return success_response(result)
