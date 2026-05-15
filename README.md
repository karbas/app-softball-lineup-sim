# SoftballSim

Local Monte Carlo lineup simulator for 8U coach-pitch softball.

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip

python scripts/run_lineup.py \
  --stats data/stats.json \
  --R 0.33 --err-bases 2 --games 200000 --seed 424242 --lambda 15 \
  --blend-sofia 0.6 --flip-olivia-brinkley \
  --lineup "Analeah Hernandez; Teliya Henderson; Isabel Hill; Brinkley Maldonado; Evalynn Jimenez; Zainy Aziz; Cara Cox; Sofia Jimenez; Paislee Buggs; Olivia Butcher"
```

## Stats JSON schema
```json
{
  "season": [
    {"first": "Analeah", "last": "Hernandez",
     "ab": 30, "h": 12, "1b": 8, "2b": 3, "3b": 1, "hr": 0, "so": 4}
  ],
  "two_game": [
    {"first": "Analeah", "last": "Hernandez",
     "ab": 4, "h": 2, "1b": 1, "2b": 1, "3b": 0, "hr": 0, "so": 0}
  ]
}
```
Each section is a list of per-player stat lines. Duplicate entries for the same `(first, last)` within a section are summed.

## Notes
- `R` is reach-on-contact (non-hit) rate (defense quality).
- `err-bases` models overthrows (1B vs 2B on errors).
