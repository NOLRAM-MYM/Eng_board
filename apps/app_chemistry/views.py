"""apps/app_chemistry/views.py"""
import dataclasses
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework import serializers, status
from apps.core.responses import success_response, error_response
from apps.core.validators import validate_atomic_number


class ChemistryPageView(TemplateView):
    template_name = 'app_chemistry/index.html'


class PeriodicTableListView(APIView):
    """GET /api/chemistry/elements/ — Complete periodic table dataset."""

    def get(self, request, *args, **kwargs):
        from .fallback_db import load_elements_data
        elements = load_elements_data()
        res = []
        for el in elements:
            res.append({
                "symbol": el.get("symbol"),
                "name": el.get("name"),
                "number": el.get("number"),
                "period": el.get("period"),
                "group": el.get("group"),
                "category": el.get("category"),
                "mass": el.get("atomic_mass") or el.get("mass") or 0.0
            })
        return success_response(res)



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


class ChemistrySimulateSerializer(serializers.Serializer):
    """Validates chemical bonding or reaction simulation requests."""
    mode = serializers.ChoiceField(choices=['bond', 'reaction'])
    formula = serializers.CharField(required=False, allow_blank=True, default='')
    reaction_id = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, data):
        mode = data.get('mode')
        if mode == 'bond' and not data.get('formula'):
            raise serializers.ValidationError({"formula": "Formula is required when mode is 'bond'."})
        if mode == 'reaction' and not data.get('reaction_id'):
            raise serializers.ValidationError({"reaction_id": "reaction_id is required when mode is 'reaction'."})
        return data


class ChemistrySimulateView(APIView):
    """
    POST /api/chemistry/simulate/
    Simulates atomic bonds or compound reactions.
    """

    def post(self, request, *args, **kwargs):
        serializer = ChemistrySimulateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid simulation parameters.",
                code="validation_error",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        mode = data['mode']
        try:
            from .services import ChemistrySimulationService
            if mode == 'bond':
                result = ChemistrySimulationService.run_bond(data['formula'])
            else:
                result = ChemistrySimulationService.run_reaction(data['reaction_id'])
            return success_response(result)
        except Exception as exc:
            return error_response(
                message=str(exc),
                code="simulation_error",
                http_status=status.HTTP_400_BAD_REQUEST,
            )


class StoichiometryInputSerializer(serializers.Serializer):
    """Validates an arbitrary chemical formula for the stoichiometry endpoint."""
    formula = serializers.CharField(max_length=100, allow_blank=False)


class StoichiometryView(APIView):
    """
    POST /api/chemistry/stoichiometry/
    Computes molar mass and per-element mass composition for an arbitrary
    chemical formula (e.g. 'C6H12O6', 'Fe2(SO4)3'), using real atomic masses.
    """

    def post(self, request, *args, **kwargs):
        serializer = StoichiometryInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid formula.",
                code="validation_error",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .services import FormulaParserService
            result = FormulaParserService.compute_molar_mass(serializer.validated_data['formula'])
            return success_response(result)
        except Exception as exc:
            return error_response(
                message=str(exc),
                code="parse_error",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

