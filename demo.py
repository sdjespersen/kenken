import sys
import kenken.main as kenken

try:
    filename = sys.argv[1]
except IndexError:
    print "Missing argument: Input puzzle filename. Exiting."
    sys.exit(1)
else:
    solved = kenken.solve(kenken.load_puzzle(filename))
    solved.print_candidates()
