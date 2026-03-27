from __future__ import annotations

import csv
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

from montecarlo.analysis import summarize_results
from montecarlo.biases import DEFAULT_PROFILE_BIASES, ProfileBiasConfig, get_profile_bias_config
from montecarlo.generator import GeneratedSample, VariabilityConfig, generate_samples_for_profile
from montecarlo.profiles import (
    DEFAULT_STAGE_ALIASES,
    ProfileDefinition,
    RelationStrength,
    load_profiles,
)
from montecarlo.runner import CRFilterConfig, run_generated_samples

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class MonteCarloConfig:
    base_yaml: str
    profiles_yaml: str
    samples_per_profile: int
    out_dir: str
    seed: int = 42
    variability_strength: float = 1.0
    profile_ids: Sequence[str] | None = None
    cr_threshold: float = 0.1
    cr_mode: str = "any"
    dry_run: bool = False
    stop_on_error: bool = False
    stage_step: int = 2
    stage_strong_step: int = 4


def _ensure_profile_subset(
    profiles: Mapping[str, ProfileDefinition],
    profile_ids: Sequence[str] | None,
) -> Dict[str, ProfileDefinition]:
    if not profile_ids:
        return dict(profiles)

    selected: Dict[str, ProfileDefinition] = {}
    for profile_id in profile_ids:
        if profile_id not in profiles:
            known = ", ".join(sorted(profiles))
            raise ValueError(f"Unknown profile id '{profile_id}'. Known ids: {known}")
        selected[profile_id] = profiles[profile_id]
    return selected


def _load_base_hierarchy(path: str | Path) -> Dict:
    import yaml

    with Path(path).open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    if not isinstance(payload, dict):
        raise ValueError("Base hierarchy YAML must contain a top-level mapping")
    return payload


def _write_settings(out_dir: Path, cfg: MonteCarloConfig, profiles: Mapping[str, ProfileDefinition]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "config": asdict(cfg),
        "profiles": {
            profile_id: {
                "name": profile.name,
                "expression": profile.expression,
                "stage_scores": profile.stage_scores,
            }
            for profile_id, profile in profiles.items()
        },
        "stage_aliases": DEFAULT_STAGE_ALIASES,
        "relation_mapping": {
            "=": 0,
            ">": cfg.stage_step,
            ">>": cfg.stage_strong_step,
        },
    }
    with (out_dir / "settings.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _write_all_runs(out_dir: Path, results: List[Dict]) -> None:
    summary_dir = out_dir / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)

    with (summary_dir / "all_runs.json").open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    rows = []
    for row in results:
        rows.append({
            "profile_id": row.get("profile_id"),
            "sample_index": row.get("sample_index"),
            "sample_seed": row.get("sample_seed"),
            "accepted": row.get("accepted"),
            "max_cr": row.get("max_cr"),
            "error": row.get("error"),
            "offending_paths": "|".join(row.get("offending_paths", [])),
        })

    with (summary_dir / "all_runs.csv").open("w", encoding="utf-8", newline="") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        else:
            writer = csv.writer(f)
            writer.writerow(["profile_id", "sample_index", "sample_seed", "accepted", "max_cr", "error", "offending_paths"])


def run_montecarlo(cfg: MonteCarloConfig) -> Dict:
    relation_strength = RelationStrength(equal=0, greater=cfg.stage_step, much_greater=cfg.stage_strong_step)
    loaded_profiles = load_profiles(cfg.profiles_yaml, relation_strength=relation_strength)
    profiles = _ensure_profile_subset(loaded_profiles, cfg.profile_ids)

    out_dir = Path(cfg.out_dir)
    _write_settings(out_dir, cfg, profiles)

    if cfg.dry_run:
        return {
            "mode": "dry_run",
            "profiles": list(profiles.keys()),
            "samples_per_profile": cfg.samples_per_profile,
            "out_dir": str(out_dir),
        }

    base_hierarchy = _load_base_hierarchy(cfg.base_yaml)
    variability = VariabilityConfig(
        stage_sigma=cfg.variability_strength,
        factor_sigma=cfg.variability_strength,
        risk_sigma=cfg.variability_strength,
    )
    generated_samples: List[GeneratedSample] = []

    for profile_id, profile in profiles.items():
        bias_cfg: ProfileBiasConfig = get_profile_bias_config(profile_id, overrides=DEFAULT_PROFILE_BIASES)
        samples = generate_samples_for_profile(
            base_hierarchy=base_hierarchy,
            profile=profile,
            bias_cfg=bias_cfg,
            variability=variability,
            samples=cfg.samples_per_profile,
            seed=cfg.seed,
            out_dir=out_dir,
        )
        generated_samples.extend(samples)

    run_results = run_generated_samples(
        samples=generated_samples,
        out_dir=out_dir,
        cr_filter=CRFilterConfig(threshold=cfg.cr_threshold, mode=cfg.cr_mode),
        stop_on_error=cfg.stop_on_error,
        dry_run=False,
    )
    _write_all_runs(out_dir, run_results)

    summary = summarize_results(run_results, profiles=profiles, out_dir=out_dir)
    return {
        "mode": "completed",
        "profiles": list(profiles.keys()),
        "generated_samples": len(generated_samples),
        "results_count": len(run_results),
        "summary_path": str(Path(cfg.out_dir) / "summary" / "summary.json"),
        "report_path": str(Path(cfg.out_dir) / "summary" / "report.md"),
        "summary": summary,
    }
