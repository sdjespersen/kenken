# KenKen solver by Scott Jespersen
# April 29, 2013, updates June 2020
"""A solver for specially-formatted KenKen puzzles."""

import collections
import copy
import functools
import itertools
import json
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple


CandidatesType = Dict[Tuple[int, ...], Set[int]]


class NoSolutionError(Exception):
    pass


class KenKenPuzzle:
    """Define a KenKenPuzzle with size, cages, and candidate sets."""

    def __init__(self, size: int, cages: Tuple[Dict[str, Any]]) -> None:
        """Create a new KenKenPuzzle object with the given inputs."""
        self.size: int = size
        self.cages: Tuple[Dict[str, Any]] = cages
        self.solution: Optional[List[List[int]]] = None
        self.candidates: CandidatesType = {}
        for coord in itertools.product(set(range(1, size + 1)), repeat=2):
            self.candidates[coord] = set(range(1, size + 1))

    def solve(self, depth: int = 0) -> None:
        """Solve the KenKen."""
        return _solve(self, depth=depth)

    def _get_slice(self, idx, mode):
        """Return a row or column from candidates, as a dict (unordered)."""
        coord = {'row': 0, 'col': 1}
        return {cell: value for cell, value in self.candidates.items()
                if cell[coord[mode]] == idx}

    def _replace(self, updates: CandidatesType) -> None:
        """Assign given candidate cells the values in updates."""
        for cell, value in updates.items():
            self.candidates[cell] = set(value)

    def _remove(self, updates: CandidatesType) -> None:
        """Subtract input sets from given cells in candidates."""
        for cell, values in updates.items():
            self.candidates[cell].difference_update(values)

    def _has_conflicts(self) -> bool:
        """Check if any candidate sets have been emptied due to conflicts."""
        return any(len(val) == 0 for val in self.candidates.values())

    def _is_solved(self) -> bool:
        """Check if there is exactly 1 candidate left in each cell."""
        done = all(len(val) == 1 for val in self.candidates.values())
        if done and self.solution is None:
            self.solution = [
                [0 for _ in range(self.size)] for _ in range(self.size)]
            for coord, values in self.candidates.items():
                self.solution[coord[0] - 1][coord[1] - 1] = (
                    copy.copy(values).pop())
        return self.solution is not None


def load_from_json(filename: os.PathLike) -> KenKenPuzzle:
    """Parse json from the given file, then validate and return the puzzle."""
    with open(filename) as f:
        return load(json.loads(f.read()))


def load(puzzle: Dict[str, Any]) -> KenKenPuzzle:
    """Validate and return the given puzzle as a KenKenPuzzle."""
    validated = validate(puzzle)
    return KenKenPuzzle(validated['size'], validated['cages'])


def _solve(kenken: KenKenPuzzle, depth: int = 0) -> None:
    """Run cageops, rowops, and recursive search if necessary."""
    while not kenken._is_solved() and not kenken._has_conflicts():
        snapshot = copy.deepcopy(kenken.candidates)
        kenken = _reduce_cages(kenken)
        kenken = _reduce_rows_and_cols(kenken)
        if kenken.candidates == snapshot and not kenken._is_solved():
            unsolved = [cell for cell in kenken.candidates.items()
                        if len(cell[1]) > 1]
            cell, choices = min(unsolved, key=lambda kv: len(kv[1]))
            for choice in choices:
                logging.info(f"Choosing {choice} in {cell}")
                proposal = KenKenPuzzle(kenken.size, kenken.cages)
                proposal.candidates = copy.deepcopy(kenken.candidates)
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
    if kenken._has_conflicts():
        raise NoSolutionError()


def _reduce_cages(kenken: KenKenPuzzle) -> KenKenPuzzle:
    """Shorten the candidate sets cage by cage."""
    for cage in kenken.cages:
        all_combos = _get_possible_combos(cage, kenken.size)
        legal_combos = _remove_illegal(all_combos, kenken.candidates)
        kenken._replace(_merge_combos(legal_combos))
    return kenken


def _get_possible_combos(cage, size):
    """Return a list of all possible combinations of cell values for cage."""
    possible_combos, cells, result = [], cage['cells'], cage['result']
    if len(cells) == 1:
        # short-circuit the whole process for singletons
        possible_combos.append({cells[0]: result})
    else:
        oper = cage['operation']
        for values in itertools.product(range(1, size + 1), repeat=len(cells)):
            combo = dict(zip(cells, values))
            correct_result = gets_right_result(
                list(combo.values()), oper, result)
            if crosscheck(combo) and correct_result:
                possible_combos.append(combo)
    return possible_combos


def crosscheck(cells):
    """Check for duplicate values in any row or column."""
    for coord1, coord2 in itertools.combinations(cells.keys(), 2):
        # check values first, coordinates second
        if cells[coord1] == cells[coord2]:
            if (coord1[0] == coord2[0] or coord1[1] == coord2[1]):
                return False
    return True


def gets_right_result(nums, operation, result):
    """Check that nums under operation produce result."""
    if operation == "+":
        return sum(nums) == result
    elif operation == "*":
        return _prod(nums) == result
    elif operation == "-":
        return abs(nums[0] - nums[1]) == result
    elif operation == "/":
        return (result * nums[0] == nums[1] or result * nums[1] == nums[0])
    else:
        raise Exception("Unrecognized operation: %s" % operation)


def _prod(xs):
    """Return the product of all numbers in xs."""
    return functools.reduce(lambda x, y: x * y, xs, 1)


def _remove_illegal(combos, candidates):
    """Remove combos that require missing candidates and return the rest."""
    for combo in list(combos):
        for cell, value in combo.items():
            if value not in candidates[cell]:
                combos.remove(combo)
                break
    return combos


def _merge_combos(combos):
    """Merge a list of dicts into one dict, taking the set union of values."""
    merged = collections.defaultdict(set)
    for combo in combos:
        for cell, value in combo.items():
            merged[cell].add(value)
    return merged


def _reduce_rows_and_cols(kenken: KenKenPuzzle) -> KenKenPuzzle:
    """Execute strategies on each row and column. Repeat until unchanged."""
    while True:
        snapshot: CandidatesType = copy.deepcopy(kenken.candidates)
        for m in range(kenken.size):
            for mode in ('row', 'col'):
                slice_m = _get_slice(kenken, m + 1, mode)
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
            return kenken


def _get_slice(kenken, idx, mode):
    """Return a row or column from candidates, as a dict (unordered)."""
    coord = {'row': 0, 'col': 1}
    return {cell: value for cell, value in kenken.candidates.items()
            if cell[coord[mode]] == idx}


def _check_no_duplicates(cslice):
    """Fail if there are any duplicate values in this slice."""
    for cands1, cands2 in itertools.combinations(cslice.values(), 2):
        if len(cands1) == 1 and cands1 == cands2:
            raise NoSolutionError()


def _find_exposed_groups(row, n):
    """
    Find all sets of n cells in row that contain only the same n candidates.
    """
    groups = {}
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


def _find_hidden_groups(row, n):
    """Find all sets of n cells in row that exclusively contain the same n
    candidates."""
    hidden = {}
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


def validate(puzzle: Dict[str, Any]) -> Dict[str, Any]:
    """Validate, parse, and return the incoming puzzle. Not bulletproof."""
    assert type(puzzle) is dict
    assert set(puzzle.keys()).issuperset(set(['cages', 'size']))

    size = copy.copy(puzzle['size'])
    cages = copy.deepcopy(puzzle['cages'])

    assert type(size) is int
    assert type(cages) in (list, tuple)

    valid_puz = {}
    valid_puz['size'] = size
    valid_puz['cages'] = []

    # for value and size testing
    all_cells = []

    for cage in cages:
        assert type(cage) is dict
        assert set(cage.keys()).issuperset(set(['cells', 'result']))

        assert type(cage['result']) is int
        assert type(cage['cells']) in (list, tuple)
        cage['cells'] = tuple([tuple(c) for c in cage['cells']])
        cells = cage['cells']

        for cell in cells:
            assert type(cell) is tuple
            assert len(cell) == 2
            assert all(type(x) is int for x in (cell[0], cell[1]))
            assert all(x in range(1, size + 1) for x in (cell[0], cell[1]))
            all_cells.append(cell)

        if len(cells) > 1:
            assert 'operation' in cage.keys()
            operation = cage['operation']
            assert operation in ('+', '-', '*', '/')
            result = cage['result']
            if operation in ('-', '/'):
                assert len(cells) == 2
            if operation == '-':
                assert result in range(1, size)
            if operation == '/':
                assert result in range(1, size + 1)

        cage['cells'] = tuple(cells)
        valid_puz['cages'].append(cage)

    assert len(all_cells) == size * size
    assert len(all_cells) == len(set(all_cells))
    logging.info("Input puzzle validated.")

    valid_puz['cages'] = tuple(valid_puz['cages'])
    return valid_puz
