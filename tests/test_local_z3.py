import pytest

pytest.importorskip("z3")

from flowsat.bruteforce import solve_all  # noqa: E402
from flowsat.encodings.local import encode_local  # noqa: E402
from flowsat.solvers import enumerate_colorings, solve_local  # noqa: E402
from flowsat.validate import validate  # noqa: E402
from tests.instances import ALL, STRAY  # noqa: E402


@pytest.mark.parametrize("seed", [0, 1, 2])
@pytest.mark.parametrize("ex", STRAY, ids=lambda e: e.name)
def test_z3_returns_invalid_solution(ex, seed):
    # no valid solution exists, so any model Z3 returns must be invalid
    coloring, result = solve_local(ex.puzzle, seed=seed)
    assert result.status == "sat"
    verdict = validate(ex.puzzle, coloring)
    assert not verdict
    assert "stray cycle" in verdict.reason


@pytest.mark.parametrize("ex", ALL, ids=lambda e: e.name)
def test_valid_local_models_are_exactly_the_solutions(ex):
    models, exhausted = enumerate_colorings(encode_local(ex.puzzle), limit=5000)
    assert exhausted
    assert len({str(m) for m in models}) == len(models)
    valid = [m for m in models if validate(ex.puzzle, m)]
    assert sorted(valid) == sorted(solve_all(ex.puzzle))


@pytest.mark.parametrize("ex", STRAY, ids=lambda e: e.name)
def test_all_local_models_of_stray_instances_are_invalid(ex):
    models, exhausted = enumerate_colorings(encode_local(ex.puzzle), limit=5000)
    assert exhausted
    assert models
    assert ex.coloring(ex.stray_model) in models
    assert not any(validate(ex.puzzle, m) for m in models)
