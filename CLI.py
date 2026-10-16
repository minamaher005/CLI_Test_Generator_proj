from argparse import ArgumentParser
from filecheck import check_imports_and_one_function
from prompt_builder import generate_py_file
parser = ArgumentParser()
parser.add_argument("pythonfile", help="Path to a Python file", type=str)
args = parser.parse_args()

if not args.pythonfile.lower().endswith(".py"):
    parser.error("Input must be a .py file")

is_valid = check_imports_and_one_function(args.pythonfile)
if is_valid:
    generate_py_file(args.pythonfile)
    print("Valid: file has imports and exactly one function")
else:
    print("Invalid: file must contain only imports and exactly one function")
