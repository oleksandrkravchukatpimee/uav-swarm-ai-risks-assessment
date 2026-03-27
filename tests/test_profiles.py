import tempfile
import unittest
from pathlib import Path

from montecarlo.profiles import (
    RelationStrength,
    load_profiles,
    parse_stage_expression,
    stage_pairwise_deltas,
)


class TestProfiles(unittest.TestCase):
    def test_parse_expression(self):
        scores = parse_stage_expression("KA = TR > OP > KS")
        self.assertEqual(scores["Knowledge analysis"], 0)
        self.assertEqual(scores["AGPM Training"], 0)
        self.assertEqual(scores["Model operation"], -2)
        self.assertEqual(scores["Knowledge selection"], -4)

    def test_pairwise_deltas(self):
        scores = parse_stage_expression("OP >> TR > KA > KS", relation_strength=RelationStrength(greater=2, much_greater=4))
        deltas = stage_pairwise_deltas(scores)
        self.assertEqual(deltas[("Knowledge selection", "Model operation")], 8)
        self.assertEqual(deltas[("Model operation", "Knowledge selection")], -8)

    def test_invalid_expression(self):
        with self.assertRaises(ValueError):
            parse_stage_expression("KA >>> TR")

    def test_load_profiles(self):
        try:
            import yaml  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("PyYAML is not installed")

        payload = """
P1:
  name: AI/ML-heavy
  profile: KA = TR > OP > KS
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profiles.yaml"
            path.write_text(payload, encoding="utf-8")
            profiles = load_profiles(path)
            self.assertIn("P1", profiles)
            self.assertEqual(profiles["P1"].name, "AI/ML-heavy")


if __name__ == "__main__":
    unittest.main()
