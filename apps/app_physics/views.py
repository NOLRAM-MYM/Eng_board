"""
apps/app_physics/views.py
==========================
Views for the Physics module.
"""

from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework import serializers, status
from apps.core.responses import success_response, error_response
from .services import ProjectileMotionService


class PhysicsPageView(TemplateView):
    """Serves the main Physics simulation HTML page."""
    template_name = 'app_physics/index.html'


class ProjectileInputSerializer(serializers.Serializer):
    """Validates parameters for the projectile motion simulation."""
    velocity_m_s = serializers.FloatField(default=20.0, min_value=0.1, max_value=1000.0)
    angle_deg = serializers.FloatField(default=45.0, min_value=0.1, max_value=89.9)
    mass_kg = serializers.FloatField(default=1.0, min_value=0.001, max_value=10000.0)
    diameter_m = serializers.FloatField(default=0.1, min_value=0.001, max_value=10.0)
    drag_coefficient = serializers.FloatField(default=0.47, min_value=0.0, max_value=5.0)


class ProjectileCalculateView(APIView):
    """
    POST /api/physics/projectile/calculate/
    Runs the numerical integration solver for projectile trajectories.
    """

    def post(self, request, *args, **kwargs):
        serializer = ProjectileInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid input parameters.",
                code="validation_error",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            service = ProjectileMotionService(
                velocity_m_s=data['velocity_m_s'],
                angle_deg=data['angle_deg'],
                mass_kg=data['mass_kg'],
                diameter_m=data['diameter_m'],
                drag_coefficient=data['drag_coefficient']
            )
            result = service.compute()
            return success_response(result)
        except Exception as exc:
            return error_response(
                message=f"Computation failed: {exc}",
                code="calculation_error",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
