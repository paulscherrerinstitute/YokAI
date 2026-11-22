from rich.console import Console
from rich.markdown import CodeBlock, Markdown
from rich.syntax import Syntax

from .common import PROGRESS_STATUS


class TerminalFrontend:
    """
    Shows YokAI's output on the terminal using rich.
    A spinner while a question runs, copy-paste-safe code blocks in the answer.
    """

    def __init__(self):
        self.console = Console()

    def progress(self):
        return self.console.status(PROGRESS_STATUS)

    def show_tool_call(self, text):
        self.console.print(text, style="dim", markup=False, highlight=False)

    def show_answer(self, text):
        md = CopyPasteSafeMarkdown(text)
        self.console.print(md, soft_wrap=True)

    def show_error(self, text):
        self.console.print(text, style="red", markup=False, highlight=False)



class CopyPasteSafeCodeBlock(CodeBlock):
    """
    A code block that copies into IPython exactly as written.
    On the terminal's background, without wrapping and without padding.
    The lexer comes from the fence's info string, falling back to plain text.
    """

    def __rich_console__(self, console, options):
        code = str(self.text).rstrip()
        yield Syntax(code, self.lexer_name, theme=self.theme, background_color="default")



class CopyPasteSafeMarkdown(Markdown):
    """
    Markdown whose code blocks are copy-paste safe.
    """

    elements = Markdown.elements | {
        "fence": CopyPasteSafeCodeBlock,
        "code_block": CopyPasteSafeCodeBlock
    }


