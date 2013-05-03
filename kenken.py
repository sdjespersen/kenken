#!/usr/bin/env python
# KenKen solver by Scott Jespersen
# April 29, 2013
"""Read in a KenKen in JSON format and solve it."""

# stdlib
import sys
import json
import itertools
import copy
# mine
import puzlint
import cageops
import rowops

class KenKenPuzzle:
    """Define a KenKenPuzzle with size, cages, and candidate sets."""

    def __init__(self, puz):
        """Create a new KenKenPuzzle object from an input puzzle."""
        self.size = puz['size']
        self.cages = puz['cages']
        self.generate_candidates()

    def generate_candidates(self):
        """Create a dictionary of candidates with self.size ** 2 elements. 

        Keys range from (1, 1) to (n, n) and each value is the set of integers
        from 1 to n (inclusive).

        """
        set_one_to_n = set(range(1, self.size + 1))
        self.candidates = {}
        for coord in itertools.product(set_one_to_n, repeat=2):
            self.candidates[coord] = copy.copy(set_one_to_n)

    def get_slice(self, idx, mode):
        """Return a row or column from candidates, as a dict (unordered)."""
        coord = {'row': 0, 'col': 1}
        return {cell: value for cell, value in self.candidates.items() if
                cell[coord[mode]] == idx}

    def replace(self, updates):
        """Assign given candidate cells the values in updates."""
        for cell, value in updates.items():
            self.candidates[cell] = set(value)

    def remove(self, updates):
        """Subtract input sets from given cells in candidates."""
        for cell, values in updates.items():
            self.candidates[cell].difference_update(values)

    def print_candidates(self):
        """Print the ordered candidates in tab-separated format."""
        for i in range(self.size):
            row = self.get_slice(i + 1, 'row')
            ordered = [str(row[cell]) for cell in sorted(row.keys())]
            print "\t".join(ordered)

    def has_conflicts(self):
        """Check if any candidate sets have been emptied due to conflicts."""
        return any(len(val) == 0 for val in self.candidates.values())

    def is_solved(self):
        """Check if there is exactly 1 candidate left in each cell."""
        return all(len(val) == 1 for val in self.candidates.values())


def load_puzzle(filename):
    """Handle loading, parsing, and validation of input file."""
    try:
        puzfi = open(filename)
    except IOError:
        print "Could not find puzzle file '" + filename + "'. Aborting."
        sys.exit(1)
    raw_puzzle = json.loads(puzfi.read())
    return KenKenPuzzle(puzlint.validate_kenken(raw_puzzle))


def comment(depth):
    """Say something witty in response to how deep the search has gone."""
    comments = []
    comments.append("Here we go! Starting to solve.")
    comments.append("I don't like making choices, but sometimes one must.")
    comments.append("It's getting pretty deep out here!")
    if depth < len(comments):
        return comments[depth]
    else:
        return "Depth:" + str(depth)


def solve(kenken, depth=0):
    """Run cageops, rowops, and recursive search if necessary."""
    print comment(depth)
    while not kenken.is_solved() and not kenken.has_conflicts():
        snapshot = copy.deepcopy(kenken.candidates)
        kenken = cageops.reduce_cages(kenken)
        print "After cage-reduce operations:"
        kenken.print_candidates()
        kenken = rowops.reduce_rows_and_cols(kenken)
        print "After row-reduce operations:"
        kenken.print_candidates()
        if kenken.candidates == snapshot and not kenken.is_solved():
            for sandbox in bifurcate(kenken):
                print "Sandbox before solve:"
                sandbox.print_candidates()
                sandbox = solve(sandbox, depth + 1)
                print "Sandbox after solve:"
                sandbox.print_candidates()
                if sandbox.has_conflicts():
                    print "Conflicts found. Moving on."
                    continue
                else:
                    print "Solved!"
                    sandbox.print_candidates()
                    return sandbox
    return kenken


def bifurcate(kenken):
    """Make a choice in the cell with the smallest number > 1 of candidates."""
    unsolved = [cell for cell in kenken.candidates.items() if len(cell[1]) > 1]
    for cell, choices in sorted(unsolved, key=lambda (cell, val): len(val)):
        for choice in choices:
            print "Choosing", choice, "from", choices, "in", cell
            kenken.candidates[cell] = set([choice])
            yield kenken


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        print "Missing argument: Input puzzle filename. Exiting."
        sys.exit(1)
    else:
        solved = solve(load_puzzle(filename))
        solved.print_candidates()
