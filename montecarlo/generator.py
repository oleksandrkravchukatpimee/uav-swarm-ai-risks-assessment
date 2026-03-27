from __future__ import annotations

import copy
import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from montecarlo.biases import ProfileBiasConfig
from montecarlo.profiles import ProfileDefinition, build_signed_pairwise_values

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VariabilityConfig:
    stage_sigma: float = 0.75
    factor_sigma: float = 0.75
    risk_sigma: float = 1.0


@dataclass(frozen=True)
class GeneratedSample:
    profile_id: str
    profile_name: str
    sample_index: int
    sample_seed: int
    hierarchy_path: Path
    metadata_path: Path


def clamp_scale_value(value: int) -> int:
    return max(-9, min(9, int(value)))


def _to_scale_int(value: Any) -> int:
    if isinstance(value, str) and "/" in value:
        numerator, denominator = value.split("/", maxsplit=1)
        raw = float(numerator) / float(denominator)
    else:
        raw = float(value)

    rounded = int(round(raw))
    return clamp_scale_value(rounded)


def _iter_compare_entries(compare_obj: Any) -> Iterable[Tuple[str, Any, Tuple[str, Any]]]:
    if isinstance(compare_obj, dict):
        for target, value in compare_obj.items():
            yield str(target), value, ("dict", str(target))
        return

    if isinstance(compare_obj, list):
        for idx, entry in enumerate(compare_obj):
            if isinstance(entry, (list, tuple)) and len(entry) == 2:
                yield str(entry[0]), entry[1], ("list_pair", idx)
                continue
            if isinstance(entry, dict) and "target" in entry and "value" in entry:
                yield str(entry["target"]), entry["value"], ("list_target_value", idx)
                continue
            if isinstance(entry, dict) and len(entry) == 1:
                key = next(iter(entry.keys()))
                yield str(key), entry[key], ("list_single_map", idx, str(key))
                continue
            raise TypeError(f"Unsupported compare entry format: {entry!r}")
        return

    raise TypeError(f"Unsupported compare type: {type(compare_obj).__name__}")


def _set_compare_value(compare_obj: Any, token: Tuple[str, Any], value: int) -> None:
    kind = token[0]
    if kind == "dict":
        compare_obj[token[1]] = value
        return
    if kind == "list_pair":
        idx = token[1]
        compare_obj[idx][1] = value
        return
    if kind == "list_target_value":
        idx = token[1]
        compare_obj[idx]["value"] = value
        return
    if kind == "list_single_map":
        idx = token[1]
        key = token[2]
        compare_obj[idx][key] = value
        return
    raise TypeError(f"Unsupported compare token: {token!r}")


def _iter_comparison_groups(hierarchy: Dict[str, Any]) -> Iterable[Tuple[str, List[str], Dict[str, Any]]]:
    yield "stage", [], hierarchy

    for stage_name, stage_node in hierarchy.items():
        if not isinstance(stage_node, dict):
            continue
        factors = stage_node.get("factors")
        if not isinstance(factors, dict):
            continue

        yield "factor", [stage_name], factors
        for factor_name, factor_node in factors.items():
            if not isinstance(factor_node, dict):
                continue
            risks = factor_node.get("risks")
            if isinstance(risks, dict):
                yield "risk", [stage_name, factor_name], risks


def _normalize_empty_risk_nodes(hierarchy: Dict[str, Any]) -> None:
    """
    YAML bare keys under risks are parsed as None. Normalize them to empty mappings
    so generated files keep explicit '{}' instead of 'null'.
    """
    for stage_node in hierarchy.values():
        if not isinstance(stage_node, dict):
            continue
        factors = stage_node.get("factors")
        if not isinstance(factors, dict):
            continue
        for factor_node in factors.values():
            if not isinstance(factor_node, dict):
                continue
            risks = factor_node.get("risks")
            if not isinstance(risks, dict):
                continue
            for risk_id, risk_node in list(risks.items()):
                if risk_node is None:
                    risks[risk_id] = {}


def _profile_seed_offset(profile_id: str) -> int:
    return sum((idx + 1) * ord(ch) for idx, ch in enumerate(profile_id))


def _sigma_for_scope(scope: str, variability: VariabilityConfig) -> float:
    if scope == "stage":
        return variability.stage_sigma
    if scope == "factor":
        return variability.factor_sigma
    return variability.risk_sigma


def _has_explicit_profile_rule(scope: str, group_path: List[str], profile: ProfileDefinition) -> bool:
    if scope == "stage":
        return True
    if scope == "factor":
        return group_path[0] in profile.factor_scores_by_stage
    path_key = " / ".join(group_path)
    return path_key in profile.risk_scores_by_path


def _score_map_for_group(
    scope: str,
    group_path: List[str],
    group_names: List[str],
    profile: ProfileDefinition,
    bias_cfg: ProfileBiasConfig,
) -> Dict[str, int]:
    if scope == "stage":
        return {name: int(profile.stage_scores.get(name, 0)) for name in group_names}

    if scope == "factor":
        stage_name = group_path[0]
        stage_bias = bias_cfg.factor_scores_by_stage.get(stage_name, {})
        return {name: int(stage_bias.get(name, 0)) for name in group_names}

    path_key = " / ".join(group_path)
    path_bias = bias_cfg.risk_scores_by_path.get(path_key, {})
    scores: Dict[str, int] = {}
    for name in group_names:
        scores[name] = int(bias_cfg.risk_scores_global.get(name, 0)) + int(path_bias.get(name, 0))
    return scores


def generate_profile_hierarchy(
    base_hierarchy: Dict[str, Any],
    profile: ProfileDefinition,
    bias_cfg: ProfileBiasConfig,
    variability: VariabilityConfig,
    sample_seed: int,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    hierarchy = copy.deepcopy(base_hierarchy)
    _normalize_empty_risk_nodes(hierarchy)
    rng = random.Random(sample_seed)
    perturbations: List[Dict[str, Any]] = []

    for scope, group_path, group_dict in _iter_comparison_groups(hierarchy):
        group_names = [name for name in group_dict.keys()]
        score_map = _score_map_for_group(scope, group_path, group_names, profile, bias_cfg)
        pairwise_map, conversion_trace = build_signed_pairwise_values(score_map, group_names)
        explicit_rule = _has_explicit_profile_rule(scope, group_path, profile)
        has_non_zero_signal = any(int(v) != 0 for v in score_map.values())
        sigma = _sigma_for_scope(scope, variability)

        for current_name, current_node in group_dict.items():
            if not isinstance(current_node, dict):
                continue
            compare_obj = current_node.get("compare")
            if compare_obj is None:
                continue

            for target_name, raw_value, token in list(_iter_compare_entries(compare_obj)):
                if target_name not in group_dict:
                    continue

                old_value = _to_scale_int(raw_value)
                if explicit_rule or has_non_zero_signal:
                    pre_mc_value = int(pairwise_map[(current_name, target_name)])
                else:
                    pre_mc_value = old_value
                deterministic_delta = int(pre_mc_value - old_value)
                noise = int(round(rng.gauss(0.0, sigma))) if sigma > 0 else 0
                new_value = clamp_scale_value(pre_mc_value + noise)

                _set_compare_value(compare_obj, token, new_value)
                perturbations.append({
                    "scope": scope,
                    "group_path": group_path,
                    "current": current_name,
                    "target": target_name,
                    "old_value": old_value,
                    "parsed_profile_order": conversion_trace["parsed_profile_order"],
                    "relative_ranks": conversion_trace["relative_ranks"],
                    "pre_montecarlo_value": pre_mc_value,
                    "deterministic_delta": deterministic_delta,
                    "random_noise": noise,
                    "new_value": new_value,
                })

    return hierarchy, perturbations


def generate_samples_for_profile(
    base_hierarchy: Dict[str, Any],
    profile: ProfileDefinition,
    bias_cfg: ProfileBiasConfig,
    variability: VariabilityConfig,
    samples: int,
    seed: int,
    out_dir: str | Path,
) -> List[GeneratedSample]:
    import yaml

    out_base = Path(out_dir)
    generated_dir = out_base / profile.profile_id / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    results: List[GeneratedSample] = []

    profile_offset = _profile_seed_offset(profile.profile_id)
    for sample_index in range(samples):
        sample_seed = seed + profile_offset * 100_000 + sample_index
        generated_hierarchy, perturbations = generate_profile_hierarchy(
            base_hierarchy=base_hierarchy,
            profile=profile,
            bias_cfg=bias_cfg,
            variability=variability,
            sample_seed=sample_seed,
        )

        sample_name = f"sample_{sample_index:04d}"
        hierarchy_path = generated_dir / f"{sample_name}.yaml"
        metadata_path = generated_dir / f"{sample_name}.meta.json"

        with hierarchy_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(generated_hierarchy, f, allow_unicode=True, sort_keys=False)

        metadata = {
            "profile_id": profile.profile_id,
            "profile_name": profile.name,
            "profile_description": profile.description,
            "profile_expression": profile.expression,
            "stage_scores": profile.stage_scores,
            "stage_pairwise_deltas": {f"{k[0]} -> {k[1]}": v for k, v in profile.stage_pairwise_deltas.items()},
            "parsed_factor_rules": profile.parsed_factor_rules,
            "parsed_risk_profile": profile.parsed_risk_profile,
            "factor_biases": bias_cfg.factor_scores_by_stage,
            "risk_biases_global": bias_cfg.risk_scores_global,
            "risk_biases_by_path": bias_cfg.risk_scores_by_path,
            "sample_index": sample_index,
            "sample_seed": sample_seed,
            "variability": {
                "stage_sigma": variability.stage_sigma,
                "factor_sigma": variability.factor_sigma,
                "risk_sigma": variability.risk_sigma,
            },
            "perturbations": perturbations,
        }
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        results.append(
            GeneratedSample(
                profile_id=profile.profile_id,
                profile_name=profile.name,
                sample_index=sample_index,
                sample_seed=sample_seed,
                hierarchy_path=hierarchy_path,
                metadata_path=metadata_path,
            )
        )

    LOGGER.info("Generated %s samples for profile %s", len(results), profile.profile_id)
    return results
