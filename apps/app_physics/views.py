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


class MagnetismPageView(TemplateView):
    """Serves the Magnetism & Motors simulation HTML page."""
    template_name = 'app_physics/magnetism.html'


class MagnetismInputSerializer(serializers.Serializer):
    """Validates parameters for the magnetism & motors simulations."""
    mode = serializers.ChoiceField(choices=['lorentz', 'poles', 'motor'])

    # Lorentz fields
    q_uc = serializers.FloatField(required=False, default=10.0)
    m_mg = serializers.FloatField(required=False, default=1.0)
    vx = serializers.FloatField(required=False, default=10.0)
    vy = serializers.FloatField(required=False, default=10.0)
    vz = serializers.FloatField(required=False, default=0.0)
    Bx = serializers.FloatField(required=False, default=0.0)
    By = serializers.FloatField(required=False, default=0.0)
    Bz = serializers.FloatField(required=False, default=1.0)

    # Pole fields
    qm1 = serializers.FloatField(required=False, default=100.0)
    qm2 = serializers.FloatField(required=False, default=-100.0)
    r = serializers.FloatField(required=False, default=0.2)

    # Motor fields
    V = serializers.FloatField(required=False, default=24.0)
    R = serializers.FloatField(required=False, default=2.0)
    L = serializers.FloatField(required=False, default=0.05)
    J = serializers.FloatField(required=False, default=0.02)
    b = serializers.FloatField(required=False, default=0.005)
    Kt = serializers.FloatField(required=False, default=0.5)
    Ke = serializers.FloatField(required=False, default=0.5)
    tl = serializers.FloatField(required=False, default=0.5)

    def validate(self, data):
        mode = data.get('mode')
        if mode == 'lorentz':
            if data.get('m_mg', 0) <= 0:
                raise serializers.ValidationError({"m_mg": "Mass must be positive and non-zero."})
        elif mode == 'poles':
            if data.get('r', 0) <= 0:
                raise serializers.ValidationError({"r": "Distance must be positive and non-zero."})
        elif mode == 'motor':
            for field in ['R', 'L', 'J', 'b', 'Kt', 'Ke']:
                if data.get(field, 0) <= 0:
                    raise serializers.ValidationError({field: f"{field} must be positive and non-zero."})
        return data


class MagnetismCalculateView(APIView):
    """
    POST /api/physics/magnetism/calculate/
    Runs calculation pipelines for Lorentz force, Pole force, and DC Motors.
    """

    def post(self, request, *args, **kwargs):
        serializer = MagnetismInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid input parameters.",
                code="validation_error",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        mode = data['mode']
        try:
            from .services import MagnetismService
            if mode == 'lorentz':
                result = MagnetismService.compute_lorentz(
                    q_uc=data['q_uc'],
                    m_mg=data['m_mg'],
                    v0=[data['vx'], data['vy'], data['vz']],
                    B=[data['Bx'], data['By'], data['Bz']]
                )
            elif mode == 'poles':
                result = MagnetismService.compute_poles(
                    qm1=data['qm1'],
                    qm2=data['qm2'],
                    r=data['r']
                )
            elif mode == 'motor':
                result = MagnetismService.compute_motor(
                    V=data['V'],
                    R=data['R'],
                    L=data['L'],
                    J=data['J'],
                    b=data['b'],
                    Kt=data['Kt'],
                    Ke=data['Ke'],
                    tl=data['tl']
                )
            return success_response(result)
        except Exception as exc:
            return error_response(
                message=f"Computation failed: {exc}",
                code="calculation_error",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

