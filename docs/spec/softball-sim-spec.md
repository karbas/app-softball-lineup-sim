# Softball Lineup Simulator (8U Coach Pitch) — CLI Spec

## Goal
A local CLI tool that compares batting orders for **expected runs/inning** and related metrics under youth softball rules (coach pitch).

## Core Concepts / Inputs
### Team
- `players.json` (or CSV) with one row per player:
  - `name` (string)
  - `avg` (float) — interpreted as **hits / AB**
  - `ops` (float) — used as a proxy for extra-base distribution
  - `k` (int) — strikeouts
  - `ab` (int) — at-bats (for K rate)

### Lineups
- A lineup is an ordered list of player names.
- Default lineup length: **10**.

### Game rules
Configurable flags:
- `outs_per_inning` (default `3`)
- `run_cap` (default `5`)
- `continuous_order` (default `true`)
- `carryover_batter` between innings (default `true`)

### 8U-specific reach model
Because ball-in-play outs often become safe on errors:
- `R` = probability of **reaching base on a ball in play that is not a hit** (default TBD; example used: `0.66`).

## Plate Appearance Model
For batter with `(avg, ops, k, ab)`:
1. Compute `pK = k/ab` (clamped).
2. If strikeout: out.
3. Else contact:
   - Let `p_hit_given_contact = avg / (1 - pK)` (clamped).
   - Reach base with probability:
     - `p_reach = p_hit_given_contact + (1 - p_hit_given_contact) * R`
   - If reach via **hit** (with prob `p_hit_given_contact`): sample bases using OPS-derived mapping (below).
   - If reach via **error**: treat as **single**.

### OPS → extra-base mapping
Assume `OBP ≈ AVG` and `SLG ≈ OPS - AVG`.
Let mean bases per hit `m = SLG/AVG` (clamp to `[1,4]`).
Convert `m` to a simple discrete distribution by shifting mass from 1B→2B→3B→HR until mean matches `m`.

## Base Running / Scoring
- Bases advance by the number of bases on the hit.
- HR clears bases.
- Inning ends at `outs_per_inning` outs or `run_cap` runs.

## Simulation
Monte Carlo, default:
- `N = 200_000` simulated innings per **starting spot**.

For each starting lineup position `s` (1..L):
- Simulate an inning beginning with batter `s`.

## Metrics (Outputs)
For a given lineup:
- `runs_by_start_spot[s]` (mean runs, capped)
- `avg_runs` = mean of `runs_by_start_spot`
- `p_cap` = P(runs == run_cap)
- `p_bad` = P(runs <= 1)

## CLI Interface
Binary name: `softball-sim` (Python recommended: `python -m softball_sim ...`).

### Commands
1) `softball-sim run --players players.json --lineup lineup.json --R 0.66 [--N 200000]`
- Prints: runs by start spot + `avg_runs`, `p_cap`, `p_bad`.

2) `softball-sim compare --players players.json --lineups lineups.json --metric avg_runs|p_cap|p_bad`
- Prints sorted comparison.

3) `softball-sim optimize --players players.json --metric p_cap --R 0.66`
- Heuristic search (swap / hill-climb) to maximize metric; outputs best lineup found.

## Validation / Guardrails
- Error if lineup contains unknown names or duplicates.
- Warn if `ab` too small (unstable K rates).
- Deterministic with `--seed`.

## Deliverables
- `softball_sim/` Python package
- `softball-sim` entrypoint
- Example `players.json`, `lineups.json`
- README with examples and explanation of assumptions
