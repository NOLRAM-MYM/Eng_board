"""
apps/app_fluids/views.py
=========================
REST API views for the Fluid Mechanics module.

Endpoints:
    POST /api/fluids/pipe-flow/
        → Compute full pipe flow analysis. Returns JSON with Reynolds number,
          friction factor, pressure drop, velocity profile, and sweep data.

    GET  /api/fluids/pipe-flow/schema/
        → Returns the input schema (field names, units, defaults, constraints)
          so the frontend can auto-generate the form without hard-coding field names.

    GET  /api/fluids/pipe-flow/
        → Returns the pipe flow HTML template (full page view).
"""

import dataclasses
import logging

from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework import status

from apps.core.responses import error_response, success_response
from .serializers import PipeFlowInputSerializer
from .services import PipeFlowService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Template View (HTML Page)
# ---------------------------------------------------------------------------

class PipeFlowPageView(TemplateView):
    """Render the full Pipe Flow dashboard page."""
    template_name = 'app_fluids/pipe_flow.html'


# ---------------------------------------------------------------------------
# API View — Pipe Flow Calculation
# ---------------------------------------------------------------------------

class PipeFlowCalculateView(APIView):
    """
    POST /api/fluids/pipe-flow/calculate/

    Accepts pipe and fluid parameters as JSON, runs PipeFlowService,
    and returns the complete analysis as a structured JSON response.

    Request body (JSON):
        {
            "diameter_mm": 50.0,        // Inner diameter [mm]
            "length_m": 100.0,          // Pipe length [m]
            "roughness_mm": 0.046,      // Wall roughness [mm] (default: 0.046)
            "density_kg_m3": 1000.0,    // Fluid density [kg/m³] (default: 1000)
            "viscosity_mpa_s": 1.002,   // Dynamic viscosity [mPa·s] (default: 1.002)
            "flow_rate_lpm": 120.0,     // Volumetric flow rate [L/min]
            "num_elbows_90": 2,         // Optional: fitting count
            "num_gate_valves_open": 1,
            "num_check_valves": 0
        }

    Response (JSON):
        {
            "status": "success",
            "data": {
                "velocity_m_s": 1.02,
                "reynolds_number": 51000.0,
                "flow_regime": "Turbulent",
                "friction_factor": 0.0208,
                "pressure_drop_total_bar": 0.234,
                ... (full PipeFlowResult fields)
            }
        }
    """

    def post(self, request, *args, **kwargs):
        logger.info("PipeFlowCalculateView.post() — %s", request.data)

        # 1. Validate and deserialize input
        serializer = PipeFlowInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid input parameters.",
                code="validation_error",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Build SI-unit input dataclass
        pipe_input = serializer.to_pipe_flow_input()

        # 3. Run computation
        try:
            service = PipeFlowService(pipe_input)
            result  = service.compute()
        except Exception as exc:
            logger.exception("PipeFlowService.compute() failed: %s", exc)
            return error_response(
                message="Computation failed. Check input values and try again.",
                code="computation_error",
                errors={"detail": str(exc)},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 4. Serialize result (dataclass → dict)
        result_dict = dataclasses.asdict(result)

        return success_response(result_dict, http_status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# API View — Input Schema (for form auto-generation)
# ---------------------------------------------------------------------------

class PipeFlowSchemaView(APIView):
    """
    GET /api/fluids/pipe-flow/schema/

    Returns the input schema so the frontend can dynamically build the form.
    Each field includes: label, unit, default, min, max, type.
    """

    def get(self, request, *args, **kwargs):
        schema = {
            "title": "Pipe Flow Analysis",
            "description": (
                "Darcy-Weisbach analysis for incompressible Newtonian pipe flow. "
                "Computes Reynolds number, friction factor, pressure drop, "
                "and velocity profile."
            ),
            "fields": [
                {
                    "name": "diameter_mm",
                    "label": "Inner Diameter",
                    "unit": "mm",
                    "type": "float",
                    "default": 50.0,
                    "min": 0.1,
                    "max": 10000.0,
                    "step": 0.1,
                    "help": "Internal pipe diameter in millimetres.",
                },
                {
                    "name": "length_m",
                    "label": "Pipe Length",
                    "unit": "m",
                    "type": "float",
                    "default": 100.0,
                    "min": 0.001,
                    "max": 100000.0,
                    "step": 0.1,
                    "help": "Total straight pipe length.",
                },
                {
                    "name": "roughness_mm",
                    "label": "Wall Roughness (ε)",
                    "unit": "mm",
                    "type": "float",
                    "default": 0.046,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.001,
                    "help": "Absolute roughness of the pipe wall. Commercial steel: 0.046 mm.",
                },
                {
                    "name": "density_kg_m3",
                    "label": "Fluid Density",
                    "unit": "kg/m³",
                    "type": "float",
                    "default": 1000.0,
                    "min": 0.001,
                    "max": 100000.0,
                    "step": 0.1,
                    "help": "Fluid density. Water at 20°C: 998.2 kg/m³.",
                },
                {
                    "name": "viscosity_mpa_s",
                    "label": "Dynamic Viscosity (μ)",
                    "unit": "mPa·s",
                    "type": "float",
                    "default": 1.002,
                    "min": 1e-6,
                    "max": 100000.0,
                    "step": 0.001,
                    "help": "Dynamic viscosity. Water at 20°C: 1.002 mPa·s.",
                },
                {
                    "name": "flow_rate_lpm",
                    "label": "Flow Rate",
                    "unit": "L/min",
                    "type": "float",
                    "default": 120.0,
                    "min": 0.0,
                    "max": 1000000.0,
                    "step": 0.1,
                    "help": "Volumetric flow rate entering the pipe.",
                },
                {
                    "name": "num_elbows_90",
                    "label": "90° Elbows",
                    "unit": "count",
                    "type": "integer",
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "help": "Number of 90° standard radius elbows.",
                },
                {
                    "name": "num_gate_valves_open",
                    "label": "Gate Valves (open)",
                    "unit": "count",
                    "type": "integer",
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "help": "Number of fully open gate valves.",
                },
                {
                    "name": "num_check_valves",
                    "label": "Check Valves",
                    "unit": "count",
                    "type": "integer",
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "help": "Number of swing check valves.",
                },
            ],
            "preset_fluids": [
                {"name": "Water (20°C)",    "density": 998.2,  "viscosity": 1.002},
                {"name": "Water (60°C)",    "density": 983.2,  "viscosity": 0.467},
                {"name": "Engine Oil",      "density": 888.0,  "viscosity": 100.0},
                {"name": "Air (20°C, 1atm)","density": 1.204,  "viscosity": 0.0181},
                {"name": "Mercury (20°C)", "density": 13546.0, "viscosity": 1.526},
                {"name": "Ethanol (20°C)", "density": 789.0,  "viscosity": 1.2},
            ],
        }
        return success_response(schema)
