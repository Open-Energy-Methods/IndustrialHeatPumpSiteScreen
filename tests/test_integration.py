"""Thermoeconomics tests use analytic counterfactuals, not fitted site data."""
import unittest
from dataclasses import replace
from site_screen.pinch import ProcessStream
from site_screen.integration import Source,TariffBlock,ProcessSite,evaluate_site

def site(*,blocks=None,hot=True,source_cap=10.,capacity=500.,aux_frac=.05,aux_kW=0.):
    streams=(ProcessStream("process feed","cold",100,160,5),)
    if hot:
        streams+=(ProcessStream("recovered hot","hot",100,70,2.),)
    return ProcessSite(site_id="synthetic",streams=streams,
        independent_source=Source(90,60,source_cap),
        tariff_blocks=blocks or (
            TariffBlock("cheap",3000,.04),
            TariffBlock("expensive",3000,.40)),
        boiler_efficiency=.9,fuel_eur_kWh=.1,
        hp_nameplate_kW=capacity,
        auxiliary_electric_fraction_of_compressor=aux_frac,
        hp_fixed_auxiliary_kW_when_on=aux_kW)


class ThermoeconomicTests(unittest.TestCase):
    def test_physical_heat_and_tariff_choice(self):
        x=evaluate_site(site())
        self.assertTrue(x["process_heat_balance_verified"])
        self.assertTrue(x["source_heat_balance_verified"])
        cheap,expensive=x["dispatch_blocks"]
        self.assertTrue(cheap["HP_dispatched_on"])
        self.assertFalse(expensive["HP_dispatched_on"])
        self.assertEqual(expensive["hp_delivered_kW"],0.)
        self.assertEqual(expensive["boiler_remaining_kW"],
                         expensive["baseline_external_heating_kW"])
        self.assertGreater(cheap["hp_delivered_kW"],0.)
        self.assertLessEqual(cheap["hp_delivered_kW"],cheap["independent_source_available_kW"]/(1-1/x["assumed_COP"])+1e-9)
        self.assertFalse(x["compressor_qualified"])
        self.assertFalse(x["process_HEN_built_or_capex_priced"])
    def test_independent_source_prevents_double_count(self):
        a=evaluate_site(site(hot=True))
        b=evaluate_site(site(hot=False))
        self.assertGreater(a["process_heat_cascade"]["maximum_internal_process_heat_recovery_kW"],
                           b["process_heat_cascade"]["maximum_internal_process_heat_recovery_kW"])
        self.assertEqual(a["independent_source"],b["independent_source"])
        self.assertEqual(a["dispatch_blocks"][0]["independent_source_available_kW"],
                         b["dispatch_blocks"][0]["independent_source_available_kW"])
    def test_capped_source_and_nameplate(self):
        s=site(source_cap=.5,capacity=50.)
        x=evaluate_site(s)
        for b in x["dispatch_blocks"]:
            self.assertLessEqual(b["hp_delivered_kW"],50.+1e-8)
            self.assertLessEqual(b["hp_external_source_heat_kW"],
                                 b["independent_source_available_kW"]+1e-8)
    def test_demand_scale_and_zero_source(self):
        s=site(blocks=(TariffBlock("zero",400,.02,0.,1.),
                  TariffBlock("no_source",300,.02,1.,0.)))
        x=evaluate_site(s)
        self.assertEqual(x["annual"]["heat_pump_delivered_kWh"],0.)
        self.assertEqual(x["dispatch_blocks"][0]["baseline_external_heating_kW"],0.)
        self.assertEqual(x["dispatch_blocks"][1]["hp_max_thermal_kW"],0.)
    def test_annual_price_and_fixed_opex_balance(self):
        s=site()
        x=evaluate_site(s)
        annual=x["annual"]
        independent=sum(b["net_hourly_cost_saving_eur"]*b["hours"] for b in x["dispatch_blocks"])
        self.assertAlmostEqual(x["annual_net_savings_eur"],
                               independent-s.incremental_fixed_opex_eur_year)
        self.assertAlmostEqual(annual["baseline_heating_utility_kWh"]-
            annual["residual_heating_utility_kWh"],annual["heat_pump_delivered_kWh"])
        self.assertAlmostEqual(annual["heat_pump_delivered_kWh"],
            annual["heat_pump_compressor_kWh"]+annual["external_source_heat_kWh"])
    def test_negative_price_is_operating_incentive_not_infinite_heat(self):
        s=site(blocks=(TariffBlock("negative",100,-.1),))
        x=evaluate_site(s);b=x["dispatch_blocks"][0]
        self.assertTrue(b["HP_dispatched_on"])
        self.assertLessEqual(b["hp_delivered_kW"],s.hp_nameplate_kW)
    def test_auxiliary_can_reverse_dispatch(self):
        s=site(blocks=(TariffBlock("price",100,.10),),aux_kW=1e5)
        z=evaluate_site(s)
        self.assertFalse(z["dispatch_blocks"][0]["HP_dispatched_on"])
        self.assertEqual(z["annual"]["heat_pump_auxiliary_kWh"],0.)
    def test_pinch_higher_dt_cannot_improve_recovery(self):
        a=evaluate_site(site())
        b=evaluate_site(replace(site(),pinch_dt_min_K=30.))
        self.assertGreaterEqual(b["process_heat_cascade"]["minimum_external_heating_kW"],
                                a["process_heat_cascade"]["minimum_external_heating_kW"]-1e-8)
    def test_no_external_heat_demand_means_no_hp(self):
        streams=(ProcessStream("cooling","hot",200,100,1.),
                 ProcessStream("heating","cold",50,150,1.))
        s=replace(site(),streams=streams)
        z=evaluate_site(s)
        self.assertEqual(z["process_heat_cascade"]["minimum_external_heating_kW"],0.)
        self.assertEqual(z["annual"]["heat_pump_delivered_kWh"],0.)
    def test_reject_nonphysical_operating_scenarios(self):
        s=site()
        with self.assertRaises(ValueError):replace(s,boiler_efficiency=1.2)
        with self.assertRaises(ValueError):replace(s,tariff_blocks=(TariffBlock("a",8000,.05),TariffBlock("b",1000,.05)))
        with self.assertRaises(ValueError):Source(60,70,10)
        with self.assertRaises(ValueError):TariffBlock("bad",800,.05,1.1)
        with self.assertRaises(ValueError):replace(s,hp_nameplate_kW=-2.)

if __name__=="__main__":unittest.main()
