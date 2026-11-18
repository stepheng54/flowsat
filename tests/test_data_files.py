import json
from pathlib import Path

import pytest

from flowsat.encodings.local import encode_local
from flowsat.puzzle import load_puzzle

DATA = Path(__file__).resolve().parent.parent / "data"
FILES = sorted(DATA.rglob("*.json"))


def test_data_files_exist():
    assert FILES


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.stem)
def test_file_loads_and_is_consistent(path):
    puzzle, solution = load_puzzle(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert puzzle.name == path.stem
    if "flows" in raw:
        assert puzzle.num_colors == raw["flows"]
    if "colors" in raw:
        assert set(raw["colors"]) == set(puzzle.labels)
    if "grid" in raw:
        assert puzzle.to_strings() == raw["grid"]
    if solution is not None:
        assert encode_local(puzzle).satisfied_by(solution)
