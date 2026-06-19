"""
apps/app_tribology/services.py
===============================
Mathematical service for gear geometry and Elastohydrodynamic Lubrication (EHL) analysis.
"""

import math
import numpy as np

class TribologyService:
    """
    Solves spur gear geometry (AGMA/ISO standards) and EHL minimum film thickness
    using the Dowson-Higginson formulation.
    """

    def __init__(
        self,
        module_mm: float,
        pinion_teeth: int,
        gear_teeth: int,
        pinion_rpm: float,
        viscosity_pa_s: float,
        roughness_um: float,
        load_n: float,
        pressure_angle_deg: float = 20.0,
        face_width_mm: float = 20.0,
        youngs_modulus_gpa: float = 210.0,
        poissons_ratio: float = 0.3,
        alpha_pa_inv: float = 2.2e-8,
    ):
        self.m = module_mm
        self.z1 = pinion_teeth
        self.z2 = gear_teeth
        self.n1 = pinion_rpm
        self.eta0 = viscosity_pa_s
        self.rq = roughness_um
        self.ft = load_n
        self.phi_deg = pressure_angle_deg
        self.phi_rad = math.radians(pressure_angle_deg)
        self.b = face_width_mm / 1000.0  # mm to meters
        self.E = youngs_modulus_gpa * 1e9  # GPa to Pa
        self.nu = poissons_ratio
        self.alpha = alpha_pa_inv

    def compute_geometry(self):
        """Calculates standard gear pitch diameters, center distance, and gear ratio."""
        d1 = self.m * self.z1  # Pitch diameter Pinion (mm)
        d2 = self.m * self.z2  # Pitch diameter Gear (mm)
        a = (d1 + d2) / 2.0     # Center distance (mm)
        ratio = self.z2 / self.z1
        return {
            "pitch_diameter_pinion_mm": d1,
            "pitch_diameter_gear_mm": d2,
            "center_distance_mm": a,
            "gear_ratio": ratio,
        }

    def compute_ehl(self, rpm=None):
        """
        Computes entrainment velocity, EHL minimum film thickness (h_min),
        Lambda ratio, and lubrication regime for a specific RPM.
        """
        if rpm is None:
            rpm = self.n1

        # Gear Geometry
        geom = self.compute_geometry()
        d1_m = geom["pitch_diameter_pinion_mm"] / 1000.0
        d2_m = geom["pitch_diameter_gear_mm"] / 1000.0

        # Equivalent curvature radius at pitch point
        r1_c = (d1_m / 2.0) * math.sin(self.phi_rad)
        r2_c = (d2_m / 2.0) * math.sin(self.phi_rad)
        r_reduced = (r1_c * r2_c) / (r1_c + r2_c) if (r1_c + r2_c) > 0 else 1.0e-5

        # Reduced Elastic Modulus E'
        # 2 / E' = (1 - nu1^2)/E1 + (1 - nu2^2)/E2
        e_reduced = 2.0 / (((1.0 - self.nu**2) / self.E) + ((1.0 - self.nu**2) / self.E))

        # Linear speed at pitch circle (m/s)
        omega1 = (2.0 * math.pi * rpm) / 60.0
        v_pitch = omega1 * (d1_m / 2.0)
        u_entrainment = v_pitch  # Entrainment velocity is equal to pitch speed

        # Normal load
        f_normal = self.ft / math.cos(self.phi_rad) if math.cos(self.phi_rad) > 0 else self.ft

        # Dimensionless Dowson-Higginson parameters
        # U = Speed, G = Material, W = Load
        u_param = (self.eta0 * u_entrainment) / (e_reduced * r_reduced) if (e_reduced * r_reduced) > 0 else 0.0
        g_param = self.alpha * e_reduced
        w_param = f_normal / (e_reduced * r_reduced * self.b) if (e_reduced * r_reduced * self.b) > 0 else 1e-15

        # Dowson-Higginson minimum film thickness formula
        # H_min = h_min / R' = 2.65 * U^0.7 * G^0.54 * W^-0.13
        if u_param > 0 and w_param > 0:
            h_min_ratio = 2.65 * (u_param**0.7) * (g_param**0.54) * (w_param**-0.13)
            h_min_m = h_min_ratio * r_reduced
        else:
            h_min_m = 0.0

        h_min_um = h_min_m * 1e6  # Convert to micrometers
        lambda_val = h_min_um / self.rq if self.rq > 0 else 0.0

        # Lubrication Regime
        if lambda_val < 1.0:
            regime = "Limítrofe"
            regime_code = "boundary"
        elif lambda_val < 3.0:
            regime = "Misto"
            regime_code = "mixed"
        else:
            regime = "Hidrodinâmico Completo"
            regime_code = "hydrodynamic"

        return {
            "pitch_line_velocity_m_s": v_pitch,
            "entrainment_velocity_m_s": u_entrainment,
            "equivalent_radius_m": r_reduced,
            "normal_load_n": f_normal,
            "u_dimensionless": u_param,
            "g_dimensionless": g_param,
            "w_dimensionless": w_param,
            "h_min_m": h_min_m,
            "h_min_um": h_min_um,
            "lambda_parameter": lambda_val,
            "regime": regime,
            "regime_code": regime_code,
        }

    def compute(self):
        """Runs complete calculations and returns results suitable for API serialization."""
        geom = self.compute_geometry()
        ehl = self.compute_ehl()
        sweep = self.compute_sweep()

        return {
            "geometry": geom,
            "ehl": ehl,
            "sweep": sweep,
        }

    def compute_sweep(self):
        """Generates Lambda parameter values for pinion speeds from 100 to 5000 RPM."""
        rpms = np.linspace(100, 5000, 50)
        lambdas = []
        h_mins = []
        for rpm in rpms:
            res = self.compute_ehl(rpm=float(rpm))
            lambdas.append(float(res["lambda_parameter"]))
            h_mins.append(float(res["h_min_um"]))

        return {
            "rpms": rpms.tolist(),
            "lambdas": lambdas,
            "h_mins": h_mins,
        }
