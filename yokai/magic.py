import re
from tokenize import DEDENT, INDENT

from IPython.core.inputtransformer2 import make_tokens_by_line
from IPython.core.magic import no_var_expand

from .defaults import DEFAULT_MAGIC_NAME


MAGIC_USAGE_TEMPL = """\
Usage: %{name} <question>, or %%{name} with the question in the cell

Asks YokAI as ai.ask("<question>") does, without quotes:

    %{name} how do I wiggle the electrons?

For a question over several lines (e.g. with a pasted traceback):

    %%{name} why did this fail?
    <traceback>
"""

#TODO: move to tests
# the usage of the default magic, %yokai
MAGIC_USAGE = MAGIC_USAGE_TEMPL.format(name=DEFAULT_MAGIC_NAME)


def check_magic_name(name):
    """
    Raises ValueError unless name is None (no magic) or a Python identifier,
    which IPython can call as %name
    """
    if name is None:
        return
    if isinstance(name, str) and name.isidentifier():
        return
    raise ValueError(f"the magic name must be a Python identifier or None, not {name!r}")


def register_magic(shell, ai, name):
    """
    Registers %name and %%name on the shell, answered by ai,
    and adds the name to the shell's rewriter.
    Registering again replaces the magic, so the YokAI created last answers.
    Does nothing without a shell (i.e., outside IPython) or without a name (magic disabled).
    """
    if shell is None or name is None:
        return
    magic = make_magic(ai, name)
    shell.register_magic_function(magic, magic_kind="line_cell", magic_name=name)
    rewriter = find_rewriter(shell)
    if rewriter is None:
        rewriter = MagicRewriter()
        shell.input_transformers_cleanup.append(rewriter)
    rewriter.names.add(name)


def registered_magic_names(shell):
    """
    The names of the magics registered on the shell, as held by its rewriter
    """
    rewriter = find_rewriter(shell)
    if rewriter is None:
        return frozenset()
    return frozenset(rewriter.names)


def find_rewriter(shell):
    transformers = shell.input_transformers_cleanup
    return next((t for t in transformers if isinstance(t, MagicRewriter)), None)


def make_magic(ai, name):
    usage = MAGIC_USAGE_TEMPL.format(name=name)

    # not expanded: IPython would format session objects for {expr} and $name
    @no_var_expand
    def magic(line, cell=None):
        text = line if cell is None else f"{line}\n{cell}"
        question = text.strip()
        if not question:
            ai.frontend.show_error(usage)
            return
        ai.ask(question)

    magic.__doc__ = usage
    return magic


class MagicRewriter:
    """
    Cleanup input transformer, one per shell, holding the names of its registered magics:
    Rewrites %name lines into the magic's call before IPython's help syntax sees them,
    which would turn a question ending in `word?` into help on word.
    Cell magics are left alone, as their body is the question.
    """

    def __init__(self):
        self.names = set()

    def __call__(self, lines):
        if not self.names or (lines and lines[0].startswith("%%")):
            return lines
        pattern = make_magic_line_pattern(self.names)
        lines = list(lines)
        while True:
            index = find_magic_line(lines, pattern)
            if index is None:
                break
            lines[index] = rewrite_magic_line(lines[index], pattern)
        return lines



def make_magic_line_pattern(names):
    """
    %name followed by whitespace or nothing, for any of the names:
    %name? is IPython's help on the magic, and %namex is another magic
    """
    alternatives = "|".join(re.escape(n) for n in sorted(names))
    name = rf"(?P<name>{alternatives})"
    return re.compile(rf"(?P<indent>[ \t]*)%{name}(?P<question>[ \t].*)?")


def find_magic_line(lines, pattern):
    """
    The index of the first %name line that starts a statement,
    so that a line inside a multi-line string is not taken.
    The lines are tokenized again after each rewrite,
    as a question's quotes (what's) stop the tokenizer until it is rewritten.
    """
    for tokens in make_tokens_by_line(lines):
        filtered = (t for t in tokens if t.type not in (INDENT, DEDENT))
        first = next(filtered, None)
        if first is None:
            continue
        index = first.start[0] - 1
        if index < len(lines) and match_magic_line(lines[index], pattern):
            return index
    return None


def match_magic_line(line, pattern):
    text = line.rstrip("\r\n")
    return pattern.fullmatch(text)


def rewrite_magic_line(line, pattern):
    match = match_magic_line(line, pattern)
    ending = line[match.end():]
    indent = match["indent"]
    name = match["name"]
    question = match["question"] or ""
    question = question.strip()
    return f"{indent}get_ipython().run_line_magic({name!r}, {question!r}){ending}"


