from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .stats_import import BatLine


@dataclass(frozen=True)
class BatterParams:
    avg: float
    pK: float
    hit_probs: Tuple[float, float, float, float]  # 1B,2B,3B,HR given a hit


def _hit_probs_from_counts(line: BatLine) -> Tuple[float, float, float, float]:
    b1 = line.b1 if line.b1 > 0 else max(0, line.h - line.b2 - line.b3 - line.hr)
    b2, b3, hr = line.b2, line.b3, line.hr
    tot = b1 + b2 + b3 + hr
    if tot <= 0:
        return (1.0, 0.0, 0.0, 0.0)
    return (b1 / tot, b2 / tot, b3 / tot, hr / tot)


def params_from_batline(line: BatLine) -> BatterParams:
    ab = line.ab
    avg = (line.h / ab) if ab else 0.0
    pK = (line.so / ab) if ab else 0.0
    return BatterParams(avg=avg, pK=pK, hit_probs=_hit_probs_from_counts(line))


def _team_rates(
    merged: Dict[Tuple[str, str], BatLine],
) -> Tuple[float, float, Tuple[float, float, float, float]]:
    """Aggregate team-wide AVG, pK, and hit-type distribution."""
    ab = h = so = b1 = b2 = b3 = hr = 0
    for ln in merged.values():
        ab += ln.ab
        h += ln.h
        so += ln.so
        b1 += ln.b1 if ln.b1 > 0 else max(0, ln.h - ln.b2 - ln.b3 - ln.hr)
        b2 += ln.b2
        b3 += ln.b3
        hr += ln.hr
    if ab == 0:
        return 0.0, 0.0, (1.0, 0.0, 0.0, 0.0)
    avg = h / ab
    pK = so / ab
    tot = b1 + b2 + b3 + hr
    hp = (b1 / tot, b2 / tot, b3 / tot, hr / tot) if tot else (1.0, 0.0, 0.0, 0.0)
    return avg, pK, hp


def _shrunk_params(
    line: BatLine,
    team_avg: float,
    team_pK: float,
    team_hp: Tuple[float, float, float, float],
    k: float,
) -> BatterParams:
    """Pseudo-AB shrinkage: blend a player's rates with team-average rates,
    weighted as if the team prior contributed `k` extra at-bats."""
    eff = line.ab + k
    if eff <= 0:
        return BatterParams(0.0, 0.0, (1.0, 0.0, 0.0, 0.0))
    avg = (line.h + k * team_avg) / eff
    pK = (line.so + k * team_pK) / eff

    own_hp = _hit_probs_from_counts(line)
    own_hits = line.h
    pseudo_hits = k * team_avg
    tot = own_hits + pseudo_hits
    if tot <= 0:
        hp = team_hp
    else:
        hp = tuple(
            (own_hits * own_hp[i] + pseudo_hits * team_hp[i]) / tot for i in range(4)
        )
    return BatterParams(avg=avg, pK=pK, hit_probs=hp)  # type: ignore


def blend_params(p2: BatterParams, p_season: BatterParams, w2: float) -> BatterParams:
    # Blend rates and hit-type distribution.
    avg = w2 * p2.avg + (1 - w2) * p_season.avg
    pK = w2 * p2.pK + (1 - w2) * p_season.pK
    hp = tuple(w2 * p2.hit_probs[i] + (1 - w2) * p_season.hit_probs[i] for i in range(4))
    s = sum(hp)
    hp = tuple(x / s for x in hp) if s else (1.0, 0.0, 0.0, 0.0)
    return BatterParams(avg=avg, pK=pK, hit_probs=hp)  # type: ignore


def build_params(
    merged: Dict[Tuple[str, str], BatLine],
    season: Dict[Tuple[str, str], BatLine] | None = None,
    two_game: Dict[Tuple[str, str], BatLine] | None = None,
    sofia_blend_w2: float | None = None,
    flip_olivia_brinkley: bool = False,
    shrink_k: float = 0.0,
) -> Dict[Tuple[str, str], BatterParams]:
    if shrink_k > 0:
        team_avg, team_pK, team_hp = _team_rates(merged)
        params = {
            key: _shrunk_params(line, team_avg, team_pK, team_hp, shrink_k)
            for key, line in merged.items()
        }
    else:
        params = {k: params_from_batline(v) for k, v in merged.items()}

    if sofia_blend_w2 is not None:
        if season is None or two_game is None:
            raise ValueError("Need season and two_game maps to blend Sofia")
        key = ("Sofia", "Jimenez")
        if key in season and key in two_game:
            params[key] = blend_params(
                params_from_batline(two_game[key]),
                params_from_batline(season[key]),
                sofia_blend_w2,
            )

    if flip_olivia_brinkley:
        ol = ("Olivia", "Butcher")
        br = ("Brinkley", "Maldonado")
        if ol in params and br in params:
            params[ol], params[br] = params[br], params[ol]

    return params
