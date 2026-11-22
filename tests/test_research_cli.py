import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from site_screen.research_cli import read_study,main
ROOT=Path(__file__).resolve().parents[1]
SAMPLE=ROOT/"data"/"synthetic_process_sites.json"

class ResearchCLI(unittest.TestCase):
    def test_example_data_and_determinism(self):
        sites,sens=read_study(SAMPLE)
        self.assertEqual(len(sites),3)
        self.assertEqual(len(sens.hp_nameplates_kW),3)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"study.json"
            self.assertEqual(main(["--input",str(SAMPLE),"--output",str(p),"--scenarios"]),0)
            raw=p.read_bytes()
            self.assertEqual(main(["--input",str(SAMPLE),"--output",str(p),"--scenarios"]),0)
            self.assertEqual(p.read_bytes(),raw)
            report=json.loads(raw)
            self.assertEqual(report["site_count"],3)
            self.assertEqual(sum(x["total_cases"] for x in report["scenario_matrix"]),162)
            self.assertTrue(all(x["source_heat_balance_verified"] for x in report["cases"]))
            self.assertTrue(all(x["process_heat_balance_verified"] for x in report["cases"]))
            self.assertTrue(all(not x["compressor_qualified"] for x in report["cases"]))
            self.assertTrue(all(not x["industrial_validation"] for x in report["cases"]))
            for x in report["cases"]:
                z=x["annual"]
                self.assertAlmostEqual(z["heat_pump_delivered_kWh"],
                  z["external_source_heat_kWh"]+z["heat_pump_compressor_kWh"])
                self.assertAlmostEqual(z["baseline_heating_utility_kWh"],
                  z["residual_heating_utility_kWh"]+z["heat_pump_delivered_kWh"])
    def _reject(self,fn):
        d=json.loads(SAMPLE.read_text())
        fn(d)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"study.json";p.write_text(json.dumps(d))
            with self.assertRaises((ValueError,TypeError,KeyError)):read_study(p)
    def test_unknown_fields(self):self._reject(lambda d:d["sites"][0].update(nonsense=5))
    def test_non_synthetic_provenance(self):self._reject(lambda d:d.update(data_provenance="unverified measurement"))
    def test_duplicate_site(self):self._reject(lambda d:d["sites"][1].update(site_id=d["sites"][0]["site_id"]))
    def test_unphysical_temperature(self):self._reject(lambda d:d["sites"][0]["streams"][0].update(supply_C=-400))
    def test_illegal_tariff_hours(self):self._reject(lambda d:d["sites"][0]["tariff_blocks"][0].update(hours=9000))
    def test_inconsistent_source(self):self._reject(lambda d:d["sites"][0]["independent_source"].update(return_C=120))
    def test_invalid_scenario_dimension(self):self._reject(lambda d:d["sensitivity"].update(carnot_fractions=[.35,1.3]))
    def test_no_hot_stream_not_error(self):
        d=json.loads(SAMPLE.read_text())
        d["sites"][0]["streams"]=[x for x in d["sites"][0]["streams"] if x["kind"]=="cold"]
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"s.json";p.write_text(json.dumps(d))
            sites,_=read_study(p)
            self.assertEqual(len(sites[0].streams),2)

if __name__=="__main__":unittest.main()
