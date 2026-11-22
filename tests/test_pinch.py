"""Analytical limiting cases of the temperature-interval pinch cascade."""
import unittest
from site_screen.pinch import ProcessStream,heat_cascade as cascade

def H(name,ti,to,cp):return ProcessStream(name,"hot",ti,to,cp)
def C(name,ti,to,cp):return ProcessStream(name,"cold",ti,to,cp)

class PinchTests(unittest.TestCase):
    def test_no_hot_process_streams(self):
        a=cascade([C("steam",30,130,2)],10.)
        self.assertAlmostEqual(a["minimum_external_heating_kW"],200.)
        self.assertEqual(a["minimum_external_cooling_kW"],0.)
        self.assertAlmostEqual(a["heat_balance_residual_kW"],0.)
    def test_complete_internal_heat_recovery(self):
        a=cascade([H("hot",200,100,1),C("cold",50,150,1)],10.)
        self.assertAlmostEqual(a["minimum_external_heating_kW"],0.)
        self.assertAlmostEqual(a["minimum_external_cooling_kW"],0.)
        self.assertAlmostEqual(a["maximum_internal_process_heat_recovery_kW"],100.)
    def test_no_temperature_overlap(self):
        a=cascade([H("waste",100,60,1),C("industrial",120,160,1)],20.)
        self.assertAlmostEqual(a["minimum_external_heating_kW"],40.)
        self.assertAlmostEqual(a["minimum_external_cooling_kW"],40.)
        self.assertEqual(a["maximum_internal_process_heat_recovery_kW"],0.)
    def test_unmatched_energy_conserved(self):
        streams=[H("H1",230,85,3.),H("H2",155,50,1.8),
                 C("C1",25,180,2.),C("C2",90,215,1.2)]
        for dt in (5.,10.,20.,40.):
            a=cascade(streams,dt)
            self.assertAlmostEqual(a["heat_balance_residual_kW"],0.,places=8)
            self.assertGreaterEqual(a["minimum_external_heating_kW"],0.)
            self.assertGreaterEqual(a["minimum_external_cooling_kW"],0.)
            self.assertGreaterEqual(a["maximum_internal_process_heat_recovery_kW"],0.)
    def test_more_temperature_approach_cannot_reduce_hot_utility(self):
        streams=[H("H1",230,85,3.),H("H2",155,50,1.8),
                 C("C1",25,180,2.),C("C2",90,215,1.2)]
        a=[cascade(streams,dt) for dt in (5.,10.,20.,40.)]
        for x,y in zip(a,a[1:]):
            self.assertLessEqual(x["minimum_external_heating_kW"],
                                 y["minimum_external_heating_kW"]+1e-8)
    def test_cold_stream_not_omitted(self):
        with self.assertRaises(ValueError):cascade([H("H1",100,40,1)],10.)
    def test_duplicate_or_backwards_fail(self):
        with self.assertRaises(ValueError):cascade([C("x",20,70,1),C("X",30,80,1)],10.)
        with self.assertRaises(ValueError):H("hot",100,150,1)
        with self.assertRaises(ValueError):C("cold",100,90,1)
        with self.assertRaises(ValueError):cascade([C("cold",30,40,1)],0)
    def test_nonuniform_three_stream_case_independent_energy(self):
        a=cascade([H("dryer",130,60,4.),C("feed",20,110,2.),
                   C("cleaning",60,95,1.)],10.)
        self.assertAlmostEqual(a["total_process_hot_kW"],280.)
        self.assertAlmostEqual(a["total_process_cold_kW"],215.)
        self.assertAlmostEqual(a["maximum_internal_process_heat_recovery_kW"]+
          a["minimum_external_heating_kW"],215.)
        self.assertAlmostEqual(a["maximum_internal_process_heat_recovery_kW"]+
          a["minimum_external_cooling_kW"],280.)

if __name__=="__main__":unittest.main()
