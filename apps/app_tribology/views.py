"""
apps/app_tribology/views.py
===========================
Views and API controllers for the Tribology module.
"""

from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework import serializers, status
from apps.core.responses import success_response, error_response
from .services import TribologyService


class TribologyPageView(TemplateView):
    """Serves the main Tribology and Gears simulation page."""
    template_name = 'app_tribology/index.html'


class TribologyInputSerializer(serializers.Serializer):
    """Validates physical input parameters for gear and EHL calculation."""
    module_mm = serializers.FloatField(default=3.0, min_value=0.1, max_value=50.0)
    pinion_teeth = serializers.IntegerField(default=20, min_value=5, max_value=500)
    gear_teeth = serializers.IntegerField(default=40, min_value=5, max_value=500)
    pinion_rpm = serializers.FloatField(default=1500.0, min_value=0.0, max_value=20000.0)
    viscosity_pa_s = serializers.FloatField(default=0.04, min_value=0.001, max_value=100.0)
    roughness_um = serializers.FloatField(default=0.5, min_value=0.01, max_value=50.0)
    load_n = serializers.FloatField(default=2000.0, min_value=1.0, max_value=1000000.0)


class TribologyCalculateView(APIView):
    """
    POST /api/tribology/calculate/
    Processes spur gear parameters and returns EHL lubrication status and speed sweeps.
    """

    def post(self, request, *args, **kwargs):
        serializer = TribologyInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid input parameters.",
                code="validation_error",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            service = TribologyService(
                module_mm=data['module_mm'],
                pinion_teeth=data['pinion_teeth'],
                gear_teeth=data['gear_teeth'],
                pinion_rpm=data['pinion_rpm'],
                viscosity_pa_s=data['viscosity_pa_s'],
                roughness_um=data['roughness_um'],
                load_n=data['load_n'],
            )
            result = service.compute()
            return success_response(result)
        except Exception as exc:
            return error_response(
                message=f"Computation failed: {exc}",
                code="calculation_error",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
