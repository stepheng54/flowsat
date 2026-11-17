"""Backtracking solver for tiny grids (<= 25 cells), used to cross-check the encodings.

Grows each color's path from its first endpoint. A new cell may only touch the current head and
the far endpoint, so every path is induced. Prunes when an endpoint can no longer be reached or
an empty region can never be filled.
"""

from __future__ import annotations

from itertools import islice
from typing import Iterator

from flowsat.puzzle import Coloring, Puzzle

MAX_CELLS = 25
_EMPTY = -1


def iter_solutions(puzzle: Puzzle, max_cells: int = MAX_CELLS) -> Iterator[Coloring]:
    if puzzle.num_cells > max_cells:
        raise ValueError(
            f"brute force is limited to {max_cells} cells; got {puzzle.rows}x{puzzle.cols}"
        )
    return _Search(puzzle).run()


def solve_all(puzzle: Puzzle, limit: int | None = None) -> list[Coloring]:
    return list(islice(iter_solutions(puzzle), limit))


def solve(puzzle: Puzzle) -> Coloring | None:
    return next(iter_solutions(puzzle), None)


def count_solutions(puzzle: Puzzle, limit: int | None = None) -> int:
    return sum(1 for _ in islice(iter_solutions(puzzle), limit))


class _Search:
    def __init__(self, puzzle: Puzzle) -> None:
        self.rows = rows = puzzle.rows
        self.cols = cols = puzzle.cols
        self.k = puzzle.num_colors
        self.n = rows * cols

        nbrs: list[tuple[int, ...]] = []
        for r in range(rows):
            for c in range(cols):
                out: list[int] = []
                if r > 0:
                    out.append((r - 1) * cols + c)
                if r < rows - 1:
                    out.append((r + 1) * cols + c)
                if c > 0:
                    out.append(r * cols + c - 1)
                if c < cols - 1:
                    out.append(r * cols + c + 1)
                nbrs.append(tuple(out))
        self.nbrs = nbrs

        self.starts = [a[0] * cols + a[1] for a, _ in puzzle.endpoints]
        self.ends = [b[0] * cols + b[1] for _, b in puzzle.endpoints]
        self.grid = [_EMPTY] * self.n
        for color in range(self.k):
            self.grid[self.starts[color]] = color
            self.grid[self.ends[color]] = color

    def run(self) -> Iterator[Coloring]:
        yield from self._begin(0)

    def _snapshot(self) -> Coloring:
        g, cols = self.grid, self.cols
        return [[g[r * cols + c] for c in range(cols)] for r in range(self.rows)]

    def _reaches(self, src: int, dst: int) -> bool:
        grid, nbrs = self.grid, self.nbrs
        seen = {src}
        stack = [src]
        while stack:
            v = stack.pop()
            for w in nbrs[v]:
                if w == dst:
                    return True
                if grid[w] == _EMPTY and w not in seen:
                    seen.add(w)
                    stack.append(w)
        return False

    def _feasible(self, color: int, head: int) -> bool:
        if not self._reaches(head, self.ends[color]):
            return False
        for d in range(color + 1, self.k):
            if not self._reaches(self.starts[d], self.ends[d]):
                return False
        # every empty region must touch a path that can still grow into it
        frontier = {head, *(self.starts[d] for d in range(color + 1, self.k))}
        grid, nbrs = self.grid, self.nbrs
        seen: set[int] = set()
        for v in range(self.n):
            if grid[v] != _EMPTY or v in seen:
                continue
            touched = False
            seen.add(v)
            stack = [v]
            while stack:
                u = stack.pop()
                for w in nbrs[u]:
                    if w in frontier:
                        touched = True
                    elif grid[w] == _EMPTY and w not in seen:
                        seen.add(w)
                        stack.append(w)
            if not touched:
                return False
        return True

    def _begin(self, color: int) -> Iterator[Coloring]:
        if color == self.k:
            if _EMPTY not in self.grid:
                yield self._snapshot()
            return
        start = self.starts[color]
        if self._feasible(color, start):
            yield from self._extend(color, start)

    def _extend(self, color: int, head: int) -> Iterator[Coloring]:
        end = self.ends[color]
        grid, nbrs = self.grid, self.nbrs
        if end in nbrs[head]:
            yield from self._begin(color + 1)
            return
        for u in nbrs[head]:
            if grid[u] != _EMPTY:
                continue
            if any(w != head and w != end and grid[w] == color for w in nbrs[u]):
                continue
            grid[u] = color
            if self._feasible(color, u):
                yield from self._extend(color, u)
            grid[u] = _EMPTY
