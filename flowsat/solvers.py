"""Solver backends"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol, Sequence

import z3

from flowsat.encodings.cnf import CNF
from flowsat.encodings.local import encode_local
from flowsat.puzzle import Coloring, Puzzle


@dataclass
class SolveResult:
    status: str  # "sat", "unsat" or "unknown"
    true_vars: frozenset[int] | None
    time_s: float
    stats: dict[str, float] = field(default_factory=dict)


def solver_versions() -> dict[str, str]:
    return {"z3": z3.get_version_string()}


class Z3Backend:
    name = "z3"

    def __init__(self, cnf: CNF, *, seed: int = 0, timeout_s: float | None = 60.0) -> None:
        z3.set_param("sat.random_seed", seed)
        z3.set_param("smt.random_seed", seed)
        self._solver = z3.Solver()
        if timeout_s is not None:
            self._solver.set("timeout", int(timeout_s * 1000))
        self._vars: list[z3.BoolRef | None] = [None]
        self._ensure_vars(cnf.num_vars)
        for clause in cnf.clauses:
            self.add_clause(clause)

    def _ensure_vars(self, n: int) -> None:
        while len(self._vars) <= n:
            self._vars.append(z3.Bool(f"x{len(self._vars)}"))

    def _lit(self, lit: int) -> z3.BoolRef:
        v = self._vars[abs(lit)]
        assert v is not None
        return v if lit > 0 else z3.Not(v)

    def add_clause(self, clause: Sequence[int]) -> None:
        if not clause:
            self._solver.add(z3.BoolVal(False))
            return
        self._ensure_vars(max(abs(lit) for lit in clause))
        lits = [self._lit(lit) for lit in clause]
        self._solver.add(lits[0] if len(lits) == 1 else z3.Or(*lits))

    def solve(self) -> SolveResult:
        t0 = time.perf_counter()
        result = self._solver.check()
        elapsed = time.perf_counter() - t0
        st = self._solver.statistics()
        stats = {key: st.get_key_value(key) for key in st.keys()}
        true_vars: frozenset[int] | None = None
        if result == z3.sat:
            model = self._solver.model()
            true_vars = frozenset(
                i
                for i in range(1, len(self._vars))
                if z3.is_true(model.eval(self._vars[i], model_completion=True))
            )
        return SolveResult(status=str(result), true_vars=true_vars, time_s=elapsed, stats=stats)

# solve local encoding once, result may contain stray cycles
def solve_local(
    puzzle: Puzzle, *, seed: int = 0, timeout_s: float | None = 60.0
) -> tuple[Coloring | None, SolveResult]:
    enc = encode_local(puzzle)
    result = Z3Backend(enc.cnf, seed=seed, timeout_s=timeout_s).solve()
    coloring = enc.decode(result.true_vars) if result.true_vars is not None else None
    return coloring, result


class _Enumerable(Protocol):
    cnf: CNF

    def decode(self, true_vars: frozenset[int]) -> Coloring: ...

    def blocking_clause(self, coloring: Coloring) -> list[int]: ...

# models by solve-and-block, boolean is true if enumeration finished (hit UNSAT)
def enumerate_colorings(
    enc: _Enumerable, *, limit: int = 10_000, seed: int = 0, timeout_s: float | None = 60.0
) -> tuple[list[Coloring], bool]:
    backend = Z3Backend(enc.cnf, seed=seed, timeout_s=timeout_s)
    colorings: list[Coloring] = []
    while len(colorings) < limit:
        result = backend.solve()
        if result.status == "unsat":
            return colorings, True
        if result.true_vars is None:
            raise RuntimeError(f"solver returned {result.status} during enumeration")
        coloring = enc.decode(result.true_vars)
        colorings.append(coloring)
        backend.add_clause(enc.blocking_clause(coloring))
    return colorings, False
