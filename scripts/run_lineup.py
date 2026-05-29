from __future__ import annotations

import argparse
from pathlib import Path

from softball_sim.stats_import import load_stats
from softball_sim.model import build_params
from softball_sim.sim import SimConfig, inning_start_distribution, simulate_games


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SoftballSim: run lineup simulations")
    p.add_argument("--stats", required=True, help="Stats JSON file (season + two_game)")
    p.add_argument("--lineup", required=True, help="Lineup as N names: 'First Last; First Last; ...' (typically 9-13)")
    p.add_argument("--R", type=float, default=0.33)
    p.add_argument("--err-bases", type=int, default=2)
    p.add_argument("--games", type=int, default=200_000)
    p.add_argument("--seed", type=int, default=424242)
    p.add_argument("--lambda", dest="lam", type=float, default=15.0)
    p.add_argument(
        "--shrink-k",
        type=float,
        default=10.0,
        help="Pseudo-AB toward team mean (Bayesian shrinkage). 0 = none; ~10 (the default) is reasonable for small-sample 8U-10U data. Pass --shrink-k 0 to use raw rates.",
    )
    return p.parse_args()


def parse_lineup(s: str):
    parts = [x.strip() for x in s.split(";") if x.strip()]
    out = []
    for part in parts:
        toks = part.split()
        if len(toks) < 2:
            raise SystemExit(f"Bad lineup entry: {part!r}")
        first = toks[0]
        last = toks[1]
        out.append((first, last))
    if len(out) < 1:
        raise SystemExit("Lineup must contain at least 1 batter")
    return out


def main() -> None:
    a = parse_args()

    stats = load_stats(Path(a.stats))
    merged = stats["combined"]

    params = build_params(merged, shrink_k=a.shrink_k)

    order = parse_lineup(a.lineup)
    lineup = [params[k] for k in order]

    cfg = SimConfig(R=a.R, err_bases=a.err_bases)
    totals = simulate_games(lineup, cfg, games=a.games, seed=a.seed)

    exp = sum(totals) / len(totals)
    p_lt10 = sum(1 for x in totals if x < 10) / len(totals)
    score = exp - a.lam * p_lt10

    dist = inning_start_distribution(lineup, cfg, games=a.games, seed=a.seed)

    print(f"E[runs]={exp:.3f}  P(<10)={p_lt10:.3f}  score=E-lambda*P={score:.3f}")
    print("inning_start_dist:")
    for i, v in enumerate(dist, 1):
        print(f"  {i}: {v*100:.2f}%")


if __name__ == "__main__":
    main()
