from .notebook import NotebookFrontend
from .terminal import TerminalFrontend


# ipykernel's shell, recognized by name, so that the core needs no ipykernel
NOTEBOOK_SHELL_NAME = "ZMQInteractiveShell"


def choose_frontend(shell):
    """
    Chooses how YokAI shows its output from the shell's class.
    A Jupyter kernel's shell gets the notebook frontend,
    any other shell or none, the terminal frontend.
    A frontend has four operations:
    - progress() (a context manager for the whole question)
    - show_tool_call(text)
    - show_answer(text)
    - show_error(text)
    """
    shell_classes = type(shell).__mro__
    if any(c.__name__ == NOTEBOOK_SHELL_NAME for c in shell_classes):
        return NotebookFrontend()
    return TerminalFrontend()


