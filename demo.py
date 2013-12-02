import sys
import kenken.main

try:
    filename = sys.argv[1]
except IndexError:
    print "Missing argument: Input puzzle filename. Exiting."
    sys.exit(1)
else:
    solved = kenken.main.solve(kenken.main.load_puzzle(filename))
    solved.print_candidates()
