"""Shared test instances.

STRAY puzzles have no valid solution but a locally consistent model (see report/notes.md).
App puzzles are gitignored and only used when present locally.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from flowsat.puzzle import Coloring, Puzzle, coloring_from_strings

DATA = Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class Example:
    name: str
    grid: tuple[str, ...]
    solution: tuple[str, ...] | None = None
    stray_model: tuple[str, ...] | None = None

    @property
    def puzzle(self) -> Puzzle:
        return Puzzle.from_strings(self.grid, name=self.name)

    def coloring(self, lines: tuple[str, ...] | None) -> Coloring:
        assert lines is not None
        return coloring_from_strings(self.puzzle, lines)


LANES_3X3 = Example(
    "lanes_3x3",
    ("A.A",
     "B.B",
     "C.C"),
    solution=("AAA",
              "BBB",
              "CCC"),
)

NESTED_L_3X4 = Example(
    "nested_l_3x4",
    ("...A",
     "...B",
     "ABCC"),
    solution=("AAAA",
              "ABBB",
              "ABCC"),
)

NESTED_L_4X5 = Example(
    "nested_l_4x5",
    ("....A",
     "....B",
     "....C",
     "ABCDD"),
    solution=("AAAAA",
              "ABBBB",
              "ABCCC",
              "ABCDD"),
)

FIVE_COLOR_5X5 = Example(
    "five_color_5x5",
    ("..BD.",
     "...A.",
     "B..C.",
     "A..E.",
     "C..ED"),
    solution=("BBBDD",
              "BAAAD",
              "BACCD",
              "AACED",
              "CCCED"),
)

BLOCKED_3X3 = Example(
    "blocked_3x3",
    ("A.B",
     "...",
     "A.B"),
)

STRAY_4X4 = Example(
    "stray_cycle_4x4",
    ("..BA",
     "....",
     "B...",
     "A..."),
    stray_model=("AABA",
                 "AABA",
                 "BBBA",
                 "AAAA"),
)

STRAY_5X5 = Example(
    "stray_cycle_5x5",
    ("..BC.",
     "...A.",
     "B....",
     ".....",
     "AC..."),
    stray_model=("AABCC",
                 "AABAC",
                 "BBBAC",
                 "AAAAC",
                 "ACCCC"),
)


def _load_app_examples() -> list[Example]:
    examples = []
    for path in sorted(DATA.rglob("app_*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if "grid" in raw and "solution" in raw:
            examples.append(Example(path.stem, tuple(raw["grid"]), solution=tuple(raw["solution"])))
    return examples


APP = _load_app_examples()
APP_SMALL = [e for e in APP if len(e.grid) * len(e.grid[0]) <= 25]
APP_LARGE = [e for e in APP if e not in APP_SMALL]

SOLVABLE = [LANES_3X3, NESTED_L_3X4, NESTED_L_4X5, FIVE_COLOR_5X5] + APP_SMALL
STRAY = [STRAY_4X4, STRAY_5X5]
TINY = [LANES_3X3, NESTED_L_3X4, BLOCKED_3X3, STRAY_4X4]
ALL = SOLVABLE + [BLOCKED_3X3] + STRAY
