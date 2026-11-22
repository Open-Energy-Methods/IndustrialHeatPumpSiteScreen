"""No positive industrial feasibility claims can enter the rendered study."""
import json,unittest
from site_screen.report import render

class Report(unittest.TestCase):
    def _report(self):
        return dict(schema_version="1.0",data_provenance="synthetic",
            cases=[dict(site_id="Site_X",
                process_heat_cascade=dict(minimum_external_heating_kW=500.,
                  maximum_internal_process_heat_recovery_kW=210.),
                fraction_external_heating_electrified=.4,
                annual_net_savings_eur=-10000.,
                break_even_incremental_installed_capex_eur=0.)])
    def test_negative_economics_retained(self):
        t=render(self._report())
        self.assertIn("-10,000",t)
        self.assertIn("0 |",t)
        self.assertIn("no measured industrial or compressor validation",t)
        self.assertIn("not an equipment cost estimate",t)
    def test_bad_provenance_refused(self):
        x=self._report();x["data_provenance"]="actual"
        with self.assertRaises(ValueError):render(x)
    def test_empty_report_rejected(self):
        x=self._report();x["cases"]=[]
        with self.assertRaises(ValueError):render(x)

if __name__=="__main__":unittest.main()
