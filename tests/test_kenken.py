import kenken
import pathlib
import pytest


def load_puzzle(relpath):
    abspath = pathlib.Path(__file__).parent / relpath
    return kenken.load_from_json(abspath)


def test_solve_4_1():
    solution = [
        [3, 2, 4, 1],
        [2, 4, 1, 3],
        [1, 3, 2, 4],
        [4, 1, 3, 2],
    ]
    puz = load_puzzle("4-1.json")
    puz.solve()
    assert puz.solution == solution


def test_solve_6_1():
    solution = [
        [1, 5, 3, 4, 6, 2],
        [6, 4, 1, 2, 3, 5],
        [4, 6, 2, 5, 1, 3],
        [3, 1, 5, 6, 2, 4],
        [5, 2, 6, 3, 4, 1],
        [2, 3, 4, 1, 5, 6],
    ]
    puz = load_puzzle("6-1.json")
    puz.solve()
    assert puz.solution == solution


def test_solve_6_2():
    solution = [
        [2, 3, 4, 5, 6, 1],
        [4, 2, 6, 1, 3, 5],
        [6, 4, 1, 3, 5, 2],
        [3, 1, 5, 2, 4, 6],
        [5, 6, 2, 4, 1, 3],
        [1, 5, 3, 6, 2, 4],
    ]
    puz = load_puzzle("6-2.json")
    puz.solve()
    assert puz.solution == solution


def test_solve_6_3():
    solution = [
        [4, 5, 6, 2, 1, 3],
        [2, 1, 5, 4, 3, 6],
        [5, 3, 4, 1, 6, 2],
        [3, 6, 1, 5, 2, 4],
        [6, 4, 2, 3, 5, 1],
        [1, 2, 3, 6, 4, 5],
    ]
    puz = load_puzzle("6-3.json")
    puz.solve()
    assert puz.solution == solution


@pytest.mark.skip("I don't know the solution yet")
def test_solve_8_1():
    solution = [[0 for _ in range(8)] for _ in range(8)]
    puz = load_puzzle("8-1.json")
    puz.solve()
    assert puz.solution == solution
