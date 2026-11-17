"""Independent solution checker. Shares no code with the encodings or the brute-force solver.

A coloring is valid iff every cell has a color, endpoints have their own color, each color's
endpoints have exactly one same-colored neighbor and every other cell exactly two, and each
color's cells are connected. In other words, each color induces a simple path.
"""

from __future__ import annotations

import operator
from collections import deque
from dataclasses import dataclass
from typing import Any, Iterator

from flowsat.puzzle import Puzzle


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reason: str = ""

    def __bool__(self) -> bool:
        return self.ok


_OK = ValidationResult(True)


def _fail(reason: str) -> ValidationResult:
    return ValidationResult(False, reason)


def validate(puzzle: Puzzle, coloring: Any) -> ValidationResult:
    rows, cols = puzzle.rows, puzzle.cols
    k = len(puzzle.endpoints)

    def label(color: int) -> str:
        return puzzle.labels[color]

    def adjacent(r: int, c: int) -> Iterator[tuple[int, int]]:
        if r > 0:
            yield (r - 1, c)
        if r < rows - 1:
            yield (r + 1, c)
        if c > 0:
            yield (r, c - 1)
        if c < cols - 1:
            yield (r, c + 1)

    # shape and values
    try:
        raw_rows = list(coloring)
    except TypeError:
        return _fail("coloring is not a sequence of rows")
    if len(raw_rows) != rows:
        return _fail(f"expected {rows} rows, got {len(raw_rows)}")
    grid: list[list[int]] = []
    for r, raw_row in enumerate(raw_rows):
        try:
            values = list(raw_row)
        except TypeError:
            return _fail(f"row {r} is not a sequence")
        if len(values) != cols:
            return _fail(f"row {r} has {len(values)} cells, expected {cols}")
        row: list[int] = []
        for c, value in enumerate(values):
            if isinstance(value, bool):
                return _fail(f"cell {(r, c)} holds a bool, not a color index")
            try:
                color = operator.index(value)
            except TypeError:
                return _fail(f"cell {(r, c)} holds {value!r}, not a color index")
            if not 0 <= color < k:
                return _fail(f"cell {(r, c)} is uncolored or has unknown color {color}")
            row.append(color)
        grid.append(row)

    endpoint_color: dict[tuple[int, int], int] = {}
    for color, pair in enumerate(puzzle.endpoints):
        for r, c in pair:
            endpoint_color[(r, c)] = color
            if grid[r][c] != color:
                return _fail(
                    f"endpoint {(r, c)} of color {label(color)} is colored {label(grid[r][c])}"
                )

    for r in range(rows):
        for c in range(cols):
            color = grid[r][c]
            same = sum(1 for nr, nc in adjacent(r, c) if grid[nr][nc] == color)
            expected = 1 if endpoint_color.get((r, c)) == color else 2
            if same != expected:
                kind = "endpoint" if expected == 1 else "cell"
                return _fail(
                    f"{kind} {(r, c)} of color {label(color)} has {same} same-colored "
                    f"neighbors, expected {expected}"
                )

    # with the degree checks passed, anything unreachable from an endpoint is a cycle
    for color, (start, _end) in enumerate(puzzle.endpoints):
        total = sum(row.count(color) for row in grid)
        seen = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in adjacent(r, c):
                if grid[nr][nc] == color and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    queue.append((nr, nc))
        if len(seen) != total:
            return _fail(
                f"color {label(color)}: {total - len(seen)} cells are not on the path between "
                f"its endpoints (stray cycle)"
            )

    return _OK
