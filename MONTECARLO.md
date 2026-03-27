# Monte Carlo Simulated-Expert AHP

## Overview
This project now supports Monte Carlo simulation of expert AHP judgments for multiple profiles while preserving the existing single-run flow (`ahp_risk_analysis.py`).

The Monte Carlo workflow:
1. Reads a base hierarchy from YAML.
2. Reads profile definitions from `profiles.yml`.
3. Applies profile-specific stage/factor/risk bias deltas.
4. Adds random perturbations to existing pairwise comparisons.
5. Runs AHP for each generated sample.
6. Filters by consistency ratio (CR).
7. Produces JSON/CSV summaries and a markdown report.

## Profiles file (`profiles.yml`)
Example:

```yaml
P1:
  name: AI/ML-heavy
  profile: KA = TR > OP > KS
P2:
  name: Swarm/Ops-heavy
  profile: OP >> TR > KA > KS
```

### Symbolic expression mapping
`profile` expressions are parsed with:
- `=`: equal priority (delta `0`)
- `>`: moderate priority gap (delta `2` by default)
- `>>`: strong priority gap (delta `4` by default)

These values are configurable from CLI:
- `--stage-step` for `>`
- `--stage-strong-step` for `>>`

Default stage code aliases:
- `KS` -> `Knowledge selection`
- `KA` -> `Knowledge analysis`
- `TR` -> `AGPM Training`
- `OP` -> `Model operation`

## Bias composition
Each generated comparison value is adjusted as:
1. Existing base value
2. Plus deterministic profile bias delta
3. Plus random perturbation noise
4. Clamped to integer range `[-9, 9]`

Profile biases are split by scope:
- Stage level (from `profiles.yml` expression)
- Factor level (code config)
- Risk level (code config)

Default factor/risk profile biases are defined in `montecarlo/biases.py`.

## CR filtering
Filtering threshold defaults to `0.1`.

Modes:
- `any` (default): reject run if any matrix has `CR >= threshold`
- `root_only`: reject run only by root matrix CR

## CLI
Entry point:

```bash
python -m ahp_cli montecarlo \
  --base in/hierarchy.yaml \
  --profiles in/profiles.yml \
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
Example output:

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
    accepted_vs_generated.png            # optional (if matplotlib available)
    mean_weight_heatmap.png              # optional (if matplotlib available)
    top5_frequency_P1.png                # optional (if matplotlib available)
```

Per-sample metadata includes:
- profile id/name/expression
- parsed stage scores and pairwise deltas
- factor/risk bias config applied
- perturbation entries
- seed and sample index

## Analysis outputs
Per profile:
- generated/accepted counts and acceptance %
- risk mean/std/median global weight
- top-3/top-5/top-10 frequency
- mean rank and rank stability

Cross profile:
- invariant risks (intersection of top-N)
- profile-sensitive risks (large rank range)
- rank correlations (Spearman rho, Kendall tau)
- optional charts (if matplotlib is installed)

## Single-run compatibility
The original single-run pipeline remains available:

```bash
python ahp_risk_analysis.py
```
