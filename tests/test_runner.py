import unittest

from montecarlo.runner import CRFilterConfig, evaluate_consistency, run_ahp_for_hierarchy


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

    def test_run_ahp_forms_labeled_paths_when_aliases_provided(self):
        class FakeAnalyzer:
            def load_hierarchy(self, _: str):
                return {}

            def build_comparison_matrices(self, _: dict):
                return []

            def calculate_local_weights_by_path(self, _, id_to_label=None):
                return {
                    "": {
                        "items": [id_to_label["KA"], id_to_label["KS"]],
                        "weights": [0.6, 0.4],
                        "lam_max": 2.0,
                        "ci": 0.0,
                        "cr": 0.0,
                    },
                    f"{id_to_label['KA']} / Human": {
                        "items": ["Annotation errors"],
                        "weights": [1.0],
                        "lam_max": 1.0,
                        "ci": 0.0,
                        "cr": 0.0,
                    },
                }

            def propagate_global_weights(self, _):
                return {"Knowledge analysis / Human / Annotation errors": 0.7}

        payload = run_ahp_for_hierarchy(
            hierarchy_path="unused.yaml",
            analyzer=FakeAnalyzer(),
            id_to_label={"KA": "Knowledge analysis", "KS": "Knowledge selection"},
        )
        self.assertIn("Knowledge analysis / Human / Annotation errors", payload["global_weights"])
        self.assertEqual(
            payload["local_weights_by_path"][""]["items"],
            ["Knowledge analysis", "Knowledge selection"],
        )


if __name__ == "__main__":
    unittest.main()
