import unittest
import numpy as np
from orbit import demo_positions, multi_orbital_figure, parse_multiple_tles
from topology import topology_figure

class TestOrbitalTwin(unittest.TestCase):
    def test_demo_trajectories(self):
        a = demo_positions()
        b = demo_positions(altitude_km=800, inclination=97.4)
        self.assertEqual(a.shape, (3, 180))
        self.assertFalse(np.array_equal(a,b))
    def test_multiorbit_figure(self):
        f = multi_orbital_figure([(demo_positions(),'Demo 1'),(demo_positions(altitude_km=800),'Demo 2')])
        self.assertEqual(len(f.data),5)
        self.assertEqual(f.data[0].surfacecolor.shape, (181,361))
    def test_tle_groups(self):
        a='ISS\n1 25544U abc\n2 25544 abc\nHUBBLE\n1 20580U abc\n2 20580 abc'
        self.assertEqual(len(parse_multiple_tles(a)),2)
    def test_topology_figure(self):
        self.assertGreater(len(topology_figure().data),5)

if __name__=='__main__': unittest.main()
