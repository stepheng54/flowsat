"""Baseline local encoding.

x[r][c][k] means cell (r, c) has color k. Each cell has exactly one color, endpoints are fixed,
and x[v][k] implies exactly d same-colored neighbors (d = 1 at k's endpoints, 2 elsewhere).
Models can still contain stray cycles disjoint from the real path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection

from flowsat.encodings.cnf import CNF, add_exactly_one, add_guarded_exactly
from flowsat.puzzle import Cell, Coloring, Puzzle


@dataclass
class LocalEncoding:
    puzzle: Puzzle
    cnf: CNF
    x: list[list[list[int]]]

    @property
    def num_color_vars(self) -> int:
        p = self.puzzle
        return p.rows * p.cols * p.num_colors

    def var(self, cell: Cell, color: int) -> int:
        r, c = cell
        return self.x[r][c][color]

    def decode(self, true_vars: Collection[int]) -> Coloring:
        true_set = true_vars if isinstance(true_vars, (set, frozenset)) else set(true_vars)
        coloring: Coloring = []
        for r, row_vars in enumerate(self.x):
            row: list[int] = []
            for c, cell_vars in enumerate(row_vars):
                chosen = [color for color, v in enumerate(cell_vars) if v in true_set]
                if len(chosen) != 1:
                    raise ValueError(f"cell {(r, c)} has {len(chosen)} colors in the model")
                row.append(chosen[0])
            coloring.append(row)
        return coloring

    # true vars for a coloring, only valid without auxiliary vars
    def assignment(self, coloring: Coloring) -> set[int]:
        if self.cnf.num_vars != self.num_color_vars:
            raise ValueError("encoding has auxiliary variables; a coloring is not a full model")
        k = self.puzzle.num_colors
        true_vars: set[int] = set()
        for r, row in enumerate(coloring):
            for c, color in enumerate(row):
                if not 0 <= color < k:
                    raise ValueError(f"cell {(r, c)} has invalid color {color}")
                true_vars.add(self.x[r][c][color])
        return true_vars

    def satisfied_by(self, coloring: Coloring) -> bool:
        return self.cnf.is_satisfied_by(self.assignment(coloring))

    def blocking_clause(self, coloring: Coloring) -> list[int]:
        owner = self.puzzle.endpoint_owner
        return [
            -self.x[r][c][color]
            for r, row in enumerate(coloring)
            for c, color in enumerate(row)
            if (r, c) not in owner
        ]


def encode_local(puzzle: Puzzle) -> LocalEncoding:
    cnf = CNF()
    k = puzzle.num_colors
    # allocate color vars first so they are exactly 1..rows*cols*k
    x = [[cnf.new_vars(k) for _ in range(puzzle.cols)] for _ in range(puzzle.rows)]
    owner = puzzle.endpoint_owner

    for r, c in puzzle.cells():
        add_exactly_one(cnf, x[r][c])
        if (r, c) in owner:
            cnf.add_clause([x[r][c][owner[(r, c)]]])

    for cell in puzzle.cells():
        r, c = cell
        nbrs = puzzle.neighbors(cell)
        fixed = owner.get(cell)
        for color in range(k):
            if fixed is not None and fixed != color:
                continue
            d = 1 if fixed == color else 2
            add_guarded_exactly(cnf, x[r][c][color], [x[nr][nc][color] for nr, nc in nbrs], d)

    return LocalEncoding(puzzle=puzzle, cnf=cnf, x=x)
