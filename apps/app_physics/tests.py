"""
apps/app_physics/tests.py
==========================
Unit and integration tests for the Physics module.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from .services import ProjectileMotionService


@pytest.fixture
def standard_projectile_service():
    """Baseball at 45 degrees launched at 45 m/s."""
    return ProjectileMotionService(
        velocity_m_s=45.0,
        angle_deg=45.0,
        mass_kg=0.145,
        diameter_m=0.074,
        drag_coefficient=0.30
    )


@pytest.fixture
def api_client():
    return APIClient()


# ===========================================================================
# Service Tests
# ===========================================================================

class TestProjectileMotionService:
    def test_drag_reduces_range(self, standard_projectile_service):
        """Verify that atmospheric drag reduces the projectile range compared to vacuum."""
        result = standard_projectile_service.compute()
        stats = result['stats']
        
        assert stats['range_drag_m'] < stats['range_vacuum_m']
        assert stats['height_drag_m'] < stats['height_vacuum_m']
        assert stats['time_drag_s'] < stats['time_vacuum_s']

    def test_increasing_drag_coefficient(self):
        """Verify that higher drag coefficient further degrades the range."""
        service_low_drag = ProjectileMotionService(
            velocity_m_s=50.0, angle_deg=45.0, mass_kg=1.0, diameter_m=0.1, drag_coefficient=0.1
        )
        service_high_drag = ProjectileMotionService(
            velocity_m_s=50.0, angle_deg=45.0, mass_kg=1.0, diameter_m=0.1, drag_coefficient=1.0
        )
        
        res_low = service_low_drag.compute()
        res_high = service_high_drag.compute()
        
        assert res_high['stats']['range_drag_m'] < res_low['stats']['range_drag_m']
        assert res_high['stats']['height_drag_m'] < res_low['stats']['height_drag_m']


# ===========================================================================
# API Integration Tests
# ===========================================================================

class TestProjectileMotionAPI:
    def test_calculate_endpoint_success(self, api_client):
        """Test API successfully computes trajectory for valid payload."""
        url = reverse('physics:projectile-calculate')
        payload = {
            "velocity_m_s": 45.0,
            "angle_deg": 45.0,
            "mass_kg": 0.145,
            "diameter_m": 0.074,
            "drag_coefficient": 0.30
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 200
        
        data = response.data
        assert data['status'] == 'success'
        assert 'x_vacuum' in data['data']
        assert 'x_drag' in data['data']
        assert 'stats' in data['data']
        assert data['data']['stats']['range_drag_m'] > 0

    def test_calculate_endpoint_invalid_angle(self, api_client):
        """Test API rejects out-of-bound launch angle."""
        url = reverse('physics:projectile-calculate')
        payload = {
            "velocity_m_s": 45.0,
            "angle_deg": 95.0,  # invalid angle (> 89.9)
            "mass_kg": 0.145,
            "diameter_m": 0.074,
            "drag_coefficient": 0.30
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 400
        assert response.data['status'] == 'error'
        assert 'angle_deg' in response.data['errors']

    def test_calculate_endpoint_negative_mass(self, api_client):
        """Test API rejects negative mass."""
        url = reverse('physics:projectile-calculate')
        payload = {
            "velocity_m_s": 45.0,
            "angle_deg": 45.0,
            "mass_kg": -1.0,  # invalid negative mass
            "diameter_m": 0.074,
            "drag_coefficient": 0.30
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 400
        assert response.data['status'] == 'error'
        assert 'mass_kg' in response.data['errors']
