"""
apps/app_tribology/tests.py
===========================
Unit and integration tests for the Tribology and Gears module.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .services import TribologyService


class TribologyNumericalTests(TestCase):
    """Verifies gear design calculations and EHL lubrication status logic."""

    def test_gear_geometry(self):
        """Checks pitch diameters, gear ratio, and center distance calculations."""
        service = TribologyService(
            module_mm=3.0,
            pinion_teeth=20,
            gear_teeth=40,
            pinion_rpm=1000.0,
            viscosity_pa_s=0.05,
            roughness_um=0.4,
            load_n=1000.0,
        )
        geom = service.compute_geometry()
        self.assertEqual(geom["pitch_diameter_pinion_mm"], 60.0)
        self.assertEqual(geom["pitch_diameter_gear_mm"], 120.0)
        self.assertEqual(geom["center_distance_mm"], 90.0)
        self.assertEqual(geom["gear_ratio"], 2.0)

    def test_ehl_regime_effects(self):
        """Verifies that faster rotational speed yields thicker oil film thickness."""
        service_slow = TribologyService(
            module_mm=3.0,
            pinion_teeth=20,
            gear_teeth=40,
            pinion_rpm=100.0,
            viscosity_pa_s=0.04,
            roughness_um=0.5,
            load_n=5000.0,
        )
        res_slow = service_slow.compute_ehl()

        service_fast = TribologyService(
            module_mm=3.0,
            pinion_teeth=20,
            gear_teeth=40,
            pinion_rpm=3000.0,
            viscosity_pa_s=0.04,
            roughness_um=0.5,
            load_n=5000.0,
        )
        res_fast = service_fast.compute_ehl()

        # Thicker oil film at higher speeds
        self.assertGreater(res_fast["h_min_um"], res_slow["h_min_um"])
        self.assertGreater(res_fast["lambda_parameter"], res_slow["lambda_parameter"])


class TribologyAPITests(APITestCase):
    """Verifies that POST calculation endpoints validate parameters and handle errors."""

    def setUp(self):
        self.calc_url = reverse("tribology:tribology-calculate")

    def test_calculation_endpoint_success(self):
        """Checks successful API request returns correct JSON geometry and EHL structures."""
        payload = {
            "module_mm": 2.5,
            "pinion_teeth": 24,
            "gear_teeth": 48,
            "pinion_rpm": 1200.0,
            "viscosity_pa_s": 0.08,
            "roughness_um": 0.35,
            "load_n": 1500.0,
        }
        response = self.client.post(self.calc_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data["data"]
        self.assertIn("geometry", data)
        self.assertIn("ehl", data)
        self.assertIn("sweep", data)
        
        # Verify geometry values
        self.assertEqual(data["geometry"]["pitch_diameter_pinion_mm"], 60.0)
        self.assertEqual(data["geometry"]["center_distance_mm"], 90.0)

    def test_calculation_endpoint_validation_error(self):
        """Checks negative/invalid inputs are rejected with 400 Bad Request."""
        payload = {
            "module_mm": -1.0,  # Negative modules are invalid
            "pinion_teeth": 15,
            "gear_teeth": 30,
            "pinion_rpm": 1500.0,
            "viscosity_pa_s": 0.04,
            "roughness_um": 0.4,
            "load_n": 2000.0,
        }
        response = self.client.post(self.calc_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
