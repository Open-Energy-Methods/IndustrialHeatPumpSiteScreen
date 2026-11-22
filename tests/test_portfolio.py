import unittest
from dataclasses import replace
from site_screen.pinch import ProcessStream
from site_screen.integration import ProcessSite,Source,TariffBlock
from site_screen.portfolio import Sensitivity,enumerate_scenarios

class Portfolio(unittest.TestCase):
    def site(self):
        return ProcessSite("S",(
            ProcessStream("hot", "hot",120,60,1.),
            ProcessStream("cold","cold",60,170,3.)),
            Source(95,65,10.),(TariffBlock("day",4000,.07),TariffBlock("night",1000,.18)),
            boiler_efficiency=.9,fuel_eur_kWh=.1)
    def test_repeatable_scenario_count_and_provenance(self):
        s=self.site()
        x=enumerate_scenarios(s,Sensitivity())
        self.assertEqual(x["total_cases"],54)
        self.assertEqual(len({y["scenario_id"] for y in x["scenarios"]}),54)
        self.assertEqual(x,enumerate_scenarios(s,Sensitivity()))
        self.assertTrue(all(y["result"]["source_heat_balance_verified"] for y in x["scenarios"]))
        self.assertTrue(all(y["result"]["process_heat_balance_verified"] for y in x["scenarios"]))
    def test_non_dominated_not_cross_price_scenarios(self):
        x=enumerate_scenarios(self.site(),
            Sensitivity(hp_nameplates_kW=(250.,500.),carnot_fractions=(.45,),
                        electricity_price_multipliers=(1.,2.),pinch_dt_min_K=(10.,)))
        self.assertEqual(x["total_cases"],4)
        self.assertTrue(x["no_cross_scenario_Pareto_comparison"])
        self.assertGreaterEqual(sum(row["non_dominated_within_identical_assumptions"]
                for row in x["scenarios"]),2)
    def test_reject_negative_overwide(self):
        with self.assertRaises(ValueError):
            Sensitivity(hp_nameplates_kW=(-1.,))
        with self.assertRaises(ValueError):
            Sensitivity(carnot_fractions=(1.2,))
        with self.assertRaises(ValueError):
            Sensitivity(hp_nameplates_kW=tuple(range(1,501)),
                electricity_price_multipliers=(.5,1.,2.,4.,8.))

if __name__=="__main__":unittest.main()
