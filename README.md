# KenKen Solver

## Usage

Load a puzzle, solve, obtain the solution:

```python
import kenken
puz = kenken.load_from_json('./tests/6-1.json')
puz.solve()
print("\n".join([str(s) for s in puz.solution]))
```
yields
```
(1, 5, 3, 4, 6, 2)
(6, 4, 1, 2, 3, 5)
(4, 6, 2, 5, 1, 3)
(3, 1, 5, 6, 2, 4)
(5, 2, 6, 3, 4, 1)
(2, 3, 4, 1, 5, 6)
```

## Approach

This solver applies pretty rudimentary logic to reduce the size of candidate
sets and thus reduce the search depth. For 4-by-4 and 6-by-6 puzzles, solving is
near-instantaneous. 8-by-8 puzzles take under 1 second.
