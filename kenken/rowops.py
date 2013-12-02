# April 24, 2013
# Scott Jespersen
"""A collection of functions for working on a single row/column at a time."""

import itertools
import copy

def reduce_rows_and_cols(kenken):
    """Execute strategies on each row and column. Repeat until unchanged."""
    snapshot = None
    while snapshot != kenken.candidates:
        snapshot = copy.deepcopy(kenken.candidates)
        for m in range(kenken.size):
            for n in range(1, kenken.size / 2 + 1):
                for mode in ('row', 'col'):
                    slice_m = kenken.get_slice(m + 1, mode)
                    exposed_groups = find_exposed_groups(slice_m, n)
                    if exposed_groups:
                        kenken.remove(invert(exposed_groups, slice_m))
                    hidden_groups = find_hidden_groups(slice_m, n)
                    if hidden_groups:
                        kenken.replace(hidden_groups)
                        kenken.remove(invert(hidden_groups, slice_m))
    return kenken


def find_exposed_groups(row, n):
    """Find all sets of n cells in row that contain only the same n
    candidates."""
    groups = {}
    length_n_cells = get_has_n_elements(row, n)
    if len(length_n_cells) >= n:
        for group in itertools.combinations(length_n_cells, n):
            if all(group[n].values() == group[n+1].values()
                   for n in range(len(group) - 1)):
                # Then we've found an exposed combo!
                for elem in group:
                    groups.update(elem)
    return groups


def get_has_n_elements(row, n):
    """Return a list of the cells and values that have length n."""
    return [{cell: value} for cell, value in row.items() if len(value) == n]


def find_hidden_groups(row, n):
    """Find all sets of n cells in row that exclusively contain the same n
    candidates."""
    hidden = {}
    appears_n_times = get_appears_n_times(flatten(row.values()), n)
    if len(appears_n_times) >= n:
        for combo in itertools.combinations(appears_n_times, n):
            if always_together(combo, row.values()):
                # Then we've found a hidden combo!
                for coords, val in row.items():
                    if set(combo).issubset(val):
                        hidden[coords] = set(combo)
    return hidden


def get_appears_n_times(row, n):
    """Return a list of elements in row that appear n times."""
    return [i for i in set(row) if row.count(i) == n]


def flatten(arr):
    """Return a deeply flattened list copy of nested list, tuple, or set."""
    flat = []
    if type(arr) in (list, tuple, set):
        for el in arr:
            flat.extend(flatten(el))
    else:
        flat.append(arr)
    return flat


def always_together(nums, arr):
    """Check if nums always appear together in elements of arr."""
    return all(set(nums).issubset(set(el)) or
               set(nums).isdisjoint(set(el)) for el in arr)


def invert(updates, row):
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
