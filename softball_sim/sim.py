from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from .model import BatterParams


@dataclass(frozen=True)
class SimConfig:
    outs_per_inning: int = 3
    run_cap: int = 5
    innings: int = 5
    R: float = 0.33
    err_bases: int = 2


def _advance(bases: Tuple[int, int, int], runs: int, hb: int) -> Tuple[Tuple[int, int, int], int]:
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


def _plate_appearance(b: BatterParams, cfg: SimConfig, bases: Tuple[int, int, int], runs: int) -> Tuple[Tuple[int, int, int], int, bool]:
    # strikeout?
    if random.random() < b.pK:
        return bases, runs, True

    # contact
    p_hit = b.avg / max(1e-9, (1 - b.pK))
    p_hit = min(0.999, max(0.0, p_hit))
    p_reach = p_hit + (1 - p_hit) * cfg.R

    if random.random() >= p_reach:
        return bases, runs, True

    # reached: decide hit vs error
    is_hit = random.random() < p_hit
    if is_hit:
        p1, p2, p3, p4 = b.hit_probs
        u = random.random()
        hb = 1 if u < p1 else 2 if u < p1 + p2 else 3 if u < p1 + p2 + p3 else 4
    else:
        hb = cfg.err_bases

    bases, runs = _advance(bases, runs, hb)
    return bases, runs, False


def simulate_games(
    lineup: Sequence[BatterParams],
    cfg: SimConfig,
    games: int,
    seed: int,
) -> List[int]:
    """Return total runs per game (length=games)."""
    random.seed(seed)
    batter_i = 0
    totals: List[int] = []

    for _ in range(games):
        game_runs = 0
        for _inn in range(cfg.innings):
            outs = 0
            bases = (0, 0, 0)
            inn_runs = 0
            while outs < cfg.outs_per_inning and inn_runs < cfg.run_cap:
                bases, inn_runs, is_out = _plate_appearance(lineup[batter_i], cfg, bases, inn_runs)
                if is_out:
                    outs += 1
                batter_i = (batter_i + 1) % len(lineup)
            game_runs += min(inn_runs, cfg.run_cap)
        totals.append(game_runs)

    return totals


def inning_start_distribution(
    lineup: Sequence[BatterParams],
    cfg: SimConfig,
    games: int,
    seed: int,
) -> List[float]:
    """Percent of innings that start at each lineup index."""
    random.seed(seed)
    batter_i = 0
    starts = [0] * len(lineup)

    for _ in range(games):
        for _inn in range(cfg.innings):
            starts[batter_i] += 1
            outs = 0
            bases = (0, 0, 0)
            inn_runs = 0
            while outs < cfg.outs_per_inning and inn_runs < cfg.run_cap:
                bases, inn_runs, is_out = _plate_appearance(lineup[batter_i], cfg, bases, inn_runs)
                if is_out:
                    outs += 1
                batter_i = (batter_i + 1) % len(lineup)

    total = sum(starts)
    return [s / total for s in starts]
