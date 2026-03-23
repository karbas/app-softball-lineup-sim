from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

BAT_FIELDS = ["AB", "H", "1B", "2B", "3B", "HR", "SO"]
ID_FIELDS = ["First", "Last"]


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


def _to_int(x: str) -> int:
    try:
        return int(float(x))
    except Exception:
        return 0


def _header_indices(path: Path) -> Dict[str, int]:
    """Return indices for the *first* occurrence of batting columns.

    Season exports often contain duplicate column names (batting + pitching).
    We intentionally take the first occurrence for batting.
    """
    with path.open(newline="") as f:
        r = csv.reader(f)
        header = None
        for row in r:
            if row and row[0].strip() == "Number":
                header = [c.strip() for c in row]
                break
        if header is None:
            raise ValueError(f"No header row starting with 'Number' found in {path}")

    def first_idx(name: str) -> int:
        return header.index(name)

    needed = ID_FIELDS + BAT_FIELDS
    return {k: first_idx(k) for k in needed}


def load_batting_csv(path: str | Path) -> List[BatLine]:
    path = Path(path)
    idx = _header_indices(path)

    out: List[BatLine] = []
    with path.open(newline="") as f:
        r = csv.reader(f)
        seen_header = False
        for row in r:
            if not row:
                continue
            if row[0].strip() == "Number":
                seen_header = True
                continue
            if not seen_header:
                continue
            if not row[0].strip().isdigit():
                continue

            first = row[idx["First"]].strip()
            last = row[idx["Last"]].strip()
            ab = _to_int(row[idx["AB"]])
            h = _to_int(row[idx["H"]])
            b1 = _to_int(row[idx["1B"]])
            b2 = _to_int(row[idx["2B"]])
            b3 = _to_int(row[idx["3B"]])
            hr = _to_int(row[idx["HR"]])
            so = _to_int(row[idx["SO"]])

            out.append(BatLine(first, last, ab, h, b1, b2, b3, hr, so))

    return out


def merge_lines(lines: Iterable[BatLine]) -> Dict[Tuple[str, str], BatLine]:
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

    merged: Dict[Tuple[str, str], BatLine] = {}
    for (first, last), a in agg.items():
        merged[(first, last)] = BatLine(first, last, *a)
    return merged
