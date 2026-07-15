"""
apps/app_materials/tests.py
=============================
Tests for the Materials & FEA beam deflection module.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from .services import BeamDeflectionService


@pytest.fixture
def api_client():
    return APIClient()


class TestBeamDeflectionService:
    def test_point_centre_matches_closed_form(self):
        svc = BeamDeflectionService(
            length_m=5.0, youngs_modulus_gpa=200.0,
            second_moment_m4=8.33e-6, load_kn=50.0, load_type='point_centre',
        )
        result = svc.compute()
        EI = 200e9 * 8.33e-6
        expected_mm = (50000 * 5.0 ** 3 / (48 * EI)) * 1000
        assert result['max_deflection_mm'] == pytest.approx(expected_mm, rel=1e-6)
        assert result['load_type'] == 'point_centre'

    def test_uniform_matches_closed_form(self):
        svc = BeamDeflectionService(
            length_m=4.0, youngs_modulus_gpa=70.0,
            second_moment_m4=2.0e-5, load_kn=20.0, load_type='uniform',
        )
        result = svc.compute()
        EI = 70e9 * 2.0e-5
        q = 20000 / 4.0
        expected_mm = (5 * q * 4.0 ** 4 / (384 * EI)) * 1000
        assert result['max_deflection_mm'] == pytest.approx(expected_mm, rel=1e-6)

    def test_cantilever_point_matches_closed_form(self):
        svc = BeamDeflectionService(
            length_m=5.0, youngs_modulus_gpa=200.0,
            second_moment_m4=8.33e-6, load_kn=50.0, load_type='cantilever_point',
        )
        result = svc.compute()
        EI = 200e9 * 8.33e-6
        expected_mm = (50000 * 5.0 ** 3 / (3 * EI)) * 1000
        assert result['max_deflection_mm'] == pytest.approx(expected_mm, rel=1e-6)

    def test_cantilever_uniform_matches_closed_form(self):
        svc = BeamDeflectionService(
            length_m=4.0, youngs_modulus_gpa=70.0,
            second_moment_m4=2.0e-5, load_kn=20.0, load_type='cantilever_uniform',
        )
        result = svc.compute()
        EI = 70e9 * 2.0e-5
        q = 20000 / 4.0
        expected_mm = (q * 4.0 ** 4 / (8 * EI)) * 1000
        assert result['max_deflection_mm'] == pytest.approx(expected_mm, rel=1e-6)

    def test_cantilever_point_deflects_more_than_simply_supported(self):
        """A cantilever with a free end always deflects more than a simply
        supported beam under the same magnitude point load (PL^3/3EI > PL^3/48EI)."""
        common = dict(length_m=5.0, youngs_modulus_gpa=200.0,
                      second_moment_m4=8.33e-6, load_kn=50.0)
        simply_supported = BeamDeflectionService(**common, load_type='point_centre').compute()
        cantilever = BeamDeflectionService(**common, load_type='cantilever_point').compute()
        assert cantilever['max_deflection_mm'] > simply_supported['max_deflection_mm']

    def test_unsupported_load_type_raises(self):
        svc = BeamDeflectionService(
            length_m=5.0, youngs_modulus_gpa=200.0,
            second_moment_m4=8.33e-6, load_kn=50.0, load_type='not_a_real_type',
        )
        with pytest.raises(ValueError):
            svc.compute()


class TestBeamDeflectionAPI:
    def test_valid_payload_returns_200(self, api_client):
        url = reverse('materials:beam-deflection')
        payload = {
            "length_m": 5.0, "youngs_modulus_gpa": 200.0,
            "second_moment_m4": 8.33e-6, "load_kn": 50.0,
            "load_type": "point_centre",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert response.data["data"]["max_deflection_mm"] > 0

    def test_cantilever_payload_returns_200(self, api_client):
        url = reverse('materials:beam-deflection')
        payload = {
            "length_m": 3.0, "youngs_modulus_gpa": 200.0,
            "second_moment_m4": 5.0e-6, "load_kn": 10.0,
            "load_type": "cantilever_uniform",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert response.data["data"]["load_type"] == "cantilever_uniform"

    def test_negative_length_returns_400(self, api_client):
        url = reverse('materials:beam-deflection')
        payload = {
            "length_m": -5.0, "youngs_modulus_gpa": 200.0,
            "second_moment_m4": 8.33e-6, "load_kn": 50.0,
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400
        assert response.data["status"] == "error"
        assert "length_m" in response.data["errors"]

    def test_zero_second_moment_returns_400_not_500(self, api_client):
        """Regression test: I=0 must not cause a raw 500 (ZeroDivisionError in EI)."""
        url = reverse('materials:beam-deflection')
        payload = {
            "length_m": 5.0, "youngs_modulus_gpa": 200.0,
            "second_moment_m4": 0.0, "load_kn": 50.0,
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400

    def test_negative_youngs_modulus_returns_400(self, api_client):
        url = reverse('materials:beam-deflection')
        payload = {
            "length_m": 5.0, "youngs_modulus_gpa": -200.0,
            "second_moment_m4": 8.33e-6, "load_kn": 50.0,
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400

    def test_invalid_load_type_returns_400(self, api_client):
        url = reverse('materials:beam-deflection')
        payload = {
            "length_m": 5.0, "youngs_modulus_gpa": 200.0,
            "second_moment_m4": 8.33e-6, "load_kn": 50.0,
            "load_type": "not_a_real_type",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400
