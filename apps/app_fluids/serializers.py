"""
apps/app_fluids/serializers.py
================================
DRF serializers for pipe flow API endpoints.

Responsibility:
    1. Deserialize raw user JSON → validated Python types
    2. Apply physical constraint validators (from apps.core.validators)
    3. Convert user units → SI units before handing off to PipeFlowService
    4. Serialize PipeFlowResult → JSON-ready dict

Design:
    - Accepts user-friendly inputs with explicit unit fields
      (e.g., diameter_mm, flow_rate_lpm) to avoid ambiguity
    - All internal calculations happen in SI; unit conversion is explicit
"""

from dataclasses import asdict

from rest_framework import serializers

from apps.core.units import to_si
from apps.core.validators import (
    validate_non_negative_flow_rate,
    validate_positive_density,
    validate_positive_diameter,
    validate_positive_length,
    validate_positive_viscosity,
    validate_roughness,
)
from .services import PipeFlowInput


class PipeFlowInputSerializer(serializers.Serializer):
    """
    Validates and normalises user inputs for the pipe flow calculation.

    Accepted units (explicit — no guessing):
        diameter  → mm   (converted to m)
        length    → m    (stored as-is)
        roughness → mm   (converted to m)
        density   → kg/m³
        viscosity → mPa·s (milli-pascal·second, converted to Pa·s)
        flow_rate → L/min (converted to m³/s)
    """

    # --- Pipe geometry ---
    diameter_mm = serializers.FloatField(
        min_value=0.1,
        max_value=10_000.0,
        help_text="Inner pipe diameter [mm]",
    )
    length_m = serializers.FloatField(
        min_value=0.001,
        max_value=100_000.0,
        help_text="Pipe length [m]",
    )
    roughness_mm = serializers.FloatField(
        default=0.046,   # Commercial steel (typical default)
        min_value=0.0,
        max_value=100.0,
        help_text="Absolute wall roughness [mm]. Default: 0.046 mm (commercial steel)",
    )

    # --- Fluid properties ---
    density_kg_m3 = serializers.FloatField(
        default=1000.0,  # Water at ~20°C
        min_value=0.001,
        max_value=100_000.0,
        help_text="Fluid density [kg/m³]. Default: 1000 kg/m³ (water)",
    )
    viscosity_mpa_s = serializers.FloatField(
        default=1.002,   # Water at 20°C
        min_value=1e-6,
        max_value=100_000.0,
        help_text="Dynamic viscosity [mPa·s]. Default: 1.002 mPa·s (water at 20°C)",
    )

    # --- Operating conditions ---
    flow_rate_lpm = serializers.FloatField(
        min_value=0.0,
        max_value=1_000_000.0,
        help_text="Volumetric flow rate [L/min]",
    )

    # --- Minor losses (optional fittings) ---
    num_elbows_90 = serializers.IntegerField(
        default=0, min_value=0, max_value=100,
        help_text="Number of 90° elbows",
    )
    num_gate_valves_open = serializers.IntegerField(
        default=0, min_value=0, max_value=100,
        help_text="Number of fully-open gate valves",
    )
    num_check_valves = serializers.IntegerField(
        default=0, min_value=0, max_value=100,
        help_text="Number of swing check valves",
    )

    # ---------------------------------------------------------------
    # Field-level validation (physical constraints)
    # ---------------------------------------------------------------

    def validate_diameter_mm(self, value: float) -> float:
        validate_positive_diameter(value / 1000, 'diameter_mm')
        return value

    def validate_length_m(self, value: float) -> float:
        validate_positive_length(value, 'length_m')
        return value

    def validate_roughness_mm(self, value: float) -> float:
        validate_roughness(value / 1000, 'roughness_mm')
        return value

    def validate_density_kg_m3(self, value: float) -> float:
        validate_positive_density(value, 'density_kg_m3')
        return value

    def validate_viscosity_mpa_s(self, value: float) -> float:
        validate_positive_viscosity(value / 1000, 'viscosity_mpa_s')
        return value

    def validate_flow_rate_lpm(self, value: float) -> float:
        validate_non_negative_flow_rate(value, 'flow_rate_lpm')
        return value

    # ---------------------------------------------------------------
    # Cross-field validation
    # ---------------------------------------------------------------

    def validate(self, attrs: dict) -> dict:
        """
        Check that roughness < diameter (otherwise pipe is physically blocked).
        """
        roughness_m = attrs['roughness_mm'] / 1000
        diameter_m  = attrs['diameter_mm'] / 1000
        if roughness_m >= diameter_m / 2:
            raise serializers.ValidationError(
                "Roughness must be less than the pipe radius. "
                f"Got roughness={roughness_m*1000:.3f} mm, radius={diameter_m/2*1000:.3f} mm."
            )
        return attrs

    # ---------------------------------------------------------------
    # Build SI-unit PipeFlowInput
    # ---------------------------------------------------------------

    def to_pipe_flow_input(self) -> PipeFlowInput:
        """
        Convert validated data to SI-unit PipeFlowInput dataclass.
        Call this after ``is_valid(raise_exception=True)``.
        """
        d = self.validated_data
        return PipeFlowInput(
            diameter_m          = d['diameter_mm'] / 1000,
            length_m            = d['length_m'],
            roughness_m         = d['roughness_mm'] / 1000,
            density_kg_m3       = d['density_kg_m3'],
            viscosity_pa_s      = d['viscosity_mpa_s'] / 1000,
            flow_rate_m3_s      = to_si(d['flow_rate_lpm'], 'L/min', 'm^3/s'),
            num_elbows_90       = d['num_elbows_90'],
            num_gate_valves_open= d['num_gate_valves_open'],
            num_check_valves    = d['num_check_valves'],
        )


class PipeFlowResultSerializer(serializers.Serializer):
    """
    Serializes PipeFlowResult to a JSON-compatible dict.

    This is a read-only serializer — it's only used for output documentation
    and response shaping. The actual serialization calls ``dataclasses.asdict``.
    """
    velocity_m_s             = serializers.FloatField(read_only=True)
    reynolds_number          = serializers.FloatField(read_only=True)
    flow_regime              = serializers.CharField(read_only=True)
    friction_factor          = serializers.FloatField(read_only=True)
    friction_method          = serializers.CharField(read_only=True)
    pressure_drop_major_pa   = serializers.FloatField(read_only=True)
    pressure_drop_minor_pa   = serializers.FloatField(read_only=True)
    pressure_drop_total_pa   = serializers.FloatField(read_only=True)
    pressure_drop_total_bar  = serializers.FloatField(read_only=True)
    radial_positions         = serializers.ListField(child=serializers.FloatField())
    velocity_profile         = serializers.ListField(child=serializers.FloatField())
    sweep_flow_rates_m3_s    = serializers.ListField(child=serializers.FloatField())
    sweep_pressure_drops_pa  = serializers.ListField(child=serializers.FloatField())
    hagen_poiseuille_exact   = serializers.CharField(allow_null=True)
    warnings                 = serializers.ListField(child=serializers.CharField())
