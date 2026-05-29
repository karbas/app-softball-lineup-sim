from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from softball_sim.stats_import import load_stats
from softball_sim.model import build_params, BatterParams
from softball_sim.sim import SimConfig

Name = Tuple[str, str]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Optimize lineup for weighted runs/inning (game-reset).")
    p.add_argument("--stats", required=True, help="Stats JSON file (season + two_game)")
    p.add_argument("--R", type=float, default=0.33)
    p.add_argument("--err-bases", type=int, default=2)
    p.add_argument("--seed", type=int, default=424242)

    p.add_argument("--games-eval", type=int, default=20000, help="Games per candidate during search")
    p.add_argument("--games-final", type=int, default=200000, help="Games to evaluate the best lineup")
    p.add_argument("--restarts", type=int, default=30)
    p.add_argument("--iters", type=int, default=400, help="Swap proposals per restart")

    p.add_argument("--blend-sofia", type=float, default=0.6)
    p.add_argument("--flip-olivia-brinkley", action="store_true")
    p.add_argument(
        "--shrink-k",
        type=float,
        default=10.0,
        help="Pseudo-AB toward team mean (Bayesian shrinkage). 0 = none; ~10 (the default) is reasonable for small-sample 8U-10U data. Pass --shrink-k 0 to use raw rates.",
    )

    p.add_argument(
        "--players",
        required=True,
        help="Roster as N players: 'First Last; First Last; ...' (typically 9-13)",
    )
    return p.parse_args()


def parse_list(s: str) -> List[Name]:
    parts = [x.strip() for x in s.split(";") if x.strip()]
    out: List[Name] = []
    for part in parts:
        toks = part.split()
        if len(toks) < 2:
            raise SystemExit(f"Bad player entry: {part!r}")
        out.append((toks[0], toks[1]))
    if len(out) < 1:
        raise SystemExit("Roster must contain at least 1 player")
    return out


def inning_mean(lineup: Sequence[BatterParams], cfg: SimConfig, games: int, seed: int) -> float:
    """Simulate games with inning-start reset to spot #1 each game; return mean runs/inning."""
    random.seed(seed)
    batter_i = 0
    total_runs = 0
    total_innings = games * cfg.innings

    def advance(bases, runs, hb):
        b1, b2, b3 = bases
        if hb == 4:
            return (0, 0, 0), runs + b1 + b2 + b3 + 1
        for _ in range(hb):
            runs += b3
            b3, b2, b1 = b2, b1, 0
        if hb == 1:
            b1 = 1
        elif hb == 2:
            b2 = 1
        elif hb == 3:
            b3 = 1
        return (b1, b2, b3), runs

    for _g in range(games):
        batter_i = 0
        for _inn in range(cfg.innings):
            outs = 0
            bases = (0, 0, 0)
            inn_runs = 0
            while outs < cfg.outs_per_inning and inn_runs < cfg.run_cap:
                b = lineup[batter_i]
                if random.random() < b.pK:
                    outs += 1
                else:
                    p_hit = b.avg / max(1e-9, (1 - b.pK))
                    p_hit = min(0.999, max(0.0, p_hit))
                    p_reach = p_hit + (1 - p_hit) * cfg.R
                    if random.random() >= p_reach:
                        outs += 1
                    else:
                        is_hit = random.random() < p_hit
                        if is_hit:
                            p1, p2, p3, p4 = b.hit_probs
                            u = random.random()
                            hb = 1 if u < p1 else 2 if u < p1 + p2 else 3 if u < p1 + p2 + p3 else 4
                        else:
                            hb = cfg.err_bases
                        bases, inn_runs = advance(bases, inn_runs, hb)
                batter_i = (batter_i + 1) % len(lineup)
            total_runs += min(inn_runs, cfg.run_cap)

    return total_runs / total_innings


def main() -> None:
    a = parse_args()

    stats = load_stats(Path(a.stats))
    season = stats["season"]
    two = stats["two_game"]
    merged = stats["combined"]

    params = build_params(
        merged,
        season=season,
        two_game=two,
        sofia_blend_w2=a.blend_sofia,
        flip_olivia_brinkley=a.flip_olivia_brinkley,
        shrink_k=a.shrink_k,
    )

    players = parse_list(a.players)

    cfg = SimConfig(R=a.R, err_bases=a.err_bases)

    rng = random.Random(a.seed)

    best_order: List[Name] = players[:]
    best_score = float("-inf")

    for _r in range(a.restarts):
        print(f"restart { _r+1 }/ {a.restarts} ...", flush=True)
        order = players[:]
        rng.shuffle(order)
        lineup = [params[n] for n in order]
        cur = inning_mean(lineup, cfg, games=a.games_eval, seed=a.seed)

        for _ in range(a.iters):
            i, j = rng.sample(range(len(order)), 2)
            cand = order[:]
            cand[i], cand[j] = cand[j], cand[i]
            cand_lineup = [params[n] for n in cand]
            sc = inning_mean(cand_lineup, cfg, games=a.games_eval, seed=a.seed)
            if sc > cur:
                order, cur = cand, sc

        if cur > best_score:
            best_order, best_score = order, cur

    final_lineup = [params[n] for n in best_order]
    final_score = inning_mean(final_lineup, cfg, games=a.games_final, seed=a.seed)

    print(f"best_estimated_runs_per_inning (eval): {best_score:.4f}")
    print(f"best_runs_per_inning (final): {final_score:.4f}")
    print("best_lineup:")
    for i, (first, last) in enumerate(best_order, 1):
        print(f"{i} {first} {last}")


if __name__ == "__main__":
    main()
