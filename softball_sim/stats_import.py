from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class BatLine:
    first: str
    last: str
    ab: int
    h: int
    b1: int
    b2: int
    b3: int
    hr: int
    so: int

    @property
    def key(self) -> Tuple[str, str]:
        return (self.first, self.last)


def _to_int(x) -> int:
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0


def _line_from_dict(d: dict) -> BatLine:
    return BatLine(
        first=str(d.get("first", "")).strip(),
        last=str(d.get("last", "")).strip(),
        ab=_to_int(d.get("ab", 0)),
        h=_to_int(d.get("h", 0)),
        b1=_to_int(d.get("1b", 0)),
        b2=_to_int(d.get("2b", 0)),
        b3=_to_int(d.get("3b", 0)),
        hr=_to_int(d.get("hr", 0)),
        so=_to_int(d.get("so", 0)),
    )


def _merge_lines(lines: Iterable[BatLine]) -> Dict[Tuple[str, str], BatLine]:
    agg: Dict[Tuple[str, str], List[int]] = {}
    for ln in lines:
        k = ln.key
        if k not in agg:
            agg[k] = [0, 0, 0, 0, 0, 0, 0]
        a = agg[k]
        a[0] += ln.ab
        a[1] += ln.h
        a[2] += ln.b1
        a[3] += ln.b2
        a[4] += ln.b3
        a[5] += ln.hr
        a[6] += ln.so
    return {(f, l): BatLine(f, l, *a) for (f, l), a in agg.items()}


def load_stats(path: str | Path) -> Dict[str, Dict[Tuple[str, str], BatLine]]:
    """Load a stats JSON file and return per-player BatLines keyed by section.

    Schema:
        {
          "season":   [ {"first": "...", "last": "...", "ab": N, "h": N,
                         "1b": N, "2b": N, "3b": N, "hr": N, "so": N }, ... ],
          "two_game": [ ... same shape ... ]
        }

    Returns a dict with three sections:
        season   - merged season stats keyed by (first, last)
        two_game - merged 2-game stats keyed by (first, last)
        combined - season + two_game summed
    """
    raw = json.loads(Path(path).read_text())
    season = _merge_lines(_line_from_dict(d) for d in raw.get("season", []))
    two_game = _merge_lines(_line_from_dict(d) for d in raw.get("two_game", []))
    combined = _merge_lines(list(season.values()) + list(two_game.values()))
    return {"season": season, "two_game": two_game, "combined": combined}
