import tempfile
import unittest
from pathlib import Path

from montecarlo.analysis import summarize_results
from montecarlo.profiles import ProfileDefinition


class TestAnalysis(unittest.TestCase):
    def test_summary_stats(self):
        raw_results = [
            {
                "profile_id": "P1",
                "profile_name": "A",
                "sample_index": 0,
                "accepted": True,
                "error": None,
                "global_weights": {"R1": 0.6, "R2": 0.4},
            },
            {
                "profile_id": "P1",
                "profile_name": "A",
                "sample_index": 1,
                "accepted": True,
                "error": None,
                "global_weights": {"R1": 0.5, "R2": 0.5},
            },
            {
                "profile_id": "P2",
                "profile_name": "B",
                "sample_index": 0,
                "accepted": True,
                "error": None,
                "global_weights": {"R1": 0.2, "R2": 0.8},
            },
        ]
        profiles = {
            "P1": ProfileDefinition("P1", "A", "KA>KS", {"Knowledge analysis": 1, "Knowledge selection": 0}, {}),
            "P2": ProfileDefinition("P2", "B", "OP>KS", {"Model operation": 1, "Knowledge selection": 0}, {}),
        }

        with tempfile.TemporaryDirectory() as tmp:
            payload = summarize_results(raw_results, profiles, out_dir=Path(tmp))
            self.assertIn("profiles", payload)
            self.assertIn("P1", payload["profiles"])
            self.assertEqual(payload["profiles"]["P1"]["accepted_runs"], 2)
            self.assertIn("cross_profile", payload)


if __name__ == "__main__":
    unittest.main()
