import ast
import sys
def check_imports_and_one_function(file_path: str) -> bool:

    with open(file_path, "r") as f:
        source = f.read()

    # Parse into AST
    tree = ast.parse(source)

    func_count = 0

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            func_count += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            
            continue
        else:
            
            return False

    
    return func_count == 1


