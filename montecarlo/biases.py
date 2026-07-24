from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping


@dataclass(frozen=True)
class ProfileBiasConfig:
    factor_scores_by_stage: Dict[str, Dict[str, int]] = field(default_factory=dict)
    risk_scores_global: Dict[str, int] = field(default_factory=dict)
    risk_scores_by_path: Dict[str, Dict[str, int]] = field(default_factory=dict)


DEFAULT_PROFILE_BIASES: Dict[str, ProfileBiasConfig] = {
    "P1": ProfileBiasConfig(
        factor_scores_by_stage={
            "Knowledge analysis": {"Human": 1, "Technological": 1},
            "Model Training": {"Human": 1, "Technological": 1},
        },
        risk_scores_global={
            "Lack of uncertainty estimation": 3,
            "Confabulations": 2,
            "Confidence miscalibration": 2,
            "Domain shift": 2,
            "Incomplete validation criteria": 2,
        },
    ),
    "P2": ProfileBiasConfig(
        factor_scores_by_stage={
            "Model operation": {"Human": 1, "Technological": 2},
        },
        risk_scores_global={
            "Cascading error propagation": 3,
            "Sensor artifacts": 2,
            "Concept drift": 2,
            "Loss of situational awareness": 2,
        },
    ),
    "P3": ProfileBiasConfig(
        factor_scores_by_stage={},
        risk_scores_global={},
    ),
    "P4": ProfileBiasConfig(
        factor_scores_by_stage={
            "Knowledge analysis": {"Human": 2},
            "Model Training": {"Human": 2},
            "Model operation": {"Human": 1, "Technological": 1},
        },
        risk_scores_global={
            "Lack of uncertainty estimation": 3,
            "Incomplete validation criteria": 3,
            "Confidence miscalibration": 3,
            "Loss of situational awareness": 2,
            "Domain shift": 1,
        },
    ),
}


def get_profile_bias_config(
    profile_id: str,
    overrides: Mapping[str, ProfileBiasConfig] | None = None,
) -> ProfileBiasConfig:
    if overrides and profile_id in overrides:
        return overrides[profile_id]
    return DEFAULT_PROFILE_BIASES.get(profile_id, ProfileBiasConfig())
