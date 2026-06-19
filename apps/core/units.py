"""
apps/core/units.py
===================
Pint UnitRegistry singleton for the entire application.

Usage:
    from apps.core.units import ureg, Q_

    # Create a quantity
    flow = Q_(10.0, 'L/min')

    # Convert
    flow_si = flow.to('m^3/s')
    print(flow_si.magnitude)  # 0.000166...

    # Use in calculations
    diameter = Q_(50, 'mm').to('m')

Why a singleton?
    Pint requires all Quantities to share the same UnitRegistry instance.
    Mixing registries raises DimensionalityError. This module provides a
    single canonical registry for the whole Django application.
"""

import pint

# ---------------------------------------------------------------------------
# Canonical UnitRegistry — import this everywhere
# ---------------------------------------------------------------------------
ureg = pint.UnitRegistry()

# Shorthand constructor: Q_(3.0, 'm/s') == ureg.Quantity(3.0, 'm/s')
Q_ = ureg.Quantity

# Make Pint quantities JSON-serializable (returns magnitude as float)
ureg.default_format = '.6g'  # 6 significant figures


# ---------------------------------------------------------------------------
# Common unit helpers
# ---------------------------------------------------------------------------

def to_si(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a scalar value from one unit to another.

    Args:
        value: Numeric magnitude.
        from_unit: Source unit string (Pint-compatible, e.g. 'mm', 'bar', 'L/min').
        to_unit:   Target unit string (e.g. 'm', 'Pa', 'm^3/s').

    Returns:
        float: Converted magnitude in ``to_unit``.

    Example:
        >>> to_si(50.0, 'mm', 'm')
        0.05
        >>> to_si(1.0, 'bar', 'Pa')
        100000.0
    """
    quantity = Q_(value, from_unit)
    return float(quantity.to(to_unit).magnitude)


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert temperatures correctly (handles offset units like °C and °F).

    Pint handles offset unit conversions via ``to()``; this wrapper makes the
    API explicit for temperature, which is a common source of bugs.

    Args:
        value:     Temperature magnitude.
        from_unit: One of 'degC', 'degF', 'kelvin', 'degR' (Rankine).
        to_unit:   Same options.

    Returns:
        float: Converted temperature.

    Example:
        >>> convert_temperature(100, 'degC', 'kelvin')
        373.15
    """
    quantity = Q_(value, from_unit)
    return float(quantity.to(to_unit).magnitude)
