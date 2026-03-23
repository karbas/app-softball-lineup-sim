# SoftballSim

Local Monte Carlo lineup simulator for 8U coach-pitch softball.

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip

python scripts/run_lineup.py \
  --season data/raw/season-export.csv \
  --two data/raw/two-game-export.csv \
  --R 0.33 --err-bases 2 --games 200000 --seed 424242 --lambda 15 \
  --blend-sofia 0.6 --flip-olivia-brinkley \
  --lineup "Analeah Hernandez; Teliya Henderson; Isabel Hill; Brinkley Maldonado; Evalynn Jimenez; Zainy Aziz; Cara Cox; Sofia Jimenez; Paislee Buggs; Olivia Butcher"
```

## Notes
- CSV exports may contain duplicate column names (batting + pitching). Importer takes the **first** batting columns.
- `R` is reach-on-contact (non-hit) rate (defense quality).
- `err-bases` models overthrows (1B vs 2B on errors).
