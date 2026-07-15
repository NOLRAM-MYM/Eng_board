"""
apps/app_chemistry/tests.py
===========================
Tests for the Chemistry Periodic Table & Reaction Simulator.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from .services import ElementPropertyService, ChemistrySimulationService, FormulaParserService


@pytest.fixture
def api_client():
    return APIClient()


class TestElementPropertyService:
    def test_get_element_by_symbol(self):
        service = ElementPropertyService()
        el = service.get_element("Fe")
        assert el.symbol == "Fe"
        assert el.name == "Iron"
        assert el.atomic_number == 26
        assert el.atomic_mass > 55.0

    def test_get_element_by_number(self):
        service = ElementPropertyService()
        el = service.get_element(6)
        assert el.symbol == "C"
        assert el.name == "Carbon"
        assert el.atomic_number == 6


class TestChemistrySimulationService:
    def test_simulate_bond_water(self):
        res = ChemistrySimulationService.run_bond("H2O")
        assert res["formula"] == "H2O"
        assert res["name"] == "Água"
        assert res["mass"] == 18.015
        assert res["bond_type"] == "Covalente Polar"
        assert len(res["atoms"]) == 3

    def test_simulate_bond_nacl(self):
        res = ChemistrySimulationService.run_bond("NaCl")
        assert res["formula"] == "NaCl"
        assert res["name"] == "Cloreto de Sódio (Sal de Cozinha)"
        assert res["bond_type"] == "Iônica"
        assert len(res["atoms"]) == 2

    def test_simulate_reaction_sodium_water(self):
        res = ChemistrySimulationService.run_reaction("sodium_water")
        assert res["id"] == "sodium_water"
        assert "NaOH" in res["product_name"]
        assert "H2" in res["byproduct_name"]
        assert res["product_mass"] == 39.997
        assert res["byproduct_mass"] == 2.016


class TestFormulaParserService:
    def test_parse_simple_formula(self):
        counts = FormulaParserService.parse_formula("H2O")
        assert counts == {"H": 2, "O": 1}

    def test_parse_formula_with_parentheses(self):
        counts = FormulaParserService.parse_formula("Fe2(SO4)3")
        assert counts == {"Fe": 2, "S": 3, "O": 12}

    def test_molar_mass_glucose_matches_known_value(self):
        result = FormulaParserService.compute_molar_mass("C6H12O6")
        assert result["molar_mass_g_mol"] == pytest.approx(180.156, rel=1e-3)

    def test_molar_mass_nacl_matches_legacy_static_value(self):
        """Cross-check the dynamic parser against the static value already
        hardcoded in ChemistrySimulationService.COMPOUNDS['NaCl']['mass']."""
        result = FormulaParserService.compute_molar_mass("NaCl")
        legacy = ChemistrySimulationService.COMPOUNDS["NaCl"]["mass"]
        assert result["molar_mass_g_mol"] == pytest.approx(legacy, rel=1e-2)

    def test_mass_percent_sums_to_100(self):
        result = FormulaParserService.compute_molar_mass("CH4")
        total_pct = sum(c["mass_percent"] for c in result["composition"])
        assert total_pct == pytest.approx(100.0, rel=1e-6)

    def test_unknown_element_raises(self):
        with pytest.raises(ValueError):
            FormulaParserService.compute_molar_mass("Xx2O")

    def test_empty_formula_raises(self):
        with pytest.raises(ValueError):
            FormulaParserService.parse_formula("")


class TestChemistryAPI:
    def test_get_elements_list(self, api_client):
        url = reverse("chemistry:periodic-table-list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["status"] == "success"
        symbols = [el["symbol"] for el in response.data["data"]]
        assert "Fe" in symbols
        assert "H" in symbols
        assert "O" in symbols

    def test_get_element_detail(self, api_client):
        url = reverse("chemistry:element-property", kwargs={"identifier": "Fe"})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert response.data["data"]["symbol"] == "Fe"

    def test_simulate_bond_api_success(self, api_client):
        url = reverse("chemistry:chemistry-simulate")
        payload = {"mode": "bond", "formula": "H2O"}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert response.data["data"]["formula"] == "H2O"

    def test_simulate_reaction_api_success(self, api_client):
        url = reverse("chemistry:chemistry-simulate")
        payload = {"mode": "reaction", "reaction_id": "sodium_water"}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert response.data["data"]["id"] == "sodium_water"

    def test_simulate_api_validation_error(self, api_client):
        url = reverse("chemistry:chemistry-simulate")
        payload = {"mode": "bond"}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400
        assert response.data["status"] == "error"
        assert "formula" in response.data["errors"]

    def test_stoichiometry_api_success(self, api_client):
        url = reverse("chemistry:stoichiometry")
        response = api_client.post(url, {"formula": "C6H12O6"}, format="json")
        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert response.data["data"]["molar_mass_g_mol"] == pytest.approx(180.156, rel=1e-3)

    def test_stoichiometry_api_invalid_formula_returns_400(self, api_client):
        url = reverse("chemistry:stoichiometry")
        response = api_client.post(url, {"formula": "Xx2O"}, format="json")
        assert response.status_code == 400
        assert response.data["status"] == "error"
