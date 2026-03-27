# Monte Carlo Simulated-Expert AHP

## Overview
This project supports Monte Carlo simulation of expert AHP judgments for multiple profiles while preserving the single-run flow (`ahp_risk_analysis.py`).

Workflow:
1. Read base hierarchy from `hierarchy.yaml`.
2. Read schema/scale aliases from `config.yaml`.
3. Read profile rules from `profiles.yaml`.
4. Validate IDs and risk placement against the base hierarchy.
5. Generate perturbed hierarchy variants per profile.
6. Run AHP for each sample.
7. Filter by CR threshold.
8. Aggregate results into JSON/CSV/Markdown (+ optional charts).

## `config.yaml`
`config.yaml` defines:
- `version`
- `aliases` for `stages`, `factors`, `risks`
- `scale.relations` for expression operators (`=`, `>`, `>>`)
- `scale.priorities` for risk levels (`low`, `medium`, `high`, `very_high`)

Aliases are labels only. Stable internal IDs are used in profile rules.

## `profiles.yaml`
Top-level format:
- `version`
- profile entries (`P1`, `P2`, ...)

Each profile supports:
- `name`
- `description`
- `stages` expression, e.g. `KA = TR > OP > KS`
- `factors` per stage, e.g. `OP: T >> H`
- `risks` per stage/factor with symbolic levels

Example:

```yaml
version: 1
P1:
  name: AI/ML-heavy
  description: Focus on uncertainty and calibration
  stages: KA = TR > OP > KS
  factors:
    KS: H > T
    OP: T >> H
  risks:
    KA:
      T:
        lack_of_uncertainty_estimation: very_high
```

## Rule interpretation
- Stage/factor expressions use `config.scale.relations`.
- Risk levels use `config.scale.priorities`.
- Risk IDs are validated to belong to the exact stage/factor group in base hierarchy.

## Bias composition
For each existing pairwise comparison:
1. Start from base integer value.
2. Add deterministic profile bias delta.
3. Add random perturbation noise.
4. Clamp to integer range `[-9, 9]`.

No new hierarchy structure is invented; only existing comparison values are modified.

## CR filtering
Default threshold: `0.1`.

Modes:
- `any`: reject if any matrix has `CR >= threshold`
- `root_only`: reject only by root matrix CR

## CLI
Run:

```bash
python -m ahp_cli montecarlo \
  --base in/hierarchy.yaml \
  --config in/config.yaml \
  --profiles in/profiles.yaml \
  --samples 200 \
  --seed 42 \
  --out out/montecarlo \
  --variability 1.0 \
  --cr-mode any \
  --cr-threshold 0.1
```

Optional:
- `--profile-ids P1,P3`
- `--dry-run`
- `--stop-on-error`

## Output structure
```text
out/montecarlo/
  settings.json
  P1/
    generated/
      sample_0000.yaml
      sample_0000.meta.json
    runs/
      raw_results.json
      raw_results.csv
  P2/
    ...
  summary/
    all_runs.json
    all_runs.csv
    acceptance.csv
    risk_stats.csv
    cross_profile.json
    summary.json
    report.md
    accepted_vs_generated.png            # optional
    mean_weight_heatmap.png              # optional
    top5_frequency_P1.png                # optional
```

Per-sample metadata includes:
- profile id/name
- parsed stage rule
- parsed factor rules
- parsed/applied risk-level biases
- random perturbations
- seed and sample index

## Analysis outputs
Per profile:
- generated / accepted count and %
- mean/std/median global risk weight
- top-3/top-5/top-10 frequency
- mean rank + rank stability

Cross-profile:
- invariant risks (top-N intersection)
- profile-sensitive risks (rank-range threshold)
- Spearman rho / Kendall tau correlations

## Single-run compatibility
Single-run flow is unchanged:

```bash
python ahp_risk_analysis.py
```
