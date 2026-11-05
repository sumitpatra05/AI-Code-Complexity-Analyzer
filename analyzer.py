"""Static complexity analysis for Python source code (uses only the stdlib)."""
import ast
import math
from dataclasses import dataclass, asdict

FUNC_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
LOOP_TYPES = (ast.For, ast.AsyncFor, ast.While)


@dataclass
class FunctionReport:
    name: str
    line: int
    loc: int
    params: int
    cyclomatic: int
    cognitive: int
    max_nesting: int
    loop_depth: int
    time_estimate: str
    space_estimate: str
    grade: str


def grade_for(cc: int) -> str:
    if cc <= 5: return "A"
    if cc <= 10: return "B"
    if cc <= 20: return "C"
    if cc <= 30: return "D"
    return "F"


def _walk_no_nested(node):
    """Yield descendants without entering nested function/class bodies."""
    for child in ast.iter_child_nodes(node):
        yield child
        if not isinstance(child, FUNC_TYPES + (ast.ClassDef, ast.Lambda)):
            yield from _walk_no_nested(child)


def cyclomatic(fn) -> int:
    score = 1
    for n in _walk_no_nested(fn):
        if isinstance(n, (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While,
                          ast.ExceptHandler, ast.match_case)):
            score += 1
        elif isinstance(n, ast.BoolOp):
            score += len(n.values) - 1
        elif isinstance(n, ast.comprehension):
            score += 1 + len(n.ifs)
    return score


def cognitive(node, nesting=0) -> int:
    """Approximation of SonarSource cognitive complexity."""
    total = 0
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While,
                              ast.ExceptHandler, ast.match_case)):
            total += 1 + nesting + cognitive(child, nesting + 1)
        elif isinstance(child, ast.BoolOp):
            total += 1 + cognitive(child, nesting)
        elif isinstance(child, FUNC_TYPES + (ast.Lambda,)):
            total += cognitive(child, nesting + 1)
        else:
            total += cognitive(child, nesting)
    return total


def max_depth(node, types, depth=0) -> int:
    best = depth
    for child in ast.iter_child_nodes(node):
        d = depth + 1 if isinstance(child, types) else depth
        best = max(best, max_depth(child, types, d))
    return best


def _calls(fn):
    names = []
    for n in _walk_no_nested(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                names.append(f.id)
            elif isinstance(f, ast.Attribute):
                names.append(f.attr)
    return names


def _sorts_inside_loop(fn) -> bool:
    """Return True when a sorting call occurs inside a loop/comprehension."""
    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.loop_depth = 0
            self.found = False

        def visit_For(self, node):
            self.loop_depth += 1
            self.generic_visit(node)
            self.loop_depth -= 1

        visit_AsyncFor = visit_For
        visit_While = visit_For

        def visit_comprehension(self, node):
            self.loop_depth += 1
            self.generic_visit(node)
            self.loop_depth -= 1

        def visit_Call(self, node):
            name = node.func.id if isinstance(node.func, ast.Name) else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
            if name in ("sorted", "sort") and self.loop_depth > 0:
                self.found = True
            self.generic_visit(node)

    v = Visitor()
    v.visit(fn)
    return v.found


def estimate_time(fn, loop_depth: int) -> str:
    """Heuristic time-complexity estimate; static AST analysis cannot prove Big-O."""
    calls = _calls(fn)
    self_calls = calls.count(fn.name)
    sorts = any(c in ("sorted", "sort") for c in calls)
    sort_in_loop = _sorts_inside_loop(fn)

    if self_calls >= 2:
        return "O(2^n) approx - branching recursion (verify; memoization may reduce it)"
    if self_calls == 1:
        if loop_depth:
            return f"O(n) recursion depth + O(n^{loop_depth}) loop work (approx)"
        return "O(n) recursion depth (approx)"
    if loop_depth:
        base = f"O(n^{loop_depth})"
        if sort_in_loop:
            return f"{base} * O(n log n) - sort inside loop (approx)"
        if sorts:
            return f"{base} + O(n log n) - separate sort (approx)"
        return f"{base} (approx)"
    return "O(n log n) - sorting detected (approx)" if sorts else "O(1) - no dominant loop detected"



def estimate_space(fn) -> str:
    """Estimate auxiliary space from obvious allocations and recursion (heuristic)."""
    allocations = []
    for n in _walk_no_nested(fn):
        if isinstance(n, (ast.List, ast.ListComp, ast.Set, ast.SetComp, ast.Dict, ast.DictComp, ast.GeneratorExp)):
            allocations.append(type(n).__name__)
        elif isinstance(n, ast.Call):
            name = n.func.id if isinstance(n.func, ast.Name) else (n.func.attr if isinstance(n.func, ast.Attribute) else "")
            if name in {"list", "dict", "set", "bytearray", "deque", "zeros", "empty"}:
                allocations.append(name)
    recursive = fn.name in _calls(fn)
    if allocations and recursive:
        return "O(n) or more - collection allocation plus recursion (approx)"
    if allocations:
        return "O(n) - collection allocation detected (approx); size depends on input"
    if recursive:
        return "O(n) - recursion stack (approx)"
    return "O(1) - no input-sized allocation detected (approx)"


def analyze_function(fn) -> FunctionReport:
    args = fn.args
    params = len(args.posonlyargs) + len(args.args) + len(args.kwonlyargs)
    params += bool(args.vararg) + bool(args.kwarg)
    loop_types = LOOP_TYPES + (ast.comprehension,)
    ld = max_depth(fn, loop_types)
    cc = cyclomatic(fn)
    return FunctionReport(
        name=fn.name, line=fn.lineno,
        loc=(fn.end_lineno or fn.lineno) - fn.lineno + 1,
        params=params, cyclomatic=cc, cognitive=cognitive(fn),
        max_nesting=max_depth(fn, (ast.If, ast.For, ast.AsyncFor, ast.While,
                                   ast.Try, ast.With, ast.AsyncWith)),
        loop_depth=ld, time_estimate=estimate_time(fn, ld),
        space_estimate=estimate_space(fn), grade=grade_for(cc),
    )


def maintainability_index(tree, loc: int, avg_cc: float) -> float:
    nodes = list(ast.walk(tree))
    vocab = len({type(n).__name__ for n in nodes}) + len(
        {n.id for n in nodes if isinstance(n, ast.Name)})
    volume = max(1, len(nodes)) * math.log2(max(2, vocab))
    mi = (171 - 5.2 * math.log(max(volume, 1)) - 0.23 * avg_cc
          - 16.2 * math.log(max(loc, 1))) * 100 / 171
    return round(max(0.0, min(100.0, mi)), 1)


def suggestions(funcs, mi):
    out = []
    for f in funcs:
        if f.cyclomatic > 10:
            out.append(f"{f.name}() (line {f.line}): cyclomatic complexity {f.cyclomatic}. Split into smaller functions or use early returns.")
        if f.cognitive > 15:
            out.append(f"{f.name}(): cognitive complexity {f.cognitive} is hard to read. Reduce nesting and extract helpers.")
        if f.max_nesting > 3:
            out.append(f"{f.name}(): nesting depth {f.max_nesting}. Use guard clauses to flatten it.")
        if f.params > 5:
            out.append(f"{f.name}(): {f.params} parameters. Group them into a dataclass or object.")
        if f.loc > 50:
            out.append(f"{f.name}(): {f.loc} lines long. Break it into single-purpose functions.")
        if f.loop_depth >= 3:
            out.append(f"{f.name}(): {f.loop_depth} nested loops ({f.time_estimate}). Look for a dict/set lookup or a better algorithm.")
        if "O(2^n)" in f.time_estimate:
            out.append(f"{f.name}(): branching recursion. Add memoization (functools.lru_cache) or iterate.")
    if mi < 40:
        out.append(f"Maintainability index is low ({mi}/100). Consider refactoring before adding features.")
    return out or ["No major complexity issues found."]


def analyze_code(source: str, language: str = "python") -> dict:
    """Analyze source in Python, C, or Java. C/Java use heuristic static analysis."""
    language = (language or "python").lower()
    if language in ("c", "java"):
        from polyglot_analyzer import analyze_polyglot
        return analyze_polyglot(source, language)
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error on line {e.lineno}: {e.msg}", "language": "Python"}
    funcs = [analyze_function(n) for n in ast.walk(tree) if isinstance(n, FUNC_TYPES)]
    funcs.sort(key=lambda f: f.line)
    loc = len([l for l in source.splitlines() if l.strip() and not l.strip().startswith("#")])
    avg_cc = sum(f.cyclomatic for f in funcs) / len(funcs) if funcs else 1
    module_cc = cyclomatic(tree) if not funcs else None
    mi = maintainability_index(tree, loc, avg_cc)
    return {
        "summary": {
            "lines_of_code": loc,
            "functions": len(funcs),
            "avg_cyclomatic": round(avg_cc, 2) if funcs else module_cc,
            "max_cyclomatic": max((f.cyclomatic for f in funcs), default=module_cc),
            "total_cognitive": sum(f.cognitive for f in funcs),
            "maintainability_index": mi,
            "overall_grade": grade_for(round(avg_cc)),
        },
        "functions": [asdict(f) for f in funcs],
        "suggestions": suggestions(funcs, mi),
    }
