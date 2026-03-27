from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Tuple


DEFAULT_STAGE_ALIASES: Dict[str, str] = {
    "KS": "Knowledge selection",
    "KA": "Knowledge analysis",
    "TR": "AGPM Training",
    "OP": "Model operation",
}


@dataclass(frozen=True)
class RelationStrength:
    equal: int = 0
    greater: int = 2
    much_greater: int = 4


@dataclass(frozen=True)
class ProfileDefinition:
    profile_id: str
    name: str
    expression: str
    stage_scores: Dict[str, int]
    stage_pairwise_deltas: Dict[Tuple[str, str], int]


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


def parse_stage_expression(
    expression: str,
    stage_aliases: Mapping[str, str] | None = None,
    relation_strength: RelationStrength | None = None,
) -> Dict[str, int]:
    aliases = dict(stage_aliases or DEFAULT_STAGE_ALIASES)
    strengths = relation_strength or RelationStrength()
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
        if op == "=":
            step = strengths.equal
        elif op == ">":
            step = strengths.greater
        else:
            step = strengths.much_greater
        current_score -= step
        scores_by_code[stage_code] = current_score

    return {aliases[code]: score for code, score in scores_by_code.items()}


def stage_pairwise_deltas(stage_scores: Mapping[str, int]) -> Dict[Tuple[str, str], int]:
    deltas: Dict[Tuple[str, str], int] = {}
    stages = list(stage_scores.keys())
    for current in stages:
        for target in stages:
            if current == target:
                continue
            deltas[(current, target)] = int(stage_scores[target] - stage_scores[current])
    return deltas


def load_profiles(
    profiles_path: str | Path,
    stage_aliases: Mapping[str, str] | None = None,
    relation_strength: RelationStrength | None = None,
) -> Dict[str, ProfileDefinition]:
    import yaml

    path = Path(profiles_path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    if not isinstance(raw, dict):
        raise ValueError(f"Profiles file '{path}' must contain a mapping of profile ids")

    profiles: Dict[str, ProfileDefinition] = {}
    for profile_id, payload in raw.items():
        if not isinstance(payload, dict):
            raise ValueError(f"Profile '{profile_id}' must be a mapping")

        name = payload.get("name")
        expression = payload.get("profile")
        if not name or not isinstance(name, str):
            raise ValueError(f"Profile '{profile_id}' missing string field 'name'")
        if not expression or not isinstance(expression, str):
            raise ValueError(f"Profile '{profile_id}' missing string field 'profile'")

        stage_scores = parse_stage_expression(expression, stage_aliases=stage_aliases, relation_strength=relation_strength)
        profiles[profile_id] = ProfileDefinition(
            profile_id=profile_id,
            name=name,
            expression=expression,
            stage_scores=stage_scores,
            stage_pairwise_deltas=stage_pairwise_deltas(stage_scores),
        )

    return profiles
