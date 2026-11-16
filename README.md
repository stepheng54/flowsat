# flowsat
SAT/SMT encodings for solving and generating Flow Free puzzles: lazy (DFJ-style) vs. eager (MTZ-style) subtour elimination, plus uniquely-solvable puzzle generation.

## Setup

```
pip install -e ".[dev]"
pytest
```

## Data

Puzzles live in `data/` as JSON (see `flowsat/puzzle.py` for the format). The repository ships
only hand-made and generated puzzles. Puzzles transcribed from the Flow Free app were used
locally for validation but are not distributed (`data/**/app_*.json` is gitignored). Tests that
use them are skipped when the files are absent.
