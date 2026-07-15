"""
apps/core/validators.py
========================
Physical constraint validators used across all scientific modules.

These validators are framework-agnostic Python callables that raise
``ValidationError`` (from DRF or Django) when a value violates a physical law.
They are imported by serializers and services throughout the application.

Design Principles:
- Every constraint has a clear docstring citing the physical law.
- Error messages are human-readable and include SI units.
- Validators accept plain Python numbers (not Pint Quantities) for maximum
  reuse; unit conversion happens in the service layer.
"""

from rest_framework.exceptions import ValidationError

# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------

#: Absolute zero in Celsius — thermodynamically impossible to go below this.
ABSOLUTE_ZERO_CELSIUS = -273.15  # °C

#: Absolute zero in Kelvin — Kelvin scale starts here.
ABSOLUTE_ZERO_KELVIN = 0.0       # K


def validate_temperature_celsius(value: float, field_name: str = 'temperature') -> float:
    """
    Reject temperatures below absolute zero (−273.15 °C / 0 K).

    Physical basis: Third Law of Thermodynamics — it is physically impossible
    to reach a temperature below absolute zero.

    Args:
        value: Temperature in degrees Celsius.
        field_name: Name used in the error message.

    Returns:
        The validated value (unchanged).

    Raises:
        ValidationError: If value < −273.15 °C.
    """
    if value < ABSOLUTE_ZERO_CELSIUS:
        raise ValidationError(
            {field_name: (
                f"Temperature {value} °C is below absolute zero "
                f"({ABSOLUTE_ZERO_CELSIUS} °C). Physically impossible."
            )}
        )
    return value


def validate_temperature_kelvin(value: float, field_name: str = 'temperature') -> float:
    """
    Reject temperatures below 0 K.

    Args:
        value: Temperature in Kelvin.
        field_name: Name used in the error message.

    Returns:
        The validated value.

    Raises:
        ValidationError: If value < 0 K.
    """
    if value < ABSOLUTE_ZERO_KELVIN:
        raise ValidationError(
            {field_name: (
                f"Temperature {value} K is below absolute zero (0 K). "
                "Physically impossible."
            )}
        )
    return value


# ---------------------------------------------------------------------------
# Mass & Density
# ---------------------------------------------------------------------------

def validate_positive_mass(value: float, field_name: str = 'mass') -> float:
    """
    Ensure mass is strictly positive.

    Physical basis: Mass is an intrinsic property of matter. Negative or zero
    mass has no physical meaning in classical or relativistic mechanics.

    Args:
        value: Mass in kg.
        field_name: Name used in the error message.

    Returns:
        The validated value.

    Raises:
        ValidationError: If value ≤ 0.
    """
    if value <= 0:
        raise ValidationError(
            {field_name: f"Mass must be strictly positive. Got {value} kg."}
        )
    return value


def validate_positive_density(value: float, field_name: str = 'density') -> float:
    """
    Ensure fluid/material density is strictly positive.

    Args:
        value: Density in kg/m³.
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value ≤ 0.
    """
    if value <= 0:
        raise ValidationError(
            {field_name: f"Density must be strictly positive. Got {value} kg/m³."}
        )
    return value


# ---------------------------------------------------------------------------
# Pressure
# ---------------------------------------------------------------------------

def validate_non_negative_pressure(value: float, field_name: str = 'pressure') -> float:
    """
    Ensure absolute pressure is non-negative.

    Physical basis: Absolute pressure is defined as force per unit area and
    cannot be negative. Gauge pressure can be negative (vacuum), but absolute
    pressure has a hard floor at 0 Pa (perfect vacuum).

    Args:
        value: Pressure in Pascals (absolute).
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value < 0.
    """
    if value < 0:
        raise ValidationError(
            {field_name: (
                f"Absolute pressure cannot be negative. "
                f"Got {value} Pa. Use gauge pressure if needed."
            )}
        )
    return value


# ---------------------------------------------------------------------------
# Pipe / Geometry
# ---------------------------------------------------------------------------

def validate_positive_diameter(value: float, field_name: str = 'diameter') -> float:
    """
    Ensure pipe/tube diameter is strictly positive.

    Args:
        value: Inner diameter in metres.
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value ≤ 0.
    """
    if value <= 0:
        raise ValidationError(
            {field_name: f"Diameter must be strictly positive. Got {value} m."}
        )
    return value


def validate_positive_length(value: float, field_name: str = 'length') -> float:
    """
    Ensure pipe/beam/rod length is strictly positive.

    Args:
        value: Length in metres.
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value ≤ 0.
    """
    if value <= 0:
        raise ValidationError(
            {field_name: f"Length must be strictly positive. Got {value} m."}
        )
    return value


def validate_roughness(value: float, field_name: str = 'roughness') -> float:
    """
    Ensure pipe roughness is non-negative and physically plausible.

    Physical basis: Surface roughness (ε) represents the average height of
    surface irregularities. It cannot be negative and is bounded above by the
    pipe radius (roughness ≥ diameter would mean the pipe is fully blocked).

    Args:
        value: Absolute roughness in metres.
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value < 0.
    """
    if value < 0:
        raise ValidationError(
            {field_name: f"Surface roughness cannot be negative. Got {value} m."}
        )
    return value


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------

def validate_non_negative_flow_rate(value: float, field_name: str = 'flow_rate') -> float:
    """
    Ensure volumetric or mass flow rate is non-negative.

    Args:
        value: Flow rate in m³/s or kg/s.
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value < 0.
    """
    if value < 0:
        raise ValidationError(
            {field_name: f"Flow rate cannot be negative. Got {value}."}
        )
    return value


def validate_positive_viscosity(value: float, field_name: str = 'viscosity') -> float:
    """
    Ensure dynamic viscosity is strictly positive.

    Physical basis: Dynamic viscosity μ represents internal fluid friction and
    must be strictly positive for any real fluid. A zero or negative viscosity
    is unphysical.

    Args:
        value: Dynamic viscosity in Pa·s.
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value ≤ 0.
    """
    if value <= 0:
        raise ValidationError(
            {field_name: (
                f"Dynamic viscosity must be strictly positive. "
                f"Got {value} Pa·s."
            )}
        )
    return value


# ---------------------------------------------------------------------------
# Atomic / Chemistry
# ---------------------------------------------------------------------------

def validate_atomic_number(value: int, field_name: str = 'atomic_number') -> int:
    """
    Ensure atomic number Z is between 1 (Hydrogen) and 118 (Oganesson).

    Args:
        value: Atomic number (integer).
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value outside [1, 118].
    """
    if not (1 <= value <= 118):
        raise ValidationError(
            {field_name: (
                f"Atomic number must be between 1 (H) and 118 (Og). Got {value}."
            )}
        )
    return value


def validate_positive_concentration(
    value: float, field_name: str = 'concentration'
) -> float:
    """
    Ensure chemical concentration is non-negative.

    Args:
        value: Concentration in mol/L.
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value < 0.
    """
    if value < 0:
        raise ValidationError(
            {field_name: f"Concentration cannot be negative. Got {value} mol/L."}
        )
    return value


# ---------------------------------------------------------------------------
# Structural / Materials
# ---------------------------------------------------------------------------

def validate_positive_youngs_modulus(value: float, field_name: str = 'youngs_modulus') -> float:
    """
    Ensure Young's modulus (E) is strictly positive.

    Physical basis: material stiffness under Hooke's law cannot be zero or
    negative — it would imply the material offers no (or negative) resistance
    to elastic deformation.

    Args:
        value: Young's modulus in GPa.
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value ≤ 0.
    """
    if value <= 0:
        raise ValidationError(
            {field_name: f"Young's modulus must be strictly positive. Got {value} GPa."}
        )
    return value


def validate_positive_second_moment(value: float, field_name: str = 'second_moment') -> float:
    """
    Ensure the second moment of area (I) is strictly positive.

    Physical basis: I describes how a cross-section resists bending. A zero
    or negative value has no physical cross-section and causes division by
    zero in the EI bending stiffness term.

    Args:
        value: Second moment of area in m⁴.
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value ≤ 0.
    """
    if value <= 0:
        raise ValidationError(
            {field_name: f"Second moment of area (I) must be strictly positive. Got {value} m⁴."}
        )
    return value


def validate_positive_load(value: float, field_name: str = 'load') -> float:
    """
    Ensure applied load magnitude is strictly positive.

    Args:
        value: Load magnitude (e.g. kN).
        field_name: Name used in the error message.

    Raises:
        ValidationError: If value ≤ 0.
    """
    if value <= 0:
        raise ValidationError(
            {field_name: f"Load must be strictly positive. Got {value}."}
        )
    return value
