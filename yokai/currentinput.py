import ast


ASK_METHOD = "ask"

# magics, e.g. %yokai and %%yokai, are in the input history as calls of these
MAGIC_CALLS = ("run_line_magic", "run_cell_magic")


def without_asking_statements(source, magic_names):
    """
    An input asked from the current input or a recent one,
    without the top-level statements that call ask or one of the magics,
    cut by their line ranges, so that the rest keeps its text and comments.
    None if nothing remains.
    An input that does not parse is kept whole.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    asking_lines = set()
    for statement in tree.body:
        if is_asking_statement(statement, magic_names):
            asking_lines.update(range(statement.lineno, statement.end_lineno + 1))
    # split at "\n" only, as ast does: str.splitlines also splits at e.g. form feeds
    lines = source.split("\n")
    kept = [line for number, line in enumerate(lines, 1) if number not in asking_lines]
    rest = "\n".join(kept).strip("\n")
    return rest if rest.strip() else None


def is_asking_statement(statement, magic_names):
    return any(is_asking_call(node, magic_names) for node in ast.walk(statement))


def is_asking_call(node, magic_names):
    """
    A call of a method named ask, as ai.ask(…), or of a magic named in magic_names.
    The object it is called on is not checked, so that reading the input reads no object.
    """
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    method = node.func.attr
    if method == ASK_METHOD:
        return True
    return method in MAGIC_CALLS and names_magic(node.args, magic_names)


def names_magic(args, magic_names):
    first = args[0] if args else None
    return isinstance(first, ast.Constant) and first.value in magic_names


