"""apps/app_materials/views.py — scaffold"""
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.core.responses import success_response


class MaterialsPageView(TemplateView):
    template_name = 'app_materials/index.html'


class BeamDeflectionView(APIView):
    """POST /api/materials/beam-deflection/ — Euler-Bernoulli beam analysis."""

    def post(self, request, *args, **kwargs):
        from .services import BeamDeflectionService
        # TODO: add serializer validation
        data = request.data
        service = BeamDeflectionService(
            length_m            = float(data.get('length_m', 5.0)),
            youngs_modulus_gpa  = float(data.get('youngs_modulus_gpa', 200.0)),
            second_moment_m4    = float(data.get('second_moment_m4', 8.33e-6)),
            load_kn             = float(data.get('load_kn', 50.0)),
            load_type           = data.get('load_type', 'point_centre'),
        )
        result = service.compute()
        return success_response(result)
