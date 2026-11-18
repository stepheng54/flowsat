import pytest

from flowsat.bruteforce import solve_all
from flowsat.encodings.local import encode_local
from flowsat.puzzle import coloring_from_strings
from flowsat.validate import validate
from tests.instances import ALL, APP, LANES_3X3, SOLVABLE, STRAY


@pytest.mark.parametrize("ex", APP, ids=lambda e: e.name)
def test_real_app_solutions_satisfy_encoding(ex):
    assert encode_local(ex.puzzle).satisfied_by(ex.coloring(ex.solution))


@pytest.mark.parametrize("ex", ALL, ids=lambda e: e.name)
def test_only_color_variables_for_few_colors(ex):
    p = ex.puzzle
    enc = encode_local(p)
    assert enc.cnf.num_vars == p.rows * p.cols * p.num_colors


@pytest.mark.parametrize("ex", SOLVABLE, ids=lambda e: e.name)
def test_every_valid_solution_satisfies_encoding(ex):
    enc = encode_local(ex.puzzle)
    for solution in solve_all(ex.puzzle):
        assert enc.satisfied_by(solution)


@pytest.mark.parametrize("ex", STRAY, ids=lambda e: e.name)
def test_stray_model_satisfies_encoding_but_is_invalid(ex):
    enc = encode_local(ex.puzzle)
    model = ex.coloring(ex.stray_model)
    assert enc.satisfied_by(model)
    result = validate(ex.puzzle, model)
    assert not result
    assert "stray cycle" in result.reason


def test_encoding_rejects_locally_bad_colorings():
    p = LANES_3X3.puzzle
    enc = encode_local(p)
    assert not enc.satisfied_by(coloring_from_strings(p, ["AAA", "BAB", "CCC"]))
    p2 = STRAY[0].puzzle
    enc2 = encode_local(p2)
    assert not enc2.satisfied_by(coloring_from_strings(p2, ["BBBA", "BBBA", "BBBA", "AAAA"]))


@pytest.mark.parametrize("ex", SOLVABLE, ids=lambda e: e.name)
def test_decode_inverts_assignment(ex):
    enc = encode_local(ex.puzzle)
    solution = ex.coloring(ex.solution)
    assert enc.decode(enc.assignment(solution)) == solution


def test_blocking_clause_excludes_exactly_that_coloring():
    ex = STRAY[0]
    enc = encode_local(ex.puzzle)
    model = ex.coloring(ex.stray_model)
    enc.cnf.add_clause(enc.blocking_clause(model))
    assert not enc.satisfied_by(model)
