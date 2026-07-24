import tempfile
import unittest
from math import isnan
from pathlib import Path

from montecarlo.analysis import _build_top_k_membership_matrix, summarize_results
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
            summary_dir = Path(tmp) / "summary"
            self.assertGreater((summary_dir / "top5_frequency_heatmap.png").stat().st_size, 0)
            self.assertGreater((summary_dir / "top10_frequency_heatmap.png").stat().st_size, 0)
            self.assertGreater((summary_dir / "top5_membership_heatmap.png").stat().st_size, 0)

    def test_top_k_membership_matrix_masks_non_members(self):
        risks, matrix = _build_top_k_membership_matrix(
            profile_mean_weights={
                "P1": {"R1": 0.7, "R2": 0.3},
                "P2": {"R1": 0.69, "R2": 0.8},
            },
            profiles=["P1", "P2"],
            top_k=1,
        )

        self.assertEqual(risks, ["R1", "R2"])
        self.assertEqual(matrix[0][0], 0.7)
        self.assertTrue(isnan(matrix[0][1]))
        self.assertTrue(isnan(matrix[1][0]))
        self.assertEqual(matrix[1][1], 0.8)


if __name__ == "__main__":
    unittest.main()
