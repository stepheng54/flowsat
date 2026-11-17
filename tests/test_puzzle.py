import json
from pathlib import Path

import pytest

from flowsat.puzzle import (
    UNCOLORED,
    Puzzle,
    coloring_from_strings,
    coloring_to_strings,
    load_puzzle,
    save_puzzle,
)
from tests.instances import ALL, FIVE_COLOR_5X5, STRAY

DATA = Path(__file__).resolve().parent.parent / "data" / "handcrafted"


def test_from_strings_numbers_colors_by_first_appearance():
    p = Puzzle.from_strings(["..BA", "....", "B...", "A..."])
    assert (p.rows, p.cols, p.num_colors) == (4, 4, 2)
    assert p.labels == ("B", "A")
    assert p.endpoints == (((0, 2), (2, 0)), ((0, 3), (3, 0)))
    assert p.endpoint_owner == {(0, 2): 0, (2, 0): 0, (0, 3): 1, (3, 0): 1}


@pytest.mark.parametrize("ex", ALL, ids=lambda e: e.name)
def test_strings_round_trip(ex):
    assert ex.puzzle.to_strings() == list(ex.grid)


@pytest.mark.parametrize(
    "lines",
    [
        ["A..", "..."],          # label appears once
        ["AAA", "..A"],          # label appears three times
        ["A.A", ".."],           # ragged rows
        [],                      # empty
    ],
)
def test_from_strings_rejects_bad_grids(lines):
    with pytest.raises(ValueError):
        Puzzle.from_strings(lines)


def test_constructor_rejects_bad_endpoints():
    with pytest.raises(ValueError):  # out of bounds
        Puzzle(2, 2, (((0, 0), (2, 0)),), ("A",))
    with pytest.raises(ValueError):  # same cell twice
        Puzzle(2, 2, (((0, 0), (0, 0)),), ("A",))
    with pytest.raises(ValueError):  # cell shared by two colors
        Puzzle(2, 2, (((0, 0), (0, 1)), ((0, 1), (1, 1))), ("A", "B"))
    with pytest.raises(ValueError):  # label count mismatch
        Puzzle(2, 2, (((0, 0), (0, 1)),), ("A", "B"))


def test_neighbors():
    p = Puzzle.from_strings(["A..", "...", "..A"])
    assert sorted(p.neighbors((0, 0))) == [(0, 1), (1, 0)]
    assert sorted(p.neighbors((0, 1))) == [(0, 0), (0, 2), (1, 1)]
    assert sorted(p.neighbors((1, 1))) == [(0, 1), (1, 0), (1, 2), (2, 1)]


def test_dict_round_trip():
    p = FIVE_COLOR_5X5.puzzle
    assert Puzzle.from_dict(json.loads(json.dumps(p.to_dict()))) == p


def test_file_round_trip_with_solution(tmp_path):
    ex = FIVE_COLOR_5X5
    path = tmp_path / "p.json"
    save_puzzle(path, ex.puzzle, ex.coloring(ex.solution))
    loaded, solution = load_puzzle(path)
    assert loaded == ex.puzzle
    assert solution == ex.coloring(ex.solution)


def test_coloring_strings():
    p = Puzzle.from_strings(["A.B", "A.B"])
    coloring = coloring_from_strings(p, ["A.B", "AAB"])
    assert coloring == [[0, UNCOLORED, 1], [0, 0, 1]]
    assert coloring_to_strings(p, coloring) == ["A.B", "AAB"]
    with pytest.raises(ValueError):
        coloring_from_strings(p, ["AZB", "AAB"])


@pytest.mark.parametrize("ex", STRAY, ids=lambda e: e.name)
def test_handcrafted_files_match_test_instances(ex):
    puzzle, solution = load_puzzle(DATA / f"{ex.name}.json")
    assert puzzle == ex.puzzle
    assert solution is None
