import tempfile
import unittest
from pathlib import Path

from montecarlo.profiles import (
    build_hierarchy_index,
    load_config,
    load_profiles,
    parse_relation_expression,
    stage_pairwise_deltas,
)


class TestProfilesAndConfig(unittest.TestCase):
    def setUp(self):
        self.config_yaml = """
version: 1
aliases:
  stages:
    KS: Knowledge selection
    KA: Knowledge analysis
    TR: AGPM Training
    OP: Model operation
  factors:
    H: Human
    T: Technological
  risks:
    representativeness: Data representativeness
    confabulations: Confabulations
scale:
  relations:
    "=": 0
    ">": 2
    ">>": 4
  priorities:
    low: 1
    medium: 2
    high: 3
    very_high: 4
"""
        self.hierarchy = {
            "Knowledge selection": {
                "factors": {
                    "Human": {"risks": {"Data representativeness": {}}},
                    "Technological": {"risks": {}},
                }
            },
            "Knowledge analysis": {
                "factors": {
                    "Human": {"risks": {}},
                    "Technological": {"risks": {"Confabulations": {}}},
                }
            },
            "AGPM Training": {"factors": {"Human": {"risks": {}}, "Technological": {"risks": {}}}},
            "Model operation": {"factors": {"Human": {"risks": {}}, "Technological": {"risks": {}}}},
        }
        self.valid_profiles = """
version: 1
P1:
  name: AI/ML-heavy
  description: desc
  stages: KA = TR > OP > KS
  factors:
    KS: H > T
    KA: T > H
    TR: T > H
    OP: T > H
  risks:
    KS:
      H:
        representativeness: high
    KA:
      T:
        confabulations: very_high
"""

    def _write(self, tmp: str, name: str, payload: str) -> Path:
        path = Path(tmp) / name
        path.write_text(payload, encoding="utf-8")
        return path

    def test_parse_relation_expression_with_config_scale(self):
        scores = parse_relation_expression(
            "KA = TR > OP > KS",
            valid_ids={"KA": "Knowledge analysis", "TR": "AGPM Training", "OP": "Model operation", "KS": "Knowledge selection"},
            relation_scale={"=": 0, ">": 2, ">>": 4},
        )
        self.assertEqual(scores["Knowledge analysis"], 0)
        self.assertEqual(scores["AGPM Training"], 0)
        self.assertEqual(scores["Model operation"], -2)
        self.assertEqual(scores["Knowledge selection"], -4)

    def test_stage_pairwise_deltas(self):
        deltas = stage_pairwise_deltas({"A": 0, "B": -2, "C": -4})
        self.assertEqual(deltas[("A", "B")], -2)
        self.assertEqual(deltas[("C", "A")], 4)

    def test_load_config_and_profiles(self):
        try:
            import yaml  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("PyYAML is not installed")

        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._write(tmp, "config.yaml", self.config_yaml)
            profiles_path = self._write(tmp, "profiles.yaml", self.valid_profiles)
            cfg = load_config(config_path)
            index = build_hierarchy_index(self.hierarchy, cfg)
            profiles = load_profiles(profiles_path, config=cfg, hierarchy_index=index)
            self.assertIn("P1", profiles)
            self.assertIn("Knowledge analysis", profiles["P1"].stage_scores)
            self.assertEqual(
                profiles["P1"].factor_scores_by_stage["Knowledge selection"]["Human"],
                0,
            )
            self.assertIn("Knowledge analysis / Technological", profiles["P1"].risk_scores_by_path)
            self.assertEqual(profiles["P1"].risk_scores_by_path["Knowledge analysis / Technological"]["Confabulations"], 4)

    def test_invalid_config_unknown_stage_id(self):
        try:
            import yaml  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("PyYAML is not installed")

        bad_config = self.config_yaml.replace("KS: Knowledge selection", "XX: Knowledge selection")
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._write(tmp, "config.yaml", bad_config)
            with self.assertRaises(ValueError):
                load_config(config_path)

    def test_invalid_yaml_structure(self):
        try:
            import yaml  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("PyYAML is not installed")

        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._write(tmp, "config.yaml", self.config_yaml)
            profiles_path = self._write(tmp, "profiles.yaml", "version: 1\nP1: [bad]")
            cfg = load_config(config_path)
            index = build_hierarchy_index(self.hierarchy, cfg)
            with self.assertRaises(ValueError):
                load_profiles(profiles_path, config=cfg, hierarchy_index=index)

    def test_unknown_stage_factor_risk_validation(self):
        try:
            import yaml  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("PyYAML is not installed")

        bad_profiles = """
version: 1
P1:
  name: Bad
  stages: KA = TR > OP > XX
"""
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._write(tmp, "config.yaml", self.config_yaml)
            profiles_path = self._write(tmp, "profiles.yaml", bad_profiles)
            cfg = load_config(config_path)
            index = build_hierarchy_index(self.hierarchy, cfg)
            with self.assertRaises(ValueError):
                load_profiles(profiles_path, config=cfg, hierarchy_index=index)

        bad_factor = """
version: 1
P1:
  name: BadFactor
  stages: KA = TR > OP > KS
  factors:
    KS: H > X
"""
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._write(tmp, "config.yaml", self.config_yaml)
            profiles_path = self._write(tmp, "profiles.yaml", bad_factor)
            cfg = load_config(config_path)
            index = build_hierarchy_index(self.hierarchy, cfg)
            with self.assertRaises(ValueError):
                load_profiles(profiles_path, config=cfg, hierarchy_index=index)

        bad_risk = """
version: 1
P1:
  name: BadRisk
  stages: KA = TR > OP > KS
  factors:
    KS: H > T
    KA: T > H
    TR: T > H
    OP: T > H
  risks:
    KS:
      H:
        unknown_risk_id: high
"""
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._write(tmp, "config.yaml", self.config_yaml)
            profiles_path = self._write(tmp, "profiles.yaml", bad_risk)
            cfg = load_config(config_path)
            index = build_hierarchy_index(self.hierarchy, cfg)
            with self.assertRaises(ValueError):
                load_profiles(profiles_path, config=cfg, hierarchy_index=index)

    def test_risk_placement_validation(self):
        try:
            import yaml  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("PyYAML is not installed")

        misplaced = """
version: 1
P1:
  name: Misplaced
  stages: KA = TR > OP > KS
  factors:
    KS: H > T
    KA: T > H
    TR: T > H
    OP: T > H
  risks:
    KS:
      H:
        confabulations: high
"""
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._write(tmp, "config.yaml", self.config_yaml)
            profiles_path = self._write(tmp, "profiles.yaml", misplaced)
            cfg = load_config(config_path)
            index = build_hierarchy_index(self.hierarchy, cfg)
            with self.assertRaises(ValueError):
                load_profiles(profiles_path, config=cfg, hierarchy_index=index)


if __name__ == "__main__":
    unittest.main()
