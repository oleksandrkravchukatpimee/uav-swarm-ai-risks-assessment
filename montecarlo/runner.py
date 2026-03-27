from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from montecarlo.generator import GeneratedSample

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CRFilterConfig:
    threshold: float = 0.1
    mode: str = "any"  # any | root_only


def _serialize_local_weights(local_weights_by_path: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    serialized: Dict[str, Dict[str, Any]] = {}
    for path, payload in local_weights_by_path.items():
        serialized[path] = {
            "items": list(payload["items"]),
            "weights": [float(x) for x in payload["weights"]],
            "lam_max": float(payload["lam_max"]),
            "ci": float(payload["ci"]),
            "cr": float(payload["cr"]),
        }
    return serialized


def _top_risks(global_weights: Dict[str, float], k: int) -> List[str]:
    ordered = sorted(global_weights.items(), key=lambda x: (-x[1], x[0]))
    return [name for name, _ in ordered[:k]]


def evaluate_consistency(local_weights_by_path: Dict[str, Dict[str, Any]], cfg: CRFilterConfig) -> Tuple[bool, List[str], float]:
    if cfg.mode not in {"any", "root_only"}:
        raise ValueError(f"Unsupported CR filter mode: {cfg.mode}")

    cr_by_path = {path: float(payload["cr"]) for path, payload in local_weights_by_path.items()}
    max_cr = max(cr_by_path.values()) if cr_by_path else 0.0

    if cfg.mode == "root_only":
        root_cr = cr_by_path.get("", 0.0)
        offending = [""] if root_cr >= cfg.threshold else []
        return not offending, offending, max_cr

    offending = [path for path, cr in cr_by_path.items() if cr >= cfg.threshold]
    return not offending, offending, max_cr


def run_ahp_for_hierarchy(hierarchy_path: str | Path, analyzer: Any | None = None) -> Dict[str, Any]:
    if analyzer is None:
        from ahp_analyzer import AHPAnalyzer

        ahp = AHPAnalyzer()
    else:
        ahp = analyzer
    hierarchy = ahp.load_hierarchy(str(hierarchy_path))
    flat_data = ahp.build_comparison_matrices(hierarchy)
    local_weights_by_path = ahp.calculate_local_weights_by_path(flat_data)
    global_weights = ahp.propagate_global_weights(local_weights_by_path)

    return {
        "hierarchy": hierarchy,
        "local_weights_by_path": local_weights_by_path,
        "global_weights": {k: float(v) for k, v in global_weights.items()},
    }


def run_generated_samples(
    samples: Iterable[GeneratedSample],
    out_dir: str | Path,
    cr_filter: CRFilterConfig,
    stop_on_error: bool = False,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    out_base = Path(out_dir)
    grouped_results: Dict[str, List[Dict[str, Any]]] = {}

    analyzer = None
    for sample in samples:
        if sample.profile_id not in grouped_results:
            grouped_results[sample.profile_id] = []

        result: Dict[str, Any] = {
            "profile_id": sample.profile_id,
            "profile_name": sample.profile_name,
            "sample_index": sample.sample_index,
            "sample_seed": sample.sample_seed,
            "hierarchy_path": str(sample.hierarchy_path),
            "metadata_path": str(sample.metadata_path),
            "accepted": False,
            "offending_paths": [],
            "max_cr": None,
            "error": None,
            "top3": [],
            "top5": [],
            "top10": [],
            "global_weights": {},
            "local_weights_by_path": {},
        }

        if dry_run:
            grouped_results[sample.profile_id].append(result)
            continue

        try:
            if analyzer is None:
                from ahp_analyzer import AHPAnalyzer

                analyzer = AHPAnalyzer()
            run_payload = run_ahp_for_hierarchy(sample.hierarchy_path, analyzer=analyzer)
            local_weights_by_path = run_payload["local_weights_by_path"]
            global_weights = run_payload["global_weights"]
            accepted, offending_paths, max_cr = evaluate_consistency(local_weights_by_path, cfg=cr_filter)

            result["accepted"] = accepted
            result["offending_paths"] = offending_paths
            result["max_cr"] = max_cr
            result["global_weights"] = global_weights
            result["local_weights_by_path"] = _serialize_local_weights(local_weights_by_path)
            result["top3"] = _top_risks(global_weights, 3)
            result["top5"] = _top_risks(global_weights, 5)
            result["top10"] = _top_risks(global_weights, 10)
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"{type(exc).__name__}: {exc}"
            LOGGER.exception("Run failed for %s", sample.hierarchy_path)
            if stop_on_error:
                raise

        grouped_results[sample.profile_id].append(result)

    flat_results: List[Dict[str, Any]] = []
    for profile_id, profile_results in grouped_results.items():
        profile_dir = out_base / profile_id / "runs"
        profile_dir.mkdir(parents=True, exist_ok=True)

        json_path = profile_dir / "raw_results.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(profile_results, f, ensure_ascii=False, indent=2)

        csv_path = profile_dir / "raw_results.csv"
        rows: List[Dict[str, Any]] = []
        for row in profile_results:
            rows.append({
                "profile_id": row["profile_id"],
                "sample_index": row["sample_index"],
                "sample_seed": row["sample_seed"],
                "accepted": row["accepted"],
                "max_cr": row["max_cr"],
                "offending_paths": "|".join(row["offending_paths"]),
                "error": row["error"],
                "top3": "|".join(row["top3"]),
                "top5": "|".join(row["top5"]),
                "top10": "|".join(row["top10"]),
            })

        with csv_path.open("w", encoding="utf-8", newline="") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            else:
                writer = csv.writer(f)
                writer.writerow(["profile_id", "sample_index", "sample_seed", "accepted", "max_cr", "offending_paths", "error", "top3", "top5", "top10"])

        flat_results.extend(profile_results)

    return flat_results
