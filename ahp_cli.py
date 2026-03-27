from __future__ import annotations

import argparse
import json
import logging
from typing import Sequence

from montecarlo.workflow import MonteCarloConfig, run_montecarlo


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AHP tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    montecarlo = subparsers.add_parser("montecarlo", help="Run Monte Carlo simulated-expert AHP")
    montecarlo.add_argument("--base", default="in/hierarchy.yaml", help="Base hierarchy YAML path")
    montecarlo.add_argument("--profiles", default="in/profiles.yaml", help="Profiles YAML path")
    montecarlo.add_argument("--samples", type=int, default=200, help="Samples per profile")
    montecarlo.add_argument("--out", default="out/montecarlo", help="Output directory")
    montecarlo.add_argument("--seed", type=int, default=42, help="Random seed")
    montecarlo.add_argument("--variability", type=float, default=1.0, help="Variability sigma for perturbations")
    montecarlo.add_argument(
        "--profile-ids",
        default="",
        help="Comma-separated subset of profile ids, e.g. P1,P3",
    )
    montecarlo.add_argument(
        "--cr-mode",
        default="any",
        choices=["any", "root_only"],
        help="Consistency filtering mode",
    )
    montecarlo.add_argument("--cr-threshold", type=float, default=0.1, help="CR rejection threshold")
    montecarlo.add_argument("--dry-run", action="store_true", help="Parse config and print plan only")
    montecarlo.add_argument("--stop-on-error", action="store_true", help="Stop batch on first execution error")
    montecarlo.add_argument("--stage-step", type=int, default=2, help="Bias delta for '>' relation")
    montecarlo.add_argument("--stage-strong-step", type=int, default=4, help="Bias delta for '>>' relation")
    montecarlo.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if args.command == "montecarlo":
        profile_ids = [part.strip() for part in args.profile_ids.split(",") if part.strip()] or None
        config = MonteCarloConfig(
            base_yaml=args.base,
            profiles_yaml=args.profiles,
            samples_per_profile=args.samples,
            out_dir=args.out,
            seed=args.seed,
            variability_strength=args.variability,
            profile_ids=profile_ids,
            cr_threshold=args.cr_threshold,
            cr_mode=args.cr_mode,
            dry_run=args.dry_run,
            stop_on_error=args.stop_on_error,
            stage_step=args.stage_step,
            stage_strong_step=args.stage_strong_step,
        )
        payload = run_montecarlo(config)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
