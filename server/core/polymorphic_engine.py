import hashlib
import random
import string
import ast
import builtins
from typing import Any, Dict, List, Optional

class PolymorphicEngine:
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(0, 2**32 - 1)
        self.random = random.Random(self.seed)
        self._cache = {}

    def mutate(self, source_code: str) -> str:
        if source_code in self._cache:
            return self._cache[source_code]

        tree = ast.parse(source_code)
        transformer = PolymorphicTransformer(self.random)
        mutated_tree = transformer.visit(tree)
        mutated_code = ast.unparse(mutated_tree)

        self._cache[source_code] = mutated_code
        return mutated_code

    def mutate_file(self, input_path: str, output_path: str) -> None:
        with open(input_path, 'r', encoding='utf-8') as f:
            source = f.read()
        mutated = self.mutate(source)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(mutated)

    def _generate_fingerprint(self, code: str) -> str:
        return hashlib.sha256(code.encode('utf-8')).hexdigest()


class PolymorphicTransformer(ast.NodeTransformer):
    def __init__(self, rand: random.Random):
        self.rand = rand
        self.name_mapping = {}
        self._builtins = set(dir(builtins))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if node.name.startswith('__') and node.name.endswith('__'):
            return node
        if node.name in self._builtins:
            return node

        new_name = self._random_name('func')
        self.name_mapping[node.name] = new_name
        node.name = new_name
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        return self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        if node.name in self._builtins:
            return node
        new_name = self._random_name('class')
        self.name_mapping[node.name] = new_name
        node.name = new_name
        self.generic_visit(node)
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id in self.name_mapping:
            node.id = self.name_mapping[node.id]
        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        if node.arg in self._builtins:
            return node
        if node.arg not in self.name_mapping:
            self.name_mapping[node.arg] = self._random_name('arg')
        node.arg = self.name_mapping[node.arg]
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        return node

    def _random_name(self, prefix: str = 'var') -> str:
        length = self.rand.randint(8, 12)
        chars = string.ascii_lowercase + string.digits
        name = prefix + '_' + ''.join(self.rand.choices(chars, k=length))
        return name

    def visit_Str(self, node: ast.Str) -> ast.Str:
        return node

    def visit_Num(self, node: ast.Num) -> ast.Num:
        return node

    def visit_Expr(self, node: ast.Expr) -> ast.Expr:
        if self.rand.random() < 0.1:
            pass
        return node

    def _create_junk_expr(self) -> ast.Expr:
        var_name = self._random_name('tmp')
        target = ast.Name(id=var_name, ctx=ast.Store())
        value = ast.BinOp(
            left=ast.Name(id=var_name, ctx=ast.Load()),
            op=ast.Mult(),
            right=ast.Constant(value=1)
        )
        assign = ast.Assign(targets=[target], value=value)
        return assign

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        return node

    def visit_List(self, node: ast.List) -> ast.List:
        return node

    def visit_Tuple(self, node: ast.Tuple) -> ast.Tuple:
        return node

    def visit_Dict(self, node: ast.Dict) -> ast.Dict:
        return node


if __name__ == '__main__':
    sample_code = '''
def calculate_sum(a, b):
    result = a + b
    return result

class DataProcessor:
    def __init__(self, factor):
        self.factor = factor

    def multiply(self, value):
        return value * self.factor
'''
    engine = PolymorphicEngine(seed=12345)
    mutated = engine.mutate(sample_code)
    print("Original:")
    print(sample_code)
    print("\nMutated:")
    print(mutated)