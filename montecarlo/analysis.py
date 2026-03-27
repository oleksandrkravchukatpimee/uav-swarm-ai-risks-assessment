from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from montecarlo.profiles import ProfileDefinition


def _ordered_risks(weights: Mapping[str, float]) -> List[str]:
    return [name for name, _ in sorted(weights.items(), key=lambda x: (-x[1], x[0]))]


def _rank_map(weights: Mapping[str, float]) -> Dict[str, int]:
    ordered = _ordered_risks(weights)
    return {risk: idx + 1 for idx, risk in enumerate(ordered)}


def _spearman_rho(rank_a: Mapping[str, int], rank_b: Mapping[str, int]) -> float:
    common = sorted(set(rank_a).intersection(rank_b))
    n = len(common)
    if n < 2:
        return 0.0
    diffs_sq = [(rank_a[key] - rank_b[key]) ** 2 for key in common]
    return 1.0 - (6.0 * sum(diffs_sq)) / (n * (n * n - 1))


def _kendall_tau(rank_a: Mapping[str, int], rank_b: Mapping[str, int]) -> float:
    common = sorted(set(rank_a).intersection(rank_b))
    n = len(common)
    if n < 2:
        return 0.0

    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            x1 = rank_a[common[i]] - rank_a[common[j]]
            x2 = rank_b[common[i]] - rank_b[common[j]]
            product = x1 * x2
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1

    denom = n * (n - 1) / 2
    if denom == 0:
        return 0.0
    return (concordant - discordant) / denom


def _safe_stats(values: Sequence[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "std": 0.0, "median": 0.0}
    return {
        "mean": float(mean(values)),
        "std": float(pstdev(values)) if len(values) > 1 else 0.0,
        "median": float(median(values)),
    }


def summarize_results(
    raw_results: Iterable[Dict[str, Any]],
    profiles: Mapping[str, ProfileDefinition],
    out_dir: str | Path,
    top_ks: Tuple[int, int, int] = (3, 5, 10),
    invariant_top_n: int = 5,
    sensitive_rank_range: int = 5,
) -> Dict[str, Any]:
    out_base = Path(out_dir)
    summary_dir = out_base / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in raw_results:
        grouped[row["profile_id"]].append(row)

    profile_summary: Dict[str, Any] = {}
    profile_mean_weights: Dict[str, Dict[str, float]] = {}
    profile_rank_maps: Dict[str, Dict[str, int]] = {}

    risk_stats_rows: List[Dict[str, Any]] = []
    acceptance_rows: List[Dict[str, Any]] = []

    for profile_id, runs in grouped.items():
        accepted_runs = [run for run in runs if run.get("accepted") and not run.get("error")]
        generated_count = len(runs)
        accepted_count = len(accepted_runs)
        acceptance_rate = (accepted_count / generated_count * 100.0) if generated_count else 0.0

        all_risks = sorted({risk for run in accepted_runs for risk in run.get("global_weights", {}).keys()})
        values_by_risk: Dict[str, List[float]] = {risk: [] for risk in all_risks}
        ranks_by_risk: Dict[str, List[int]] = {risk: [] for risk in all_risks}
        topk_counts: Dict[int, Counter[str]] = {k: Counter() for k in top_ks}

        for run in accepted_runs:
            weights = {k: float(v) for k, v in run.get("global_weights", {}).items()}
            ordered = _ordered_risks(weights)
            rank_map = {name: idx + 1 for idx, name in enumerate(ordered)}

            for risk in all_risks:
                values_by_risk[risk].append(weights.get(risk, 0.0))
                ranks_by_risk[risk].append(rank_map.get(risk, len(ordered) + 1))

            for k in top_ks:
                for risk in ordered[:k]:
                    topk_counts[k][risk] += 1

        risk_stats: Dict[str, Dict[str, float]] = {}
        for risk in all_risks:
            stats = _safe_stats(values_by_risk[risk])
            stats["mean_rank"] = float(mean(ranks_by_risk[risk])) if ranks_by_risk[risk] else 0.0
            stats["rank_std"] = float(pstdev(ranks_by_risk[risk])) if len(ranks_by_risk[risk]) > 1 else 0.0
            for k in top_ks:
                freq = topk_counts[k][risk]
                stats[f"top{k}_freq"] = int(freq)
                stats[f"top{k}_pct"] = float((freq / accepted_count * 100.0) if accepted_count else 0.0)
            risk_stats[risk] = stats

            risk_stats_rows.append({
                "profile_id": profile_id,
                "risk": risk,
                "mean": stats["mean"],
                "std": stats["std"],
                "median": stats["median"],
                "mean_rank": stats["mean_rank"],
                "rank_std": stats["rank_std"],
                "top3_freq": stats.get("top3_freq", 0),
                "top3_pct": stats.get("top3_pct", 0.0),
                "top5_freq": stats.get("top5_freq", 0),
                "top5_pct": stats.get("top5_pct", 0.0),
                "top10_freq": stats.get("top10_freq", 0),
                "top10_pct": stats.get("top10_pct", 0.0),
            })

        mean_weights = {risk: stats["mean"] for risk, stats in risk_stats.items()}
        profile_mean_weights[profile_id] = mean_weights
        profile_rank_maps[profile_id] = _rank_map(mean_weights) if mean_weights else {}

        top_risks = _ordered_risks(mean_weights)[:10]
        profile_summary[profile_id] = {
            "profile_name": profiles[profile_id].name if profile_id in profiles else profile_id,
            "profile_expression": profiles[profile_id].expression if profile_id in profiles else "",
            "generated_runs": generated_count,
            "accepted_runs": accepted_count,
            "accepted_pct": acceptance_rate,
            "risk_stats": risk_stats,
            "top_risks_mean_weight": top_risks,
        }

        acceptance_rows.append({
            "profile_id": profile_id,
            "profile_name": profile_summary[profile_id]["profile_name"],
            "generated_runs": generated_count,
            "accepted_runs": accepted_count,
            "accepted_pct": acceptance_rate,
        })

    all_profile_ids = sorted(profile_summary.keys())
    all_risks = sorted({risk for profile_id in all_profile_ids for risk in profile_mean_weights.get(profile_id, {})})

    risk_rank_ranges: Dict[str, int] = {}
    for risk in all_risks:
        ranks = [profile_rank_maps[pid].get(risk, len(all_risks) + 1) for pid in all_profile_ids]
        risk_rank_ranges[risk] = max(ranks) - min(ranks) if ranks else 0

    top_sets = []
    for profile_id in all_profile_ids:
        ordered = _ordered_risks(profile_mean_weights.get(profile_id, {}))
        top_sets.append(set(ordered[:invariant_top_n]))

    invariant_risks = sorted(set.intersection(*top_sets)) if top_sets else []
    profile_sensitive_risks = sorted([risk for risk, rr in risk_rank_ranges.items() if rr >= sensitive_rank_range])

    profile_correlations: Dict[str, Dict[str, float]] = {}
    for i, profile_a in enumerate(all_profile_ids):
        for profile_b in all_profile_ids[i + 1 :]:
            rank_a = profile_rank_maps.get(profile_a, {})
            rank_b = profile_rank_maps.get(profile_b, {})
            key = f"{profile_a}__{profile_b}"
            profile_correlations[key] = {
                "spearman_rho": _spearman_rho(rank_a, rank_b),
                "kendall_tau": _kendall_tau(rank_a, rank_b),
            }

    cross_profile_summary = {
        "invariant_risks_top_n": invariant_top_n,
        "invariant_risks": invariant_risks,
        "sensitive_rank_range_threshold": sensitive_rank_range,
        "profile_sensitive_risks": profile_sensitive_risks,
        "risk_rank_ranges": risk_rank_ranges,
        "profile_correlations": profile_correlations,
    }

    summary_payload = {
        "profiles": profile_summary,
        "cross_profile": cross_profile_summary,
    }

    with (summary_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary_payload, f, ensure_ascii=False, indent=2)

    with (summary_dir / "acceptance.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["profile_id", "profile_name", "generated_runs", "accepted_runs", "accepted_pct"])
        writer.writeheader()
        writer.writerows(acceptance_rows)

    with (summary_dir / "risk_stats.csv").open("w", encoding="utf-8", newline="") as f:
        if risk_stats_rows:
            writer = csv.DictWriter(f, fieldnames=list(risk_stats_rows[0].keys()))
            writer.writeheader()
            writer.writerows(risk_stats_rows)
        else:
            writer = csv.writer(f)
            writer.writerow(["profile_id", "risk", "mean", "std", "median", "mean_rank", "rank_std", "top3_freq", "top3_pct", "top5_freq", "top5_pct", "top10_freq", "top10_pct"])

    with (summary_dir / "cross_profile.json").open("w", encoding="utf-8") as f:
        json.dump(cross_profile_summary, f, ensure_ascii=False, indent=2)

    _try_generate_charts(summary_dir, profile_summary, profile_mean_weights, acceptance_rows)
    _write_markdown_report(summary_dir / "report.md", summary_payload)
    return summary_payload


def _try_generate_charts(
    summary_dir: Path,
    profile_summary: Mapping[str, Any],
    profile_mean_weights: Mapping[str, Mapping[str, float]],
    acceptance_rows: Sequence[Mapping[str, Any]],
) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return

    # Accepted vs generated per profile
    if acceptance_rows:
        labels = [row["profile_id"] for row in acceptance_rows]
        generated = [row["generated_runs"] for row in acceptance_rows]
        accepted = [row["accepted_runs"] for row in acceptance_rows]
        x = list(range(len(labels)))

        plt.figure(figsize=(8, 4))
        plt.bar([i - 0.2 for i in x], generated, width=0.4, label="Generated")
        plt.bar([i + 0.2 for i in x], accepted, width=0.4, label="Accepted")
        plt.xticks(x, labels)
        plt.ylabel("Runs")
        plt.title("Accepted vs Generated Runs")
        plt.legend()
        plt.tight_layout()
        plt.savefig(summary_dir / "accepted_vs_generated.png", dpi=150)
        plt.close()

    # Heatmap of mean risk weights by profile
    all_profiles = sorted(profile_mean_weights.keys())
    all_risks = sorted({risk for pid in all_profiles for risk in profile_mean_weights.get(pid, {})})
    if all_profiles and all_risks:
        matrix: List[List[float]] = []
        for profile_id in all_profiles:
            matrix.append([float(profile_mean_weights[profile_id].get(risk, 0.0)) for risk in all_risks])

        plt.figure(figsize=(max(8, len(all_risks) * 0.25), max(4, len(all_profiles) * 0.5)))
        plt.imshow(matrix, aspect="auto")
        plt.colorbar(label="Mean global weight")
        plt.yticks(range(len(all_profiles)), all_profiles)
        plt.xticks(range(len(all_risks)), all_risks, rotation=90)
        plt.title("Mean Risk Weights by Profile")
        plt.tight_layout()
        plt.savefig(summary_dir / "mean_weight_heatmap.png", dpi=150)
        plt.close()

    # Top-5 frequency per profile (single chart per profile)
    for profile_id, payload in profile_summary.items():
        stats = payload.get("risk_stats", {})
        rows = sorted(
            [(risk, data.get("top5_freq", 0)) for risk, data in stats.items()],
            key=lambda x: (-x[1], x[0]),
        )[:10]
        if not rows:
            continue
        labels = [r[0] for r in rows]
        values = [r[1] for r in rows]

        plt.figure(figsize=(8, 4))
        plt.bar(labels, values)
        plt.xticks(rotation=60, ha="right")
        plt.ylabel("Count")
        plt.title(f"Top-5 Frequency ({profile_id})")
        plt.tight_layout()
        plt.savefig(summary_dir / f"top5_frequency_{profile_id}.png", dpi=150)
        plt.close()


def _write_markdown_report(report_path: Path, summary_payload: Dict[str, Any]) -> None:
    profiles = summary_payload["profiles"]
    cross = summary_payload["cross_profile"]

    lines: List[str] = []
    lines.append("# Monte Carlo AHP Report")
    lines.append("")
    lines.append("## Profile Acceptance")
    lines.append("")
    lines.append("| Profile | Generated | Accepted | Accepted % |")
    lines.append("|---|---:|---:|---:|")
    for profile_id, payload in sorted(profiles.items()):
        lines.append(
            f"| {profile_id} ({payload['profile_name']}) | {payload['generated_runs']} | {payload['accepted_runs']} | {payload['accepted_pct']:.2f} |"
        )

    lines.append("")
    lines.append("## Top Risks by Mean Weight")
    lines.append("")
    for profile_id, payload in sorted(profiles.items()):
        lines.append(f"### {profile_id} - {payload['profile_name']}")
        top = payload["top_risks_mean_weight"][:10]
        for risk in top:
            risk_stats = payload["risk_stats"][risk]
            lines.append(f"- {risk}: mean={risk_stats['mean']:.4f}, std={risk_stats['std']:.4f}, median={risk_stats['median']:.4f}")
        lines.append("")

    lines.append("## Cross-profile")
    lines.append("")
    lines.append(f"- Invariant risks (top-{cross['invariant_risks_top_n']} intersection): {', '.join(cross['invariant_risks']) or 'None'}")
    lines.append(
        f"- Profile-sensitive risks (rank range >= {cross['sensitive_rank_range_threshold']}): "
        f"{', '.join(cross['profile_sensitive_risks']) or 'None'}"
    )
    lines.append("")
    lines.append("### Ranking Correlations")
    for pair, corr in sorted(cross["profile_correlations"].items()):
        lines.append(f"- {pair}: Spearman={corr['spearman_rho']:.4f}, Kendall={corr['kendall_tau']:.4f}")

    with report_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
