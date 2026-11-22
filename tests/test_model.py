"""Independent algebraic and limiting-case tests, not experimental validation."""
import unittest
from dataclasses import replace
from math import isclose

from site_screen.model import Site, screen_site


def sample(**overrides):
    base = dict(site_id="synthetic_unit",source_supply_C=80,
        source_return_C=60,source_flow_kg_s=5,
        process_return_C=110,process_supply_C=150,
        process_demand_kW=1000,operating_hours_per_year=5000,
        electricity_eur_per_kWh=0.08,boiler_fuel_eur_per_kWh=0.10,
        boiler_efficiency=0.90)
    base.update(overrides)
    return Site(**base)


class ThermodynamicScreens(unittest.TestCase):
    def test_full_demand_source_and_electricity_conservation(self):
        z = screen_site(sample())
        self.assertEqual(z["status"], "full_heat_demand_proxy")
        self.assertEqual(z["heat_pump_heat_kW"], 1000)
        self.assertAlmostEqual(z["first_law_residual_kW"], 0, places=8)
        self.assertAlmostEqual(z["heat_pump_heat_kW"],
            z["recovered_source_heat_kW"] + z["compressor_electric_kW"])
        self.assertLessEqual(z["recovered_source_heat_kW"],
                             z["source_heat_available_kW"] + 1e-9)
        self.assertFalse(z["refrigerant_compressor_map_verified"])
        self.assertFalse(z["auxiliaries_included"])
        self.assertFalse(z["industrial_pinches_resolved"])

    def test_exact_COP_definition(self):
        site = sample()
        z = screen_site(site)
        T_hot = site.process_supply_C + site.hot_approach_K + 273.15
        T_cold = site.source_return_C - site.cold_approach_K + 273.15
        self.assertAlmostEqual(z["COP_assumed"],
                               0.45 * T_hot / (T_hot - T_cold))
        self.assertLess(z["COP_assumed"], z["carnot_heating_COP_ideal"])

    def test_source_limited_preserves_source_energy(self):
        z = screen_site(sample(source_flow_kg_s=0.2, process_demand_kW=2000))
        self.assertEqual(z["status"], "source_limited_proxy")
        self.assertAlmostEqual(z["recovered_source_heat_kW"],
                               z["source_heat_available_kW"])
        self.assertGreater(z["residual_boiler_heat_kW"], 0)
        self.assertAlmostEqual(z["residual_boiler_heat_kW"] +
                               z["heat_pump_heat_kW"], 2000)

    def test_annual_fuel_displacement_is_not_double_counted(self):
        s = sample()
        z = screen_site(s)
        self.assertAlmostEqual(
            z["baseline_boiler_fuel_kWh_per_year"] -
            z["hybrid_boiler_fuel_kWh_per_year"],
            z["boiler_fuel_displaced_kWh_per_year"])
        self.assertAlmostEqual(z["annual_net_savings_before_capex_eur"],
            z["annual_fuel_cost_savings_eur"] -
            z["annual_hp_electricity_cost_eur"] -
            s.incremental_opex_eur_per_year)

    def test_break_even_ceiling_is_pv_of_savings(self):
        s = sample(lifetime_years=2, discount_rate=0.10)
        z = screen_site(s)
        factor = 1 / 1.10 + 1 / 1.10**2
        self.assertAlmostEqual(
            z["pv_net_savings_before_capex_eur"],
            z["annual_net_savings_before_capex_eur"] * factor)
        self.assertEqual(z["positive_economic_break_even_ceiling"],
                         z["pv_net_savings_before_capex_eur"] > 0)
        self.assertAlmostEqual(z["break_even_installed_capex_ceiling_eur"],
            max(0, z["pv_net_savings_before_capex_eur"]))

    def test_zero_discount_and_unfavorable_pricing(self):
        s = sample(discount_rate=0, lifetime_years=10,
                   electricity_eur_per_kWh=0.5,
                   boiler_fuel_eur_per_kWh=0.01)
        z = screen_site(s)
        self.assertLess(z["annual_net_savings_before_capex_eur"], 0)
        self.assertEqual(z["break_even_installed_capex_ceiling_eur"], 0)
        self.assertAlmostEqual(z["pv_net_savings_before_capex_eur"],
            10 * z["annual_net_savings_before_capex_eur"])

    def test_tariff_break_even_yields_zero_operating_savings(self):
        s = sample(incremental_opex_eur_per_year=20000)
        first = screen_site(s)
        s = replace(s,electricity_eur_per_kWh=first["break_even_electricity_price_eur_per_kWh"])
        self.assertAlmostEqual(
            screen_site(s)["annual_net_savings_before_capex_eur"], 0, places=6)

    def test_too_low_assumed_COP_is_explicitly_rejected(self):
        z = screen_site(sample(assumed_carnot_fraction=0.1))
        self.assertEqual(z["status"], "rejected")
        self.assertEqual(z["reasons"], ["assumed_COP_at_or_below_one"])

    def test_bad_fields_fail_closed(self):
        for o in (dict(boiler_efficiency=1.5),dict(source_flow_kg_s=-1),
                  dict(source_return_C=85),dict(operating_hours_per_year=9000),
                  dict(process_supply_C=100),dict(assumed_carnot_fraction=float("nan")),
                  dict(discount_rate=-0.01),dict(lifetime_years=0)):
            with self.subTest(o=o), self.assertRaises(ValueError):
                sample(**o)

    def test_ranking_does_not_claim_vendor_price_or_RTE(self):
        z = screen_site(sample())
        self.assertFalse(z["manufacturer_capex_estimated"])
        self.assertFalse(z["refrigerant_compressor_map_verified"])
        self.assertNotIn("Carnot_battery_RTE", z)
        self.assertNotIn("measured_COP", z)


if __name__ == "__main__":
    unittest.main()
