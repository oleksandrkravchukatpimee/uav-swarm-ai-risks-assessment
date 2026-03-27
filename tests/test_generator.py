import unittest

from montecarlo.biases import ProfileBiasConfig
from montecarlo.generator import VariabilityConfig, clamp_scale_value, generate_profile_hierarchy
from montecarlo.profiles import ProfileDefinition, parse_relation_expression


class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.base_hierarchy = {
            "KS": {"factors": {"H": {"risks": {}}, "T": {"risks": {}}}},
            "KA": {
                "compare": {"KS": -2},
                "factors": {
                    "H": {"compare": {"T": -5}, "risks": {}},
                    "T": {
                        "compare": {"H": 5},
                        "risks": {
                            "confabulations": {"compare": {"overfitting": -4}},
                            "overfitting": {"compare": {"confabulations": 4}},
                        },
                    },
                },
            },
            "TR": {"compare": {"KS": -3, "KA": -2}, "factors": {"H": {"risks": {}}, "T": {"risks": {}}}},
            "OP": {"compare": {"KS": -3, "KA": -3, "TR": -4}, "factors": {"H": {"risks": {}}, "T": {"risks": {}}}},
        }
        self.base_hierarchy["TR"]["factors"]["H"]["risks"]["domain_shift"] = None
        self.neutral_profile = ProfileDefinition(
            profile_id="P1",
            name="Test",
            expression="KS = KA = TR = OP",
            stage_scores={"KS": 0, "KA": 0, "TR": 0, "OP": 0},
            stage_pairwise_deltas={},
        )

    def test_clamp_scale(self):
        self.assertEqual(clamp_scale_value(15), 9)
        self.assertEqual(clamp_scale_value(-14), -9)
        self.assertEqual(clamp_scale_value(0), 0)
        self.assertEqual(clamp_scale_value(-0), 0)

    def test_reproducible_generation(self):
        bias = ProfileBiasConfig()
        variability = VariabilityConfig(stage_sigma=0.5, factor_sigma=0.5, risk_sigma=0.5)
        h1, m1 = generate_profile_hierarchy(self.base_hierarchy, self.neutral_profile, bias, variability, sample_seed=123)
        h2, m2 = generate_profile_hierarchy(self.base_hierarchy, self.neutral_profile, bias, variability, sample_seed=123)
        self.assertEqual(h1, h2)
        self.assertEqual(m1, m2)

    def test_none_risk_nodes_are_normalized_to_empty_mappings(self):
        bias = ProfileBiasConfig()
        variability = VariabilityConfig(stage_sigma=0.0, factor_sigma=0.0, risk_sigma=0.0)
        hierarchy, _ = generate_profile_hierarchy(self.base_hierarchy, self.neutral_profile, bias, variability, sample_seed=123)
        self.assertEqual(hierarchy["TR"]["factors"]["H"]["risks"]["domain_shift"], {})

    def test_stage_profile_regression_expected_fragment(self):
        stage_scores = parse_relation_expression(
            expression="KA = TR > OP > KS",
            valid_ids={"KS": "Knowledge selection", "KA": "Knowledge analysis", "TR": "AGPM Training", "OP": "Model operation"},
            relation_scale={"=": 0, ">": 2, ">>": 4},
        )
        profile = ProfileDefinition(
            profile_id="P1",
            name="StageSign",
            expression="KA = TR > OP > KS",
            stage_scores=stage_scores,
            stage_pairwise_deltas={},
        )
        bias = ProfileBiasConfig()
        variability = VariabilityConfig(stage_sigma=1.0, factor_sigma=0.0, risk_sigma=0.0)
        hierarchy, perturbations = generate_profile_hierarchy(self.base_hierarchy, profile, bias, variability, sample_seed=3487)

        self.assertEqual(hierarchy["KA"]["compare"]["KS"], -8)
        self.assertEqual(hierarchy["TR"]["compare"]["KS"], -6)
        self.assertEqual(hierarchy["TR"]["compare"]["KA"], -1)
        self.assertEqual(hierarchy["OP"]["compare"]["KS"], -5)
        self.assertEqual(hierarchy["OP"]["compare"]["KA"], 4)
        self.assertEqual(hierarchy["OP"]["compare"]["TR"], 2)

        stage_perturb = next(p for p in perturbations if p["scope"] == "stage")
        self.assertIn("parsed_profile_order", stage_perturb)
        self.assertIn("relative_ranks", stage_perturb)
        self.assertIn("pre_montecarlo_value", stage_perturb)
        self.assertIn("new_value", stage_perturb)

    def test_factor_profile_sign_and_magnitude_without_noise(self):
        bias = ProfileBiasConfig(factor_scores_by_stage={"KA": {"T": 0, "H": -2}})
        variability = VariabilityConfig(stage_sigma=0.0, factor_sigma=0.0, risk_sigma=0.0)
        hierarchy, _ = generate_profile_hierarchy(self.base_hierarchy, self.neutral_profile, bias, variability, sample_seed=1)

        self.assertEqual(hierarchy["KA"]["factors"]["H"]["compare"]["T"], 8)  # T preferred over H
        self.assertEqual(hierarchy["KA"]["factors"]["T"]["compare"]["H"], -8)  # T preferred over H

    def test_risk_profile_sign_and_magnitude_without_noise(self):
        bias = ProfileBiasConfig(risk_scores_by_path={"KA / T": {"confabulations": 4, "overfitting": 2}})
        variability = VariabilityConfig(stage_sigma=0.0, factor_sigma=0.0, risk_sigma=0.0)
        hierarchy, _ = generate_profile_hierarchy(self.base_hierarchy, self.neutral_profile, bias, variability, sample_seed=1)

        self.assertEqual(hierarchy["KA"]["factors"]["T"]["risks"]["overfitting"]["compare"]["confabulations"], 8)
        self.assertEqual(hierarchy["KA"]["factors"]["T"]["risks"]["confabulations"]["compare"]["overfitting"], -8)

    def test_stage_bias_applied_without_noise(self):
        profile = ProfileDefinition(
            profile_id="P1",
            name="Test",
            expression="KA > KS",
            stage_scores={"KA": 2, "KS": 0},
            stage_pairwise_deltas={},
        )
        bias = ProfileBiasConfig()
        variability = VariabilityConfig(stage_sigma=0.0, factor_sigma=0.0, risk_sigma=0.0)
        hierarchy, _ = generate_profile_hierarchy(self.base_hierarchy, profile, bias, variability, sample_seed=1)
        self.assertEqual(hierarchy["KA"]["compare"]["KS"], -8)


if __name__ == "__main__":
    unittest.main()
