# April 21, 2013
# Scott Jespersen
"""Module to check if an input KenKen is valid."""

import ast

def validate_kenken(puzzle):
    """Validate, parse, and return the incoming puzzle. Not bulletproof."""
    assert type(puzzle) is dict
    assert set(puzzle.keys()).issuperset(set(['cages', 'size']))

    size = puzzle['size']
    cages = puzzle['cages']

    assert type(size) is int
    assert type(cages) in (list, tuple)

    valid_puz = {}
    valid_puz['size'] = size
    valid_puz['cages'] = []

    # for value and size testing
    all_cells = []

    for cage in cages:
        assert type(cage) is dict
        assert set(cage.keys()).issuperset(set(['cells','result']))

        result = cage['result']
        cells = ast.literal_eval(cage['cells'])

        assert type(result) is int
        assert type(cells) is tuple

        for cell in cells:
            assert type(cell) is tuple
            assert len(cell) == 2
            assert all(type(x) is int for x in (cell[0], cell[1]))
            assert all(x in range(1, size+1) for x in (cell[0], cell[1]))
            all_cells.append(cell)

        if len(cells) > 1:
            assert 'operation' in cage.keys()
            operation = cage['operation']
            assert operation in ('+', '-', '*', '/')
            if operation in ('-', '/'):
                assert len(cells) == 2
            if operation is '-':
                assert result in range(1, size)
            if operation is '/':
                assert result in range(1, size + 1)

        cage['cells'] = tuple(cells)
        valid_puz['cages'].append(cage)

    assert len(all_cells) == size * size
    assert len(all_cells) == len(set(all_cells))
    print "Input puzzle validated."

    valid_puz['cages'] = tuple(valid_puz['cages'])
    return valid_puz
