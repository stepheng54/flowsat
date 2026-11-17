from itertools import product

import pytest

from flowsat.bruteforce import iter_solutions, solve, solve_all
from flowsat.puzzle import Puzzle
from flowsat.validate import validate
from tests.instances import ALL, APP_SMALL, SOLVABLE, STRAY, TINY


@pytest.mark.parametrize("ex", APP_SMALL, ids=lambda e: e.name)
def test_real_app_puzzle_has_unique_solution(ex):
    assert solve_all(ex.puzzle) == [ex.coloring(ex.solution)]


def _exhaustive(puzzle: Puzzle) -> list[list[list[int]]]:
    owner = puzzle.endpoint_owner
    free = [cell for cell in puzzle.cells() if cell not in owner]
    found = []
    for values in product(range(puzzle.num_colors), repeat=len(free)):
        grid = [[-1] * puzzle.cols for _ in range(puzzle.rows)]
        for (r, c), color in owner.items():
            grid[r][c] = color
        for (r, c), color in zip(free, values):
            grid[r][c] = color
        if validate(puzzle, grid):
            found.append(grid)
    return sorted(found)


@pytest.mark.parametrize("ex", TINY, ids=lambda e: e.name)
def test_matches_exhaustive_search(ex):
    assert sorted(solve_all(ex.puzzle)) == _exhaustive(ex.puzzle)


@pytest.mark.parametrize("ex", ALL, ids=lambda e: e.name)
def test_every_solution_is_valid_and_distinct(ex):
    solutions = solve_all(ex.puzzle)
    for s in solutions:
        result = validate(ex.puzzle, s)
        assert result, result.reason
    assert len({str(s) for s in solutions}) == len(solutions)


@pytest.mark.parametrize("ex", SOLVABLE, ids=lambda e: e.name)
def test_finds_known_solution(ex):
    assert ex.coloring(ex.solution) in solve_all(ex.puzzle)


@pytest.mark.parametrize("ex", STRAY, ids=lambda e: e.name)
def test_stray_instances_are_unsolvable(ex):
    assert solve(ex.puzzle) is None


def test_refuses_large_grids():
    p = Puzzle.from_strings(["A....", "A....", ".....", ".....", ".....", "....."])
    with pytest.raises(ValueError):
        iter_solutions(p)
