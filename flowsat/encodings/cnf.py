"""CNF container and cardinality constraints shared by all encodings.

Exactly-one uses pairwise at-most-one (sequential counter above PAIRWISE_AMO_MAX literals).
Guarded exactly-d over a cell's neighbors uses direct subset enumeration.
"""

from __future__ import annotations

from itertools import combinations
from typing import Collection, Iterable, Sequence

PAIRWISE_AMO_MAX = 16
GUARDED_MAX_LITS = 8


class CNF:
    def __init__(self) -> None:
        self.num_vars: int = 0
        self.clauses: list[list[int]] = []

    def new_var(self) -> int:
        self.num_vars += 1
        return self.num_vars

    def new_vars(self, n: int) -> list[int]:
        return [self.new_var() for _ in range(n)]

    def add_clause(self, clause: Iterable[int]) -> None:
        lits = [int(lit) for lit in clause]
        for lit in lits:
            if lit == 0 or abs(lit) > self.num_vars:
                raise ValueError(f"literal {lit} does not refer to an allocated variable")
        self.clauses.append(lits)

    @property
    def num_clauses(self) -> int:
        return len(self.clauses)

    def is_satisfied_by(self, true_vars: Collection[int]) -> bool:
        true_set = set(true_vars)
        return all(
            any((lit > 0) == (abs(lit) in true_set) for lit in clause) for clause in self.clauses
        )

    def to_dimacs(self) -> str:
        lines = [f"p cnf {self.num_vars} {len(self.clauses)}"]
        lines.extend(" ".join(map(str, [*clause, 0])) for clause in self.clauses)
        return "\n".join(lines) + "\n"


def add_at_least_one(cnf: CNF, lits: Sequence[int]) -> None:
    cnf.add_clause(lits)


def add_at_most_one(cnf: CNF, lits: Sequence[int]) -> None:
    lits = list(lits)
    if len(lits) <= PAIRWISE_AMO_MAX:
        for a, b in combinations(lits, 2):
            cnf.add_clause([-a, -b])
    else:
        _add_sequential_amo(cnf, lits)


def _add_sequential_amo(cnf: CNF, lits: list[int]) -> None:
    # Sinz 2005; s[i] = some of lits[0..i] is true
    n = len(lits)
    s = cnf.new_vars(n - 1)
    cnf.add_clause([-lits[0], s[0]])
    for i in range(1, n - 1):
        cnf.add_clause([-lits[i], s[i]])
        cnf.add_clause([-s[i - 1], s[i]])
        cnf.add_clause([-lits[i], -s[i - 1]])
    cnf.add_clause([-lits[n - 1], -s[n - 2]])


def add_exactly_one(cnf: CNF, lits: Sequence[int]) -> None:
    lits = list(lits)
    add_at_least_one(cnf, lits)
    add_at_most_one(cnf, lits)


# guard -> exactly d of lits
def add_guarded_exactly(cnf: CNF, guard: int, lits: Sequence[int], d: int) -> None:
    lits = list(lits)
    n = len(lits)
    if n > GUARDED_MAX_LITS:
        raise ValueError(f"subset enumeration is only meant for <= {GUARDED_MAX_LITS} literals")
    if d < 0:
        raise ValueError("d must be non-negative")
    if d > n:
        cnf.add_clause([-guard])
        return
    for subset in combinations(lits, d + 1):  # at most d
        cnf.add_clause([-guard, *(-lit for lit in subset)])
    if d > 0:
        for subset in combinations(lits, n - d + 1):  # at least d
            cnf.add_clause([-guard, *subset])
