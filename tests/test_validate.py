import pytest

from flowsat.puzzle import Puzzle, coloring_from_strings
from flowsat.validate import validate
from tests.instances import APP_LARGE, LANES_3X3, SOLVABLE, STRAY


@pytest.mark.parametrize("ex", SOLVABLE + APP_LARGE, ids=lambda e: e.name)
def test_accepts_known_solutions(ex):
    result = validate(ex.puzzle, ex.coloring(ex.solution))
    assert result.ok, result.reason
    assert result


@pytest.mark.parametrize("ex", STRAY, ids=lambda e: e.name)
def test_rejects_stray_cycle(ex):
    result = validate(ex.puzzle, ex.coloring(ex.stray_model))
    assert not result
    assert "stray cycle" in result.reason


def _lanes():
    return LANES_3X3.puzzle, [list(row) for row in LANES_3X3.coloring(LANES_3X3.solution)]


def test_rejects_wrong_shape():
    p, good = _lanes()
    assert "rows" in validate(p, good[:2]).reason
    assert "cells" in validate(p, [good[0], good[1], good[2][:2]]).reason
    assert not validate(p, 5)
    assert not validate(p, [1, 2, 3])


def test_rejects_bad_values():
    p, good = _lanes()
    for bad in (-1, 3, "A", 1.0, True):
        coloring = [row[:] for row in good]
        coloring[1][1] = bad
        result = validate(p, coloring)
        assert not result, bad
        assert "(1, 1)" in result.reason


def test_rejects_endpoint_with_wrong_color():
    p, good = _lanes()
    coloring = [row[:] for row in good]
    coloring[0][0] = 1
    result = validate(p, coloring)
    assert not result
    assert "endpoint (0, 0)" in result.reason


def test_rejects_path_that_touches_itself():
    # a Hamiltonian path, but not an induced one
    p = Puzzle.from_strings(["A..", "A.."])
    result = validate(p, coloring_from_strings(p, ["AAA", "AAA"]))
    assert not result
    assert "same-colored neighbors" in result.reason


def test_rejects_branching():
    p = Puzzle.from_strings(["A.A", "...", "B.B"])
    result = validate(p, coloring_from_strings(p, ["AAA", "AAA", "BBB"]))
    assert not result
    assert "same-colored neighbors" in result.reason


def test_accepts_numpy_like_ints():
    class IntLike:
        def __init__(self, v):
            self.v = v

        def __index__(self):
            return self.v

    p, good = _lanes()
    assert validate(p, [[IntLike(v) for v in row] for row in good])
