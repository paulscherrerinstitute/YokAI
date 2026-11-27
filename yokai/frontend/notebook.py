import re
from contextlib import contextmanager
from uuid import uuid4

from IPython import display

from .common import PROGRESS_STATUS


MIN_FENCE_LENGTH = 3


class NotebookFrontend:
    """
    Shows YokAI's output in a notebook cell's output with IPython.display:
    No animation and no threads, as the kernel sends each update itself.
    """

    def __init__(self):
        self.progress_area = None

    @contextmanager
    def progress(self):
        self.progress_area = ProgressArea()
        try:
            yield
        finally:
            self.progress_area.end()
            self.progress_area = None

    def show_tool_call(self, text):
        # called only inside progress(), so progress_area is set
        self.progress_area.add_tool_call(text)

    def show_answer(self, text):
        display.display(display.Markdown(text))

    def show_error(self, text):
        text_block = make_text_block(text)
        display.display(display.Markdown(text_block))



class ProgressArea:
    """
    One output area, updated in place through its display ID:
    The status line above the tool-call lines while the question runs,
    only the tool-call lines once it ends.
    """

    def __init__(self):
        self.display_id = uuid4().hex
        self.tool_call_lines = []
        status = as_plain_text([PROGRESS_STATUS])
        display.display(status, display_id=self.display_id)

    def add_tool_call(self, text):
        self.tool_call_lines.append(text)
        self.show([PROGRESS_STATUS, *self.tool_call_lines])

    def end(self):
        self.show(self.tool_call_lines)

    def show(self, lines):
        text = as_plain_text(lines)
        display.update_display(text, display_id=self.display_id)



def as_plain_text(lines):
    text = "\n".join(lines)
    return display.Pretty(text)


def make_text_block(text):
    """
    Markdown showing text exactly as the terminal does.
    As Markdown, it would lose line breaks and anything taken for HTML (<question>).
    The fence is longer than any run of backticks in text, so none of them closes it.
    """
    backtick_runs = re.findall("`+", text)
    lengths = (len(r) for r in backtick_runs)
    longest_run = max(lengths, default=0)
    fence = "`" * max(MIN_FENCE_LENGTH, longest_run + 1)
    body = text.rstrip("\n")
    return f"{fence}text\n{body}\n{fence}"


