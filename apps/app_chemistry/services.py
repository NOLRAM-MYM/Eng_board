"""
apps/app_chemistry/services.py
================================
Atomic & Molecular property service using pymatgen, ASE, and mendeleev.

Libraries:
    - mendeleev:  Precise periodic table data (ionisation energies, radii, etc.)
    - pymatgen:   Crystal structure analysis, composition parsing
    - ase:        Atomic simulation, bond lengths, molecular geometry

Modules:
    - ElementPropertyService:   Fetch all properties of a periodic table element
    - MoleculeGeometryService:  Build atomic positions for simple molecules
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ElementData:
    """Structured data for a single periodic table element."""
    symbol: str
    name: str
    atomic_number: int
    atomic_mass: float           # u (unified atomic mass units)
    period: int
    group: int | None
    electron_configuration: str
    electronegativity: float | None   # Pauling scale
    atomic_radius_pm: float | None    # Covalent radius in pm
    ionisation_energy_ev: float | None  # First ionisation energy in eV
    melting_point_k: float | None
    boiling_point_k: float | None
    density_g_cm3: float | None
    oxidation_states: list[int] = field(default_factory=list)


class ElementPropertyService:
    """
    Retrieve complete properties for a chemical element by symbol or atomic number.

    Uses mendeleev for precise, IUPAC-approved data with a local JSON fallback if unavailable.
    """

    def get_element(self, identifier: str | int) -> ElementData:
        """
        Fetch element data.

        Args:
            identifier: Element symbol (e.g., 'Fe') or atomic number (e.g., 26).

        Returns:
            ElementData dataclass with all available properties.
        """
        try:
            from mendeleev import element as mendeleev_element
            el = mendeleev_element(identifier)
            
            # Convert ionisation energy from kJ/mol to eV
            ie_ev = None
            if el.ionenergies and 1 in el.ionenergies:
                # 1 kJ/mol = 0.01036 eV/atom
                ie_ev = el.ionenergies[1] * 0.010364

            return ElementData(
                symbol                = el.symbol,
                name                  = el.name,
                atomic_number         = el.atomic_number,
                atomic_mass           = float(el.atomic_weight) if el.atomic_weight else 0.0,
                period                = el.period,
                group                 = el.group_id,
                electron_configuration= el.ec.conf if hasattr(el, 'ec') else str(el.econf),
                electronegativity     = float(el.electronegativity('pauling') or 0) or None,
                atomic_radius_pm      = float(el.covalent_radius_pyykko or 0) or None,
                ionisation_energy_ev  = ie_ev,
                melting_point_k       = float(el.melting_point) if el.melting_point else None,
                boiling_point_k       = float(el.boiling_point) if el.boiling_point else None,
                density_g_cm3         = float(el.density) if el.density else None,
                oxidation_states      = list(el.oxistates) if el.oxistates else [],
            )
        except ImportError:
            # Fall back to local periodic table database
            from .fallback_db import get_element_fallback
            return get_element_fallback(identifier)
