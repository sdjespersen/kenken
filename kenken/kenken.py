# KenKen solver by Scott Jespersen and Amy Shoemaker
# April 29, 2013, updates June 2020
"""A solver for specially-formatted KenKen puzzles."""

import collections
import functools
import itertools
import json
import logging
import os
from typing import (
    Dict, FrozenSet, Iterable, List, NamedTuple, Optional, Set, Tuple
)


# A 2-D coordinate of a cell in a KenKen
Cell = Tuple[int, int]
# A mapping from a Cell to a set of candidate solutions
Candidates = Dict[Cell, Set[int]]
# A possible solution for a given cage of cells
CageCombo = Tuple[Tuple[Cell, int], ...]
# A solution to the puzzle
Solution = Tuple[Tuple[int, ...], ...]


class NoSolutionError(Exception):
    pass


class Cage(NamedTuple):
    cells: FrozenSet[Cell]
    result: int
    operation: Optional[str] = None


class KenKenPuzzle:
    """Define a KenKenPuzzle with size, cages, and candidate sets."""

    def __init__(self, size: int, cages: Tuple[Cage, ...]) -> None:
        """Create a new KenKenPuzzle object with the given inputs."""
        self.size: int = size
        self.cages: Tuple[Cage, ...] = cages
        self.solution: Optional[Solution] = None
        self.candidates: Candidates = {}
        # Initialize candidates: All possible values in each cell
        for i, j in itertools.product(set(range(1, size + 1)), repeat=2):
            self.candidates[(i, j)] = set(range(1, size + 1))

    def solve(self, depth: int = 0) -> None:
        """Solve the KenKen."""
        return _solve(self, depth=depth)

    def _get_slice(self, idx: int, mode: str) -> Candidates:
        """Return a row or column from candidates, as a dict."""
        coord = {'row': 0, 'col': 1}
        return {cell: value for cell, value in self.candidates.items()
                if cell[coord[mode]] == idx}

    def _replace(self, updates: Candidates) -> None:
        """Assign given candidate cells the values in updates."""
        for cell, value in updates.items():
            self.candidates[cell] = set(value)

    def _remove(self, updates: Candidates) -> None:
        """Subtract input sets from given cells in candidates."""
        for cell, values in updates.items():
            self.candidates[cell].difference_update(values)

    def _has_conflicts(self) -> bool:
        """Check if any candidate sets have been emptied due to conflicts."""
        return any(len(val) == 0 for val in self.candidates.values())

    def _is_solved(self) -> bool:
        """Check if the KenKen is solved."""
        if not all(len(val) == 1 for val in self.candidates.values()):
            return False
        # Check all cages and throw if invalid
        for cage in self.cages:
            nums: List[int] = [
                next(iter(self.candidates[cell])) for cell in cage.cells]
            if not _gets_right_result(nums, cage.operation, cage.result):
                raise NoSolutionError()
        # Check all rows/cols and throw if invalid
        for mode in ('row', 'col'):
            for i in range(1, self.size + 1):
                slice_set = set(
                    [next(iter(z)) for z in self._get_slice(i, mode).values()])
                if not slice_set == set(range(1, self.size + 1)):
                    raise NoSolutionError()
        # Valid! Save solution.
        if self.solution is None:
            sol = [[0 for _ in range(self.size)] for _ in range(self.size)]
            for coord, values in self.candidates.items():
                sol[coord[0] - 1][coord[1] - 1] = next(iter(values))
            self.solution = tuple([tuple(v) for v in sol])
        return True


def load_from_json(filename: os.PathLike) -> KenKenPuzzle:
    """Parse json from the given file, then validate and return the puzzle."""
    with open(filename) as f:
        parsed = json.loads(f.read())
        cages = [Cage(**v) for v in parsed['cages']]
        return load(parsed['size'], cages)


def load(size: int, cages: Iterable[Cage]) -> KenKenPuzzle:
    """Validate and return the given puzzle spec as a KenKenPuzzle."""
    return KenKenPuzzle(*validate(size, cages))


def _solve(kenken: KenKenPuzzle, depth: int = 0) -> None:
    """Solve the KenKen with deduction and recursive search when needed."""
    while not kenken._is_solved():
        snapshot = _copy_candidates(kenken)
        _reduce_cages(kenken)
        _reduce_rows_and_cols(kenken)
        if kenken.candidates == snapshot and not kenken._is_solved():
            unsolved = [cell for cell in kenken.candidates.items()
                        if len(cell[1]) > 1]
            cell, choices = min(unsolved, key=lambda kv: len(kv[1]))
            for choice in choices:
                logging.info(f"Choosing {choice} in {cell}")
                proposal = KenKenPuzzle(kenken.size, kenken.cages)
                proposal.candidates = _copy_candidates(kenken)
                proposal.candidates[cell] = {choice}
                try:
                    _solve(proposal, depth + 1)
                    kenken.candidates = proposal.candidates
                    assert kenken._is_solved()
                    return
                except NoSolutionError:
                    logging.info(f"Choosing {choice} in {cell} failed, next")
                    continue
            raise NoSolutionError()


def _reduce_cages(kenken: KenKenPuzzle) -> None:
    """Shorten the candidate sets cage by cage."""
    for cage in kenken.cages:
        all_combos = _get_possible_combos(cage, kenken.size)
        legal_combos = _remove_illegal(all_combos, kenken.candidates)
        kenken._replace(_merge_combos(legal_combos))


def memoize(f):
    cache = {}
    def memoized(cage: Cage, size: int) -> Tuple[CageCombo, ...]:
        key = (cage, size)
        if key not in cache:
            cache[key] = f(cage, size)
        return cache[key]
    return memoized


@memoize
def _get_possible_combos(cage: Cage, size: int) -> Tuple[CageCombo, ...]:
    """Return a list of all possible combinations of cell values for cage."""
    possible_combos: List[CageCombo] = []
    cells: FrozenSet[Cell] = cage.cells
    if len(cells) == 1:
        # short-circuit the whole process for singletons
        cell: Cell = next(iter(cells))
        possible_combos.append(((cell, cage.result),))
    else:
        for values in itertools.product(range(1, size + 1), repeat=len(cells)):
            combo = dict(zip(cells, values))
            correct_result = _gets_right_result(
                list(combo.values()), cage.operation, cage.result)
            if _crosscheck(combo) and correct_result:
                possible_combos.append(tuple(combo.items()))
    return tuple(possible_combos)


def _crosscheck(cells: Candidates) -> bool:
    """Check for duplicate values in any row or column."""
    for coord1, coord2 in itertools.combinations(cells.keys(), 2):
        # check values first, coordinates second
        if cells[coord1] == cells[coord2]:
            if (coord1[0] == coord2[0] or coord1[1] == coord2[1]):
                return False
    return True


def _gets_right_result(
        nums: List[int], operation: Optional[str], result: int) -> bool:
    """Check that nums under operation produce result."""
    if operation == "+":
        return sum(nums) == result
    elif operation == "*":
        return _prod(nums) == result
    elif operation == "-":
        return abs(nums[0] - nums[1]) == result
    elif operation == "/":
        return (result * nums[0] == nums[1] or result * nums[1] == nums[0])
    elif operation is None:
        return nums[0] == result
    else:
        raise Exception("Unrecognized operation: %s" % operation)


def _prod(xs: List[int]) -> int:
    """Return the product of all numbers in xs."""
    return functools.reduce(lambda x, y: x * y, xs, 1)


def _remove_illegal(
        combos: Tuple[CageCombo, ...],
        candidates: Candidates) -> Tuple[CageCombo, ...]:
    """Remove combos that require missing candidates and return the rest."""
    legal_combos: List[CageCombo] = []
    for combo in combos:
        legal_combos.append(combo)
        for cell, value in combo:
            if value not in candidates[cell]:
                legal_combos.pop()
                break
    return tuple(legal_combos)


def _merge_combos(combos: Tuple[CageCombo, ...]) -> Dict[Cell, Set[int]]:
    """Merge a list of dicts into one dict, taking the set union of values."""
    merged = collections.defaultdict(set)
    for combo in combos:
        for cell, value in combo:
            merged[cell].add(value)
    return merged


def _reduce_rows_and_cols(kenken: KenKenPuzzle) -> None:
    """Execute strategies on each row and column. Repeat until unchanged."""
    while True:
        snapshot: Candidates = _copy_candidates(kenken)
        for m in range(kenken.size):
            for mode in ('row', 'col'):
                slice_m: Candidates = _get_slice(kenken, m + 1, mode)
                for n in range(1, kenken.size // 2 + 1):
                    exposed_groups = _find_exposed_groups(slice_m, n)
                    if exposed_groups:
                        kenken._remove(_invert(exposed_groups, slice_m))
                    hidden_groups = _find_hidden_groups(slice_m, n)
                    if hidden_groups:
                        kenken._replace(hidden_groups)
                        kenken._remove(_invert(hidden_groups, slice_m))
                _check_no_duplicates(slice_m)
        if kenken.candidates == snapshot:
            return


def _get_slice(kenken: KenKenPuzzle, idx: int, mode: str) -> Candidates:
    """Return a row or column from candidates, as a dict (unordered)."""
    coord = {'row': 0, 'col': 1}
    return {cell: value for cell, value in kenken.candidates.items()
            if cell[coord[mode]] == idx}


def _check_no_duplicates(cslice: Candidates) -> None:
    """Fail if there are any duplicate values in this slice."""
    for cands1, cands2 in itertools.combinations(cslice.values(), 2):
        if len(cands1) == 1 and cands1 == cands2:
            raise NoSolutionError()


def _find_exposed_groups(row: Candidates, n: int) -> Dict[Cell, Set[int]]:
    """
    Find all sets of n cells in row that contain only the same n candidates.
    """
    groups: Dict[Cell, Set[int]] = {}
    length_n_cells = [
        {cell: value} for cell, value in row.items() if len(value) == n]
    if len(length_n_cells) >= n:
        for group in itertools.combinations(length_n_cells, n):
            if all([*group[n].values()][0] == [*group[n + 1].values()][0]
                   for n in range(len(group) - 1)):
                # Then we've found an exposed combo!
                for elem in group:
                    groups.update(elem)
    return groups


def _find_hidden_groups(row: Candidates, n: int) -> Dict[Cell, Set[int]]:
    """Find all sets of n cells in row that exclusively contain the same n
    candidates."""
    hidden: Dict[Cell, Set[int]] = {}
    flatrow = _flatten(row.values())
    appears_n_times = [i for i in set(flatrow) if flatrow.count(i) == n]
    if len(appears_n_times) >= n:
        for combo in itertools.combinations(appears_n_times, n):
            if _always_together(combo, row.values()):
                # Then we've found a hidden combo!
                for coords, val in row.items():
                    if set(combo).issubset(val):
                        hidden[coords] = set(combo)
    return hidden


def _flatten(arr):
    """Return a deeply flattened list copy of nested list, tuple, or set."""
    flat = []
    if type(arr) in (list, tuple, set):
        for el in arr:
            flat.extend(_flatten(el))
    else:
        flat.append(arr)
    return flat


def _always_together(nums, arr):
    """Check if nums always appear together in elements of arr."""
    return all(set(nums).issubset(set(el)) or set(nums).isdisjoint(set(el))
               for el in arr)


def _invert(updates, row):
    """Return a new dict specifying cells and values for removal."""
    to_be_deleted = {cell: set([]) for cell in row.keys()}
    for key, value in updates.items():
        for cell in to_be_deleted.keys():
            if cell != key:
                to_be_deleted[cell].update(value)
    for cell in to_be_deleted.keys():
        if cell in updates.keys():
            to_be_deleted[cell].difference_update(updates[cell])
    return to_be_deleted


def _copy_candidates(kenken: KenKenPuzzle) -> Candidates:
    return {k: set(v) for k, v in kenken.candidates.items()}


def validate(size: int, cages: Iterable[Cage]) -> Tuple[int, Tuple[Cage, ...]]:
    """Validate, parse, and return the incoming puzzle. Not bulletproof."""
    all_cages: List[Cage] = []
    # To make sure all cells were covered
    all_cells: List[Cell] = []

    for cage in cages:
        for cell in cage.cells:
            assert len(cell) == 2
            assert all(type(x) is int for x in (cell[0], cell[1]))
            assert all(x in range(1, size + 1) for x in (cell[0], cell[1]))

        if len(cage.cells) > 1:
            assert cage.operation is not None
            assert cage.operation in ('+', '-', '*', '/')
            if cage.operation in ('-', '/'):
                assert len(cage.cells) == 2
            if cage.operation == '-':
                assert cage.result in range(1, size)
            if cage.operation == '/':
                assert cage.result in range(1, size + 1)
        valid_cells: FrozenSet[Cell] = (
            frozenset([(v[0], v[1]) for v in cage.cells]))
        all_cells.extend(valid_cells)
        all_cages.append(Cage(
            cells=valid_cells, result=cage.result, operation=cage.operation))

    assert len(all_cells) == size * size
    assert len(all_cells) == len(set(all_cells))
    logging.info("Input puzzle validated.")

    return size, tuple(all_cages)
