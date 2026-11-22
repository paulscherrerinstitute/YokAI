from IPython import get_ipython
from openai import OpenAIError

from .client import MISSING_TOKEN_MESSAGE, describe_error, make_client, request_answer, without_thinking
from .currentinput import without_asking_statements
from .frontend import choose_frontend
from .magic import register_magic
from .prompt import make_system_prompt, make_user_message


DEFAULT_URL = "https://ai.psi.ch/api/"
DEFAULT_MODEL = "Qwen3.8-27B"

INTERRUPTED_MESSAGE = "YokAI was interrupted; the conversation is unchanged."


class YokAI:

    def __init__(self, url=DEFAULT_URL, model=DEFAULT_MODEL, *, plugins=(), shell=None, client=None):
        self.url = url
        self.model = model
        self.plugins = tuple(plugins)
        if client is None:
            client = make_client(url)
        self.client = client
        if shell is None:
            shell = get_ipython()
        self.shell = shell
        self.frontend = choose_frontend(shell)
        if shell is not None: # no shell outside IPython
            register_magic(shell, self)
        self.conversation = []
        self.last = []
        # In[0] is always "", so the first question gets the inputs from In[1] on
        self.previous_question_at = 0


    def ask(self, question):
        frontend = self.frontend

        if self.client is None:
            frontend.show_error(MISSING_TOKEN_MESSAGE)
            return

        shell = self.shell
        namespace = shell.user_ns
        hidden = shell.user_ns_hidden
        system_prompt = make_system_prompt(namespace, hidden, self.plugins)
        inputs = namespace["In"]

        # IPython adds an input to In before running it: the last is this question's
        asked_at = len(inputs) - 1
        current_input = without_asking_statements(inputs[asked_at])
        new_inputs = read_new_inputs(inputs, self.previous_question_at, asked_at)

        # set before the request, so that it holds a failed question, too
        self.last = [make_user_message(question, current_input, new_inputs)]
        earlier_messages = [system_prompt, *self.conversation]

        try:
            with frontend.progress():
                answer = self._request_answer(earlier_messages)
        except QuestionFailed as exc:
            frontend.show_error(str(exc))
            return
        except KeyboardInterrupt:
            frontend.show_error(INTERRUPTED_MESSAGE)
            return

        # the question joins the conversation only once its answer is complete
        self.conversation.extend(without_thinking(self.last))
        self.previous_question_at = asked_at
        frontend.show_answer(answer["content"])


    def _request_answer(self, earlier_messages):
        """
        Raises QuestionFailed with a description of the request error.
        Describing the error can read the model list, so ctrl-c must be caught around it.
        """
        try:
            return request_answer(
                self.client,
                self.model,
                earlier_messages,
                self.last,
                self.shell.user_ns,
                self.plugins,
                self.frontend
            )
        except OpenAIError as exc:
            description = describe_error(exc, self.client, self.url, self.model)
            raise QuestionFailed(description) from exc


    def reset(self):
        self.conversation = []



class QuestionFailed(Exception):
    """
    A question whose request failed, described with the cause and the fix.
    """



def read_new_inputs(inputs, previous_question_at, asked_at):
    """
    The inputs between the previous question and this one.
    A failed question asked again word for word is left out, so it is not sent twice.
    """
    question_input = inputs[asked_at]
    between = inputs[previous_question_at + 1:asked_at]
    return [i for i in between if i != question_input]


