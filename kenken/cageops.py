# April 24, 2013
# Scott Jespersen
"""A collection of functions for working on cages of cells."""

import itertools

def reduce_cages(kenken):
    """Shorten the candidate sets cage by cage."""
    for cage in kenken.cages:
        all_combos = get_possible_combos(cage, kenken.size)
        legal_combos = remove_illegal(all_combos, kenken.candidates)
        kenken.replace(merge_combos(legal_combos))
    return kenken


def memoize(func):
    """Cache results of wrapped function, keyed by first argument."""
    cache = {}
    def memoizer(*args):
        key = str(args[0])
        if key not in cache:
            cache[key] = func(*args)
        return cache[key]
    return memoizer


@memoize
def get_possible_combos(cage, size):
    """Return a list of all possible combinations of cell values for cage."""
    possible_combos, cells, result = [], cage['cells'], cage['result']
    if len(cells) == 1:
        # short-circuit the whole process for singletons
        possible_combos.append({cells[0]: result})
    else:
        oper = cage['operation']
        for values in itertools.product(range(1, size + 1), repeat=len(cells)):
            combo = dict(zip(cells, values))
            if (crosscheck(combo) and
                gets_right_result(combo.values(), oper, result)):
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
        # use prod function defined in this module
        return prod(nums) == result
    elif operation == "-":
        return abs(nums[0] - nums[1]) == result
    elif operation == "/":
        return (result * nums[0] == nums[1] or result * nums[1] == nums[0])
    else:
        raise Exception("Unrecognized operation: %s" % operation)


def prod(arr):
    """Return the product of all numbers in arr."""
    product = 1
    for num in arr:
        product *= num
    return product


def remove_illegal(combos, candidates):
    """Remove combos that require missing candidates and return the rest."""
    for combo in list(combos):
        for cell, value in combo.items():
            if value not in candidates[cell]:
                combos.remove(combo)
                break
    return combos


def merge_combos(combos):
    """Merge a list of dicts into one dict, taking the set union of values."""
    merged = {}
    for combo in combos:
        for cell, value in combo.items():
            if cell not in merged.keys():
                merged[cell] = set([])
            merged[cell].add(value)
    return merged