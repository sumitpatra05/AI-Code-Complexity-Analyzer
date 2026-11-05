"""Lightweight C/Java static complexity analysis.

Important: this module is a heuristic analyzer, not a full compiler/parser.
It performs basic lexical validation so malformed C/Java code is rejected
instead of receiving a misleading complexity grade.
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def _strip_comments(code):
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
    code = re.sub(r'//[^\n]*', '', code)
    return code


def _validate_delimiters(code):
    """Catch common structural syntax errors without pretending to be a compiler."""
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    in_string = None
    escape = False
    i = 0
    while i < len(code):
        ch = code[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == in_string:
                in_string = None
            i += 1
            continue
        if ch in ('"', "'"):
            in_string = ch
        elif ch in '([{':
            stack.append(ch)
        elif ch in ')]}':
            if not stack or stack[-1] != pairs[ch]:
                return False, f"Unexpected '{ch}' near character {i + 1}."
            stack.pop()
        i += 1
    if in_string:
        return False, "Unterminated string literal."
    if stack:
        return False, f"Unclosed '{stack[-1]}'."
    return True, None


def _compiler_syntax_check(code, language):
    """Use an installed compiler when available; otherwise return None.

    This is optional so the project still runs on machines without GCC/JDK.
    """
    if language == 'c':
        compiler = shutil.which('gcc') or shutil.which('clang')
        if not compiler:
            return None
        suffix = '.c'
        cmd = [compiler, '-fsyntax-only']
    else:
        compiler = shutil.which('javac')
        if not compiler:
            return None
        suffix = '.java'
        cmd = [compiler, '-Xlint:none']

    try:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / ('Main' + suffix)
            path.write_text(code, encoding='utf-8')
            if language == 'java':
                # javac requires a public class to match the filename. If the
                # submitted code has a different public class, skip compiler
                # validation and rely on lexical checks rather than rejecting it.
                m = re.search(r'\bpublic\s+class\s+([A-Za-z_]\w*)', code)
                if m and m.group(1) != 'Main':
                    return None
            result = subprocess.run(cmd + [str(path)], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True, None
            msg = (result.stderr or result.stdout).strip().splitlines()
            return False, msg[0] if msg else 'Compiler reported a syntax error.'
    except (OSError, subprocess.SubprocessError):
        return None


def validate_source(source, language):
    clean = _strip_comments(source)
    ok, err = _validate_delimiters(clean)
    if not ok:
        return False, err
    compiler_result = _compiler_syntax_check(clean, language)
    if compiler_result is not None:
        return compiler_result
    return True, None


def _grade(cc):
    if cc <= 5: return 'A'
    if cc <= 10: return 'B'
    if cc <= 20: return 'C'
    if cc <= 30: return 'D'
    return 'F'


def _functions(code, language):
    if language == 'java':
        pat = re.compile(r'(?m)^\s*(?:(?:public|private|protected|static|final|synchronized|abstract|native|strictfp)\s+)*(?:[\w<>\[\], ?]+)\s+(\w+)\s*\(([^)]*)\)\s*\{')
    else:
        pat = re.compile(r'(?m)^\s*(?:[\w\*]+\s+)+([A-Za-z_]\w*)\s*\(([^;{}]*)\)\s*\{')
    out = []
    for m in pat.finditer(code):
        start = m.start()
        brace = code.find('{', m.start(), m.end())
        depth = 0; end = None
        for i in range(brace, len(code)):
            if code[i] == '{': depth += 1
            elif code[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1; break
        if end is None:
            end = len(code)
        line = code.count('\n', 0, start) + 1
        body = code[brace:end]
        name = m.group(1)
        # Do not mistake control statements such as `for (...) {` for functions.
        if name in {'if', 'for', 'while', 'switch', 'catch', 'foreach'}:
            continue
        params = [p.strip() for p in m.group(2).split(',') if p.strip()]
        out.append((name, line, body, len(params)))
    return out


def _complexity(body, function_name):
    decisions = len(re.findall(r'\b(if|for|while|case|catch|switch)\b', body))
    decisions += len(re.findall(r'&&|\|\|', body))
    cc = 1 + decisions
    cognitive = decisions
    max_nesting = 0; depth = 0
    for ch in body:
        if ch == '{':
            depth += 1; max_nesting = max(max_nesting, depth)
        elif ch == '}': depth = max(0, depth - 1)
    loops = len(re.findall(r'\b(for|while)\b', body))
    # Count loop nesting approximately by brace depth at each loop token.
    loop_depth = 0
    current = 0
    tokens = re.finditer(r'\b(for|while)\b|[{}]', body)
    for m in tokens:
        token = m.group(0)
        if token == '{':
            current += 1
        elif token == '}':
            current = max(0, current - 1)
        elif current > 0:
            loop_depth = max(loop_depth, current)
    sorts = bool(re.search(r'\b(sort|Arrays\.sort|Collections\.sort|qsort)\s*\(', body))
    if loops >= 2:
        time = f'O(n^{min(loops, 3)}) approx - nested loops (heuristic)'
    elif loops == 1:
        time = 'O(n) approx - loop detected (heuristic)'
    elif sorts:
        time = 'O(n log n) approx - sorting detected (heuristic)'
    else:
        time = 'O(1) approx - no dominant loop detected'
    # Approximate auxiliary space: explicit arrays/containers and recursion.
    alloc = bool(re.search(r'\b(new\s+\w+\s*\[|\w+\s+\w+\s*\[\s*\w*\s*\]|malloc\s*\(|calloc\s*\(|realloc\s*\()', body))
    recursive = bool(re.search(r'\b' + re.escape(function_name) + r'\s*\(', body))
    space = 'O(n) - array/heap allocation detected (approx)' if alloc else ('O(n) - possible recursion stack (approx)' if recursive and loops == 0 else 'O(1) - no input-sized allocation detected (approx)')
    return cc, cognitive, max_nesting, min(loop_depth, 3), time, space


def analyze_polyglot(source, language):
    clean = _strip_comments(source)
    valid, error = validate_source(source, language)
    if not valid:
        return {
            'error': f"Syntax error: {error}",
            'language': language.title(),
            'syntax_valid': False,
        }

    funcs = _functions(clean, language)
    reports = []
    for name, line, body, params in funcs:
        cc, cog, nesting, loop_depth, time, space = _complexity(body, name)
        loc = body.count('\n') + 1
        reports.append({
            'name': name, 'line': line, 'loc': loc, 'params': params,
            'cyclomatic': cc, 'cognitive': cog, 'max_nesting': nesting,
            'loop_depth': loop_depth, 'time_estimate': time, 'space_estimate': space, 'grade': _grade(cc)
        })

    loc = len([x for x in clean.splitlines() if x.strip()])
    avg = round(sum(x['cyclomatic'] for x in reports) / len(reports), 2) if reports else None
    max_cc = max((x['cyclomatic'] for x in reports), default=None)
    suggestions = []
    for f in reports:
        if f['cyclomatic'] > 10: suggestions.append(f"{f['name']}(): high cyclomatic complexity ({f['cyclomatic']}). Split conditions into smaller methods.")
        if f['max_nesting'] > 4: suggestions.append(f"{f['name']}(): nesting depth {f['max_nesting']}. Use guard clauses/helper methods.")
        if f['loop_depth'] >= 2: suggestions.append(f"{f['name']}(): nested loops detected. Consider a better data structure or algorithm.")
        if f['params'] > 5: suggestions.append(f"{f['name']}(): many parameters ({f['params']}). Group related values into an object/struct.")

    return {
        'summary': {
            'language': language.title(), 'lines_of_code': loc,
            'functions': len(reports), 'avg_cyclomatic': avg,
            'max_cyclomatic': max_cc, 'total_cognitive': sum(x['cognitive'] for x in reports),
            'maintainability_index': None,
            # Grade is deliberately complexity-only, not correctness.
            'overall_grade': _grade(round(avg)) if avg is not None else 'N/A',
            'syntax_valid': True,
            'analysis_note': 'C/Java use heuristic static analysis. Time and space estimates are approximations, not formal proofs. The grade measures complexity, not correctness.'
        },
        'functions': reports,
        'suggestions': suggestions or ['No major heuristic complexity issues found.'],
    }
