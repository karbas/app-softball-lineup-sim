# Session notes (2026-02-27) — SoftballSim

## What we built
A Monte Carlo simulator for 8U coach-pitch softball to compare 10-batter lineup orders under:
- 3 outs/inning
- 5-run cap/inning
- continuous batting order; next inning starts where you left off

## Models discussed
### 1) Simple model (early)
- OBP ≈ AVG
- hits treated as singles; later added extra-base approximation via OPS

### 2) Ks + reach-on-contact model (later, more realistic)
- Strikeout probability: `pK = SO/AB`
- If not K: ball in play
  - Convert AVG to hit-on-contact rate: `p_hit_contact = AVG / (1 - pK)` (clamped)
  - Reach base (hit or error): `p_reach = p_hit_contact + (1 - p_hit_contact) * R`
- When reaching on **error**, sometimes modeled as 1B; later switched to **2B** (overthrow to 2nd)
- Hit-type distribution taken from statlines (1B/2B/3B/HR counts)

## Key knobs
- `R`: reach-on-ball-in-play-but-not-a-hit (proxy for opponent defense)
  - Brendan heuristic: ~0.35 for good defense, ~0.60 for bad defense
- `ERR_BASES`: bases awarded on error reach (1 or 2)

## Derived metrics we compared
- Expected runs per inning (averaged over all 10 possible inning start spots)
- Expected runs per 5-inning game
- Ceiling/floor probabilities:
  - P(game runs >= 20)
  - P(game runs >= 17)
  - P(game runs < 10)
- Composite score: `E[runs] - λ * P(<10)` (example λ=15)

## CSV parsing note
The season CSV export contains duplicate column headers (e.g., `H`, `SO`, etc. for pitching vs batting).
Parsing must select the **batting** columns (first occurrence) by index.

## Lineup labels used
- "Alpha" (old omega order):
  1 Analeah Hernandez
  2 Teliya Henderson
  3 Isabel Hill
  4 Brinkley Maldonado
  5 Evalynn Jimenez
  6 Zainy Aziz
  7 Cara Cox
  8 Sofia Jimenez
  9 Paislee Buggs
  10 Olivia Butcher

- "Omega" (old "worst" order):
  1 Brinkley Maldonado
  2 Cara Cox
  3 Paislee Buggs
  4 Zainy Aziz
  5 Sofia Jimenez
  6 Analeah Hernandez
  7 Teliya Henderson
  8 Isabel Hill
  9 Olivia Butcher
  10 Evalynn Jimenez
