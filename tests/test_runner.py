import unittest

from montecarlo.runner import CRFilterConfig, evaluate_consistency


class TestRunner(unittest.TestCase):
    def setUp(self):
        self.local_weights = {
            "": {"cr": 0.05},
            "A": {"cr": 0.11},
            "B": {"cr": 0.04},
        }

    def test_any_mode_filters_if_any_cr_high(self):
        accepted, offending, max_cr = evaluate_consistency(self.local_weights, CRFilterConfig(threshold=0.1, mode="any"))
        self.assertFalse(accepted)
        self.assertIn("A", offending)
        self.assertAlmostEqual(max_cr, 0.11)

    def test_root_only_mode(self):
        accepted, offending, max_cr = evaluate_consistency(self.local_weights, CRFilterConfig(threshold=0.1, mode="root_only"))
        self.assertTrue(accepted)
        self.assertEqual(offending, [])
        self.assertAlmostEqual(max_cr, 0.11)


if __name__ == "__main__":
    unittest.main()
