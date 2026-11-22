import re
from tokenize import DEDENT, INDENT

from IPython.core.inputtransformer2 import make_tokens_by_line
from IPython.core.magic import no_var_expand


MAGIC_NAME = "yokai"

# %yokai followed by whitespace or nothing: %yokai? is IPython's help on the magic
MAGIC_LINE = re.compile(rf"(?P<indent>[ \t]*)%{MAGIC_NAME}(?P<question>[ \t].*)?")

MAGIC_USAGE = """\
Usage: %yokai <question>, or %%yokai with the question in the cell

Asks YokAI as ai.ask("<question>") does, without quotes:

    %yokai how do I wiggle the electrons?

For a question over several lines (e.g. with a pasted traceback):

    %%yokai why did this fail?
    <traceback>
"""


def register_magic(shell, ai):
    """
    Registers %yokai and %%yokai on the shell, answered by ai.
    Registering again replaces the magic, so the YokAI created last answers.
    """
    magic = make_magic(ai)
    shell.register_magic_function(magic, magic_kind="line_cell", magic_name=MAGIC_NAME)
    transformers = shell.input_transformers_cleanup
    if rewrite_magic_lines not in transformers:
        transformers.append(rewrite_magic_lines)


def make_magic(ai):
    # not expanded: IPython would format session objects for {expr} and $name
    @no_var_expand
    def yokai(line, cell=None):
        text = line if cell is None else f"{line}\n{cell}"
        question = text.strip()
        if not question:
            ai.frontend.show_error(MAGIC_USAGE)
            return
        ai.ask(question)

    yokai.__doc__ = MAGIC_USAGE
    return yokai


def rewrite_magic_lines(lines):
    """
    Cleanup input transformer:
    Rewrites %yokai lines into the magic's call before IPython's help syntax sees them,
    which would turn a question ending in `word?` into help on word.
    Cell magics are left alone, as their body is the question.
    """
    if lines and lines[0].startswith("%%"):
        return lines
    lines = list(lines)
    while True:
        index = find_magic_line(lines)
        if index is None:
            break
        lines[index] = rewrite_magic_line(lines[index])
    return lines


def find_magic_line(lines):
    """
    The index of the first %yokai line that starts a statement,
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
        if index < len(lines) and match_magic_line(lines[index]):
            return index
    return None


def match_magic_line(line):
    text = line.rstrip("\r\n")
    return MAGIC_LINE.fullmatch(text)


def rewrite_magic_line(line):
    match = match_magic_line(line)
    ending = line[match.end():]
    indent = match["indent"]
    question = match["question"] or ""
    question = question.strip()
    return f"{indent}get_ipython().run_line_magic({MAGIC_NAME!r}, {question!r}){ending}"


