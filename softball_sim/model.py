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
) -> Dict[Tuple[str, str], BatterParams]:
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
