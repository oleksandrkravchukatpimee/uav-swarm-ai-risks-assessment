import unittest

from montecarlo.biases import ProfileBiasConfig
from montecarlo.generator import VariabilityConfig, clamp_scale_value, generate_profile_hierarchy
from montecarlo.profiles import ProfileDefinition


class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.base_hierarchy = {
            "Knowledge selection": {"factors": {"Human": {"risks": {"A": {}, "B": {"compare": {"A": 1}}}}}},
            "Knowledge analysis": {
                "compare": {"Knowledge selection": -2},
                "factors": {"Human": {"risks": {"A2": {}, "B2": {"compare": {"A2": 1}}}}},
            },
        }
        self.profile = ProfileDefinition(
            profile_id="P1",
            name="Test",
            expression="KA > KS",
            stage_scores={"Knowledge analysis": 2, "Knowledge selection": 0},
            stage_pairwise_deltas={
                ("Knowledge selection", "Knowledge analysis"): 2,
                ("Knowledge analysis", "Knowledge selection"): -2,
            },
        )

    def test_clamp_scale(self):
        self.assertEqual(clamp_scale_value(15), 9)
        self.assertEqual(clamp_scale_value(-14), -9)
        self.assertEqual(clamp_scale_value(0), 1)
        self.assertEqual(clamp_scale_value(-0), 1)

    def test_reproducible_generation(self):
        bias = ProfileBiasConfig()
        variability = VariabilityConfig(stage_sigma=0.5, factor_sigma=0.5, risk_sigma=0.5)
        h1, m1 = generate_profile_hierarchy(self.base_hierarchy, self.profile, bias, variability, sample_seed=123)
        h2, m2 = generate_profile_hierarchy(self.base_hierarchy, self.profile, bias, variability, sample_seed=123)
        self.assertEqual(h1, h2)
        self.assertEqual(m1, m2)

    def test_stage_bias_applied_without_noise(self):
        bias = ProfileBiasConfig()
        variability = VariabilityConfig(stage_sigma=0.0, factor_sigma=0.0, risk_sigma=0.0)
        hierarchy, _ = generate_profile_hierarchy(self.base_hierarchy, self.profile, bias, variability, sample_seed=1)
        # Current node: KA, target KS, old=-2, deterministic delta = score(KS)-score(KA) = -2
        self.assertEqual(hierarchy["Knowledge analysis"]["compare"]["Knowledge selection"], -4)


if __name__ == "__main__":
    unittest.main()
