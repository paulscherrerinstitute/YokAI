from functools import cache
from importlib.resources import files

from logzero import logger as log

from ..files import read_markdown

from .discovery import object_list
from .inputsize import cut_from_top, limit_recent_inputs
from .mood import format_mood


INSTRUCTIONS = read_markdown(files(__package__) / "instructions.md")

OBJECT_LIST_HEADING = "# Object list: the variables in the user's session\n\n"
CURRENT_INPUT_HEADING = "The IPython input the question was asked in:"
RECENT_INPUTS_HEADING = "Recent IPython inputs, oldest first:"


def make_system_prompt(namespace, hidden, plugins, mood):
    """
    Rebuilt for every question:
    Core instructions, plugins paragraphs, the mood, plugins FAQs, and the object list.
    The mood is last in the instructions, so that its guard can refer to all above it.
    The object list is last, so the static sections before it stay in vLLM's prefix cache.
    """
    paragraphs = [p.paragraph for p in plugins]
    mood_paragraph = format_mood(mood)
    faqs = [read_faq(p.faq_file) for p in plugins if p.faq_file is not None]
    objects = OBJECT_LIST_HEADING + object_list(namespace, hidden, plugins)
    sections = [INSTRUCTIONS, *paragraphs, mood_paragraph, *faqs, objects]
    content = "\n".join(s for s in sections if s is not None)
    return {"role": "system", "content": content}


@cache
def read_faq(path):
    try:
        return read_markdown(path)
    except FileNotFoundError:
        log.warning(f"YokAI works without the FAQ {path}, as it is missing")
        return None


def make_user_message(question, unanswered_note, current_input, new_inputs):
    """
    The question, followed by
    the note on the questions left unanswered, if any,
    the rest of the current input, if any,
    and the most recent of the inputs since the previous question.
    """
    content = [question]
    if unanswered_note:
        content.append(unanswered_note)
    if current_input:
        content.append(format_current_input(cut_from_top(current_input)))
    if new_inputs:
        content.append(format_recent_inputs(limit_recent_inputs(new_inputs)))
    content = "\n\n".join(content)
    return {"role": "user", "content": content}


def format_current_input(current_input):
    fence = python_fence(current_input)
    return "\n\n".join([CURRENT_INPUT_HEADING, fence])


def format_recent_inputs(inputs):
    """
    One fence per input, so that the inputs stay apart even if they contain blank lines.
    """
    fences = [python_fence(i) for i in inputs]
    return "\n\n".join([RECENT_INPUTS_HEADING, *fences])


def python_fence(code):
    return f"```python\n{code}\n```"


