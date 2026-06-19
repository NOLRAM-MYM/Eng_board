"""apps/app_chemistry/views.py"""
import dataclasses
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework import serializers
from apps.core.responses import success_response, error_response
from apps.core.validators import validate_atomic_number


class ChemistryPageView(TemplateView):
    template_name = 'app_chemistry/index.html'


class ElementPropertyView(APIView):
    """GET /api/chemistry/element/<symbol_or_z>/ — Element properties."""

    def get(self, request, identifier, *args, **kwargs):
        from .services import ElementPropertyService
        # Validate atomic number if integer provided
        try:
            z = int(identifier)
            validate_atomic_number(z)
            lookup = z
        except ValueError:
            lookup = str(identifier).capitalize()

        try:
            service = ElementPropertyService()
            data = service.get_element(lookup)
            return success_response(dataclasses.asdict(data))
        except Exception as exc:
            return error_response(
                message=f"Element '{identifier}' not found or error: {exc}",
                code="element_not_found",
            )
