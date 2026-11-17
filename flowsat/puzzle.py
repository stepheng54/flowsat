"""Puzzle representation and string/JSON I/O.

Cells are (row, col). Colors are ints 0..k-1, and a coloring is a rows x cols list of lists.
JSON files either give rows/cols/endpoints or a compact "grid" of strings (see from_strings).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Iterator, Sequence

Cell = tuple[int, int]
Coloring = list[list[int]]

UNCOLORED = -1
EMPTY_CHAR = "."


def _as_cell(value: Any) -> Cell:
    r, c = value
    return (int(r), int(c))


@dataclass(frozen=True)
class Puzzle:
    rows: int
    cols: int
    endpoints: tuple[tuple[Cell, Cell], ...]
    labels: tuple[str, ...]
    name: str = ""

    def __post_init__(self) -> None:
        normalized: list[tuple[Cell, Cell]] = []
        for pair in self.endpoints:
            pair = tuple(pair)
            if len(pair) != 2:
                raise ValueError("each color needs exactly two endpoints")
            normalized.append((_as_cell(pair[0]), _as_cell(pair[1])))
        object.__setattr__(self, "endpoints", tuple(normalized))
        object.__setattr__(self, "labels", tuple(str(label) for label in self.labels))

        if self.rows < 1 or self.cols < 1:
            raise ValueError(f"grid must be at least 1x1, got {self.rows}x{self.cols}")
        if not self.endpoints:
            raise ValueError("a puzzle needs at least one color")
        if len(self.labels) != len(self.endpoints):
            raise ValueError("need exactly one label per color")
        if len(set(self.labels)) != len(self.labels):
            raise ValueError("color labels must be distinct")
        seen: set[Cell] = set()
        for label, pair in zip(self.labels, self.endpoints):
            for cell in pair:
                if not self.in_bounds(cell):
                    raise ValueError(
                        f"endpoint {cell} of color {label} is outside the "
                        f"{self.rows}x{self.cols} grid"
                    )
                if cell in seen:
                    raise ValueError(f"cell {cell} is used as an endpoint more than once")
                seen.add(cell)

    @property
    def num_colors(self) -> int:
        return len(self.endpoints)

    @property
    def num_cells(self) -> int:
        return self.rows * self.cols

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def cells(self) -> Iterator[Cell]:
        for r in range(self.rows):
            for c in range(self.cols):
                yield (r, c)

    def neighbors(self, cell: Cell) -> list[Cell]:
        r, c = cell
        candidates = ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        return [n for n in candidates if self.in_bounds(n)]

    @cached_property
    def endpoint_owner(self) -> dict[Cell, int]:
        return {cell: color for color, pair in enumerate(self.endpoints) for cell in pair}

    @classmethod
    def from_strings(cls, lines: Sequence[str], name: str = "") -> Puzzle:
        """Parse rows like "A..B"; "." is empty, every label must appear exactly twice."""
        lines = [line.strip() for line in lines]
        if not lines or not lines[0]:
            raise ValueError("puzzle must have at least one non-empty row")
        if any(len(line) != len(lines[0]) for line in lines):
            raise ValueError("all rows must have the same length")
        found: dict[str, list[Cell]] = {}
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == EMPTY_CHAR:
                    continue
                if ch.isspace():
                    raise ValueError(f"whitespace inside row {r}")
                found.setdefault(ch, []).append((r, c))
        for label, cells in found.items():
            if len(cells) != 2:
                raise ValueError(f"color {label!r} appears {len(cells)} times; expected 2")
        return cls(
            rows=len(lines),
            cols=len(lines[0]),
            endpoints=tuple((cells[0], cells[1]) for cells in found.values()),
            labels=tuple(found),
            name=name,
        )

    def to_strings(self) -> list[str]:
        grid = [[EMPTY_CHAR] * self.cols for _ in range(self.rows)]
        for label, pair in zip(self.labels, self.endpoints):
            for r, c in pair:
                grid[r][c] = label[0]
        return ["".join(row) for row in grid]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rows": self.rows,
            "cols": self.cols,
            "endpoints": {
                label: [list(a), list(b)] for label, (a, b) in zip(self.labels, self.endpoints)
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Puzzle:
        if "endpoints" not in data and "grid" in data:
            return cls.from_strings(data["grid"], name=str(data.get("name", "")))
        eps = data["endpoints"]
        labels = tuple(eps)
        return cls(
            rows=int(data["rows"]),
            cols=int(data["cols"]),
            endpoints=tuple(tuple(eps[label]) for label in labels),
            labels=labels,
            name=str(data.get("name", "")),
        )


def _require_single_char_labels(puzzle: Puzzle) -> None:
    if any(len(label) != 1 for label in puzzle.labels):
        raise ValueError("string colorings need single-character color labels")


def coloring_from_strings(puzzle: Puzzle, lines: Sequence[str]) -> Coloring:
    _require_single_char_labels(puzzle)
    index = {label: i for i, label in enumerate(puzzle.labels)}
    if len(lines) != puzzle.rows:
        raise ValueError(f"expected {puzzle.rows} rows, got {len(lines)}")
    coloring: Coloring = []
    for r, line in enumerate(lines):
        if len(line) != puzzle.cols:
            raise ValueError(f"row {r} has length {len(line)}, expected {puzzle.cols}")
        row: list[int] = []
        for ch in line:
            if ch == EMPTY_CHAR:
                row.append(UNCOLORED)
            elif ch in index:
                row.append(index[ch])
            else:
                raise ValueError(f"unknown color label {ch!r}")
        coloring.append(row)
    return coloring


def coloring_to_strings(puzzle: Puzzle, coloring: Coloring) -> list[str]:
    _require_single_char_labels(puzzle)
    k = puzzle.num_colors
    return [
        "".join(
            EMPTY_CHAR if v == UNCOLORED else (puzzle.labels[v] if 0 <= v < k else "?")
            for v in row
        )
        for row in coloring
    ]


def format_coloring(puzzle: Puzzle, coloring: Coloring) -> str:
    return "\n".join(coloring_to_strings(puzzle, coloring))


def load_puzzle(path: str | Path) -> tuple[Puzzle, Coloring | None]:
    """Returns the puzzle and its stored solution, if any."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("name", path.stem)
    puzzle = Puzzle.from_dict(data)
    solution = data.get("solution")
    return puzzle, (coloring_from_strings(puzzle, solution) if solution else None)


def save_puzzle(path: str | Path, puzzle: Puzzle, solution: Coloring | None = None) -> None:
    data = puzzle.to_dict()
    if solution is not None:
        data["solution"] = coloring_to_strings(puzzle, solution)
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
