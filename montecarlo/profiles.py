from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple


VALID_STAGE_IDS = {"KS", "KA", "TR", "OP"}
VALID_FACTOR_IDS = {"H", "T"}
REQUIRED_RELATION_TOKENS = {"=", ">", ">>"}
REQUIRED_PRIORITY_LEVELS = {"low", "medium", "high", "very_high"}


@dataclass(frozen=True)
class ConfigDefinition:
    version: int
    stage_aliases: Dict[str, str]
    factor_aliases: Dict[str, str]
    risk_aliases: Dict[str, str]
    relation_scale: Dict[str, int]
    priority_scale: Dict[str, int]


@dataclass(frozen=True)
class HierarchyIndex:
    stage_id_to_label: Dict[str, str]
    factor_id_to_label: Dict[str, str]
    risk_id_to_label: Dict[str, str]
    risk_id_to_location_ids: Dict[str, Tuple[str, str]]


@dataclass(frozen=True)
class ProfileDefinition:
    profile_id: str
    name: str
    expression: str
    stage_scores: Dict[str, int]
    stage_pairwise_deltas: Dict[Tuple[str, str], int]
    description: str = ""
    factor_scores_by_stage: Dict[str, Dict[str, int]] = field(default_factory=dict)
    risk_scores_by_path: Dict[str, Dict[str, int]] = field(default_factory=dict)
    parsed_factor_rules: Dict[str, str] = field(default_factory=dict)
    parsed_risk_profile: Dict[str, Dict[str, Dict[str, int]]] = field(default_factory=dict)


def _tokenize_expression(expression: str) -> List[str]:
    text = "".join(expression.split())
    if not text:
        raise ValueError("Profile expression is empty")

    tokens: List[str] = []
    idx = 0
    while idx < len(text):
        if text.startswith(">>", idx):
            tokens.append(">>")
            idx += 2
            continue

        ch = text[idx]
        if ch in (">", "="):
            tokens.append(ch)
            idx += 1
            continue

        if ch.isalnum() or ch in ("_", "-"):
            end = idx + 1
            while end < len(text) and (text[end].isalnum() or text[end] in ("_", "-")):
                end += 1
            tokens.append(text[idx:end])
            idx = end
            continue

        raise ValueError(f"Unsupported symbol '{ch}' in expression '{expression}'")

    return tokens


def parse_relation_expression(
    expression: str,
    valid_ids: Mapping[str, str],
    relation_scale: Mapping[str, int],
) -> Dict[str, int]:
    aliases = dict(valid_ids)
    relations = dict(relation_scale)
    tokens = _tokenize_expression(expression)

    if len(tokens) < 3:
        raise ValueError(f"Invalid profile expression '{expression}': expected at least 3 tokens")
    if len(tokens) % 2 == 0:
        raise ValueError(f"Invalid profile expression '{expression}': malformed token sequence")

    stage_codes: List[str] = []
    operators: List[str] = []
    for idx, token in enumerate(tokens):
        if idx % 2 == 0:
            if token in (">", ">>", "="):
                raise ValueError(f"Invalid profile expression '{expression}': expected stage code at position {idx}")
            stage_codes.append(token)
        else:
            if token not in (">", ">>", "="):
                raise ValueError(f"Invalid profile expression '{expression}': unknown operator '{token}'")
            operators.append(token)

    unknown = [code for code in stage_codes if code not in aliases]
    if unknown:
        known = ", ".join(sorted(aliases))
        raise ValueError(f"Unknown stage code(s) {unknown} in expression '{expression}'. Known codes: {known}")

    if len(set(stage_codes)) != len(stage_codes):
        raise ValueError(f"Duplicated stage code in expression '{expression}'")

    scores_by_code: Dict[str, int] = {}
    current_score = 0
    scores_by_code[stage_codes[0]] = current_score

    for op, stage_code in zip(operators, stage_codes[1:]):
        if op not in relations:
            raise ValueError(f"Relation '{op}' is not configured in config.scale.relations")
        step = int(relations[op])
        current_score -= step
        scores_by_code[stage_code] = current_score

    return scores_by_code


def stage_pairwise_deltas(stage_scores: Mapping[str, int]) -> Dict[Tuple[str, str], int]:
    deltas: Dict[Tuple[str, str], int] = {}
    stages = list(stage_scores.keys())
    for current in stages:
        for target in stages:
            if current == target:
                continue
            deltas[(current, target)] = int(stage_scores[target] - stage_scores[current])
    return deltas


def load_config(config_path: str | Path) -> ConfigDefinition:
    import yaml

    path = Path(config_path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    if not isinstance(raw, dict):
        raise ValueError(f"Config file '{path}' must contain a mapping")

    version = raw.get("version")
    if version != 1:
        raise ValueError(f"Unsupported config version '{version}'. Expected version=1")

    aliases = raw.get("aliases")
    if not isinstance(aliases, dict):
        raise ValueError("config.aliases must be a mapping")

    stage_aliases = aliases.get("stages")
    factor_aliases = aliases.get("factors")
    risk_aliases = aliases.get("risks")
    if not isinstance(stage_aliases, dict):
        raise ValueError("config.aliases.stages must be a mapping")
    if not isinstance(factor_aliases, dict):
        raise ValueError("config.aliases.factors must be a mapping")
    if not isinstance(risk_aliases, dict):
        raise ValueError("config.aliases.risks must be a mapping")

    unknown_stage_ids = set(stage_aliases) - VALID_STAGE_IDS
    missing_stage_ids = VALID_STAGE_IDS - set(stage_aliases)
    if unknown_stage_ids or missing_stage_ids:
        raise ValueError(
            f"Invalid stage ids in config.aliases.stages. Unknown={sorted(unknown_stage_ids)}, missing={sorted(missing_stage_ids)}"
        )

    unknown_factor_ids = set(factor_aliases) - VALID_FACTOR_IDS
    missing_factor_ids = VALID_FACTOR_IDS - set(factor_aliases)
    if unknown_factor_ids or missing_factor_ids:
        raise ValueError(
            f"Invalid factor ids in config.aliases.factors. Unknown={sorted(unknown_factor_ids)}, missing={sorted(missing_factor_ids)}"
        )

    scale = raw.get("scale")
    if not isinstance(scale, dict):
        raise ValueError("config.scale must be a mapping")
    relations = scale.get("relations")
    priorities = scale.get("priorities")
    if not isinstance(relations, dict):
        raise ValueError("config.scale.relations must be a mapping")
    if not isinstance(priorities, dict):
        raise ValueError("config.scale.priorities must be a mapping")

    if REQUIRED_RELATION_TOKENS - set(relations):
        raise ValueError(f"config.scale.relations must define {sorted(REQUIRED_RELATION_TOKENS)}")
    if REQUIRED_PRIORITY_LEVELS - set(priorities):
        raise ValueError(f"config.scale.priorities must define {sorted(REQUIRED_PRIORITY_LEVELS)}")

    relation_scale: Dict[str, int] = {}
    for key, value in relations.items():
        relation_scale[str(key)] = int(value)

    priority_scale: Dict[str, int] = {}
    for key, value in priorities.items():
        priority_scale[str(key)] = int(value)

    return ConfigDefinition(
        version=1,
        stage_aliases={str(k): str(v) for k, v in stage_aliases.items()},
        factor_aliases={str(k): str(v) for k, v in factor_aliases.items()},
        risk_aliases={str(k): str(v) for k, v in risk_aliases.items()},
        relation_scale=relation_scale,
        priority_scale=priority_scale,
    )


def build_hierarchy_index(hierarchy: Mapping[str, Any], config: ConfigDefinition) -> HierarchyIndex:
    if not isinstance(hierarchy, dict):
        raise ValueError("Base hierarchy must be a mapping")

    missing_stage_ids = [stage_id for stage_id in config.stage_aliases if stage_id not in hierarchy]
    if missing_stage_ids:
        raise ValueError(f"Configured stage ids missing in hierarchy: {missing_stage_ids}")

    risk_id_to_location_ids: Dict[str, Tuple[str, str]] = {}
    for stage_id, stage_node in hierarchy.items():
        if stage_id not in config.stage_aliases:
            raise ValueError(f"Unknown stage id '{stage_id}' in hierarchy")
        if not isinstance(stage_node, dict):
            continue
        factors = stage_node.get("factors")
        if not isinstance(factors, dict):
            continue
        for factor_id, factor_node in factors.items():
            if factor_id not in config.factor_aliases:
                raise ValueError(f"Unknown factor id '{factor_id}' in hierarchy stage '{stage_id}'")
            if not isinstance(factor_node, dict):
                continue
            risks = factor_node.get("risks")
            if not isinstance(risks, dict):
                continue
            for risk_id in risks.keys():
                risk_id_str = str(risk_id)
                if risk_id_str in risk_id_to_location_ids:
                    prev = risk_id_to_location_ids[risk_id_str]
                    raise ValueError(
                        f"Risk id '{risk_id_str}' appears multiple times in hierarchy: {prev} and {(stage_id, factor_id)}"
                    )
                risk_id_to_location_ids[risk_id_str] = (str(stage_id), str(factor_id))

    unknown_risk_ids = set(risk_id_to_location_ids) - set(config.risk_aliases)
    if unknown_risk_ids:
        raise ValueError(f"Hierarchy contains risk ids missing from config.aliases.risks: {sorted(unknown_risk_ids)}")

    missing_risk_ids = set(config.risk_aliases) - set(risk_id_to_location_ids)
    if missing_risk_ids:
        raise ValueError(f"Config risk ids not found in hierarchy: {sorted(missing_risk_ids)}")

    return HierarchyIndex(
        stage_id_to_label=dict(config.stage_aliases),
        factor_id_to_label=dict(config.factor_aliases),
        risk_id_to_label=dict(config.risk_aliases),
        risk_id_to_location_ids=risk_id_to_location_ids,
    )


def load_profiles(
    profiles_path: str | Path,
    config: ConfigDefinition,
    hierarchy_index: HierarchyIndex,
) -> Dict[str, ProfileDefinition]:
    import yaml

    path = Path(profiles_path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    if not isinstance(raw, dict):
        raise ValueError(f"Profiles file '{path}' must contain a mapping of profile ids")

    version = raw.get("version")
    if version != config.version:
        raise ValueError(f"Profiles version '{version}' is incompatible with config version '{config.version}'")

    profile_entries = {k: v for k, v in raw.items() if k != "version"}
    if not profile_entries:
        raise ValueError(f"Profiles file '{path}' does not contain profile entries")

    profiles: Dict[str, ProfileDefinition] = {}
    for profile_id, payload in profile_entries.items():
        if not isinstance(payload, dict):
            raise ValueError(f"Profile '{profile_id}' must be a mapping")

        name = payload.get("name")
        description = payload.get("description", "")
        expression = payload.get("stage_profile", payload.get("stages", payload.get("profile")))
        if not name or not isinstance(name, str):
            raise ValueError(f"Profile '{profile_id}' missing string field 'name'")
        if not expression or not isinstance(expression, str):
            raise ValueError(f"Profile '{profile_id}' missing string field 'stage_profile' (or 'stages')")

        stage_scores = parse_relation_expression(
            expression=expression,
            valid_ids=config.stage_aliases,
            relation_scale=config.relation_scale,
        )
        if set(stage_scores) != set(config.stage_aliases):
            raise ValueError(
                f"Profile '{profile_id}' stage expression must include all stages: {sorted(config.stage_aliases)}"
            )

        factor_rules_raw = payload.get("factor_profile", payload.get("factors", {}))
        if factor_rules_raw is None:
            factor_rules_raw = {}
        if not isinstance(factor_rules_raw, dict):
            raise ValueError(f"Profile '{profile_id}' field 'factor_profile' must be a mapping")

        factor_scores_by_stage: Dict[str, Dict[str, int]] = {}
        parsed_factor_rules: Dict[str, str] = {}
        for stage_id, factor_expr in factor_rules_raw.items():
            stage_id_str = str(stage_id)
            if stage_id_str not in config.stage_aliases:
                raise ValueError(f"Profile '{profile_id}' factor rule uses unknown stage id '{stage_id_str}'")
            if not isinstance(factor_expr, str):
                raise ValueError(f"Profile '{profile_id}' factor rule for stage '{stage_id_str}' must be a string expression")

            parsed = parse_relation_expression(
                expression=factor_expr,
                valid_ids=config.factor_aliases,
                relation_scale=config.relation_scale,
            )
            if set(parsed) != set(config.factor_aliases):
                raise ValueError(
                    f"Profile '{profile_id}' factor expression for stage '{stage_id_str}' must include all factors: {sorted(config.factor_aliases)}"
                )
            factor_scores_by_stage[stage_id_str] = parsed
            parsed_factor_rules[stage_id_str] = factor_expr

        risk_rules_raw = payload.get("risk_profile", payload.get("risks", {}))
        if risk_rules_raw is None:
            risk_rules_raw = {}
        if not isinstance(risk_rules_raw, dict):
            raise ValueError(f"Profile '{profile_id}' field 'risk_profile' must be a mapping")

        risk_scores_by_path: Dict[str, Dict[str, int]] = {}
        parsed_risk_profile: Dict[str, Dict[str, Dict[str, int]]] = {}
        for stage_id, stage_payload in risk_rules_raw.items():
            stage_id_str = str(stage_id)
            if stage_id_str not in config.stage_aliases:
                raise ValueError(f"Profile '{profile_id}' risk rules use unknown stage id '{stage_id_str}'")
            if not isinstance(stage_payload, dict):
                raise ValueError(f"Profile '{profile_id}' risk rules for stage '{stage_id_str}' must be a mapping")

            parsed_risk_profile[stage_id_str] = {}
            for factor_id, factor_payload in stage_payload.items():
                factor_id_str = str(factor_id)
                if factor_id_str not in config.factor_aliases:
                    raise ValueError(
                        f"Profile '{profile_id}' risk rules use unknown factor id '{factor_id_str}' in stage '{stage_id_str}'"
                    )
                if not isinstance(factor_payload, dict):
                    raise ValueError(
                        f"Profile '{profile_id}' risk rules for '{stage_id_str}/{factor_id_str}' must be a mapping"
                    )

                parsed_risk_profile[stage_id_str][factor_id_str] = {}
                path_key = f"{stage_id_str} / {factor_id_str}"
                if path_key not in risk_scores_by_path:
                    risk_scores_by_path[path_key] = {}

                for risk_id, level in factor_payload.items():
                    risk_id_str = str(risk_id)
                    if risk_id_str not in config.risk_aliases:
                        raise ValueError(
                            f"Profile '{profile_id}' risk rules use unknown risk id '{risk_id_str}' in '{stage_id_str}/{factor_id_str}'"
                        )
                    if risk_id_str not in hierarchy_index.risk_id_to_location_ids:
                        raise ValueError(
                            f"Profile '{profile_id}' risk '{risk_id_str}' is not present in base hierarchy aliases"
                        )
                    if hierarchy_index.risk_id_to_location_ids[risk_id_str] != (stage_id_str, factor_id_str):
                        expected = hierarchy_index.risk_id_to_location_ids[risk_id_str]
                        raise ValueError(
                            f"Profile '{profile_id}' risk '{risk_id_str}' placed under '{stage_id_str}/{factor_id_str}', "
                            f"but hierarchy defines it under '{expected[0]}/{expected[1]}'"
                        )
                    level_key = str(level)
                    if level_key not in config.priority_scale:
                        raise ValueError(
                            f"Profile '{profile_id}' risk '{risk_id_str}' uses unknown priority level '{level_key}'"
                        )
                    priority_value = int(config.priority_scale[level_key])
                    risk_scores_by_path[path_key][risk_id_str] = priority_value
                    parsed_risk_profile[stage_id_str][factor_id_str][risk_id_str] = priority_value

        profiles[profile_id] = ProfileDefinition(
            profile_id=profile_id,
            name=name,
            description=description if isinstance(description, str) else "",
            expression=expression,
            stage_scores=stage_scores,
            stage_pairwise_deltas=stage_pairwise_deltas(stage_scores),
            factor_scores_by_stage=factor_scores_by_stage,
            risk_scores_by_path=risk_scores_by_path,
            parsed_factor_rules=parsed_factor_rules,
            parsed_risk_profile=parsed_risk_profile,
        )

    return profiles
