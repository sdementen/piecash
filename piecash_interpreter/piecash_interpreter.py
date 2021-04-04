import sys
import piecash


if sys.version_info.major == 3:

    def run_file(fname):
        with open(fname) as f:
            code = compile(f.read(), fname, "exec")
            exec(code, {})


else:

    def run_file(fname):
        return execfile(fname, {})


if len(sys.argv) == 1:
    print("Specify as argument the path to the script to run")
    sys.exit()

file = sys.argv.pop(1)
run_file(file)
