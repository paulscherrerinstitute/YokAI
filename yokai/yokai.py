from IPython import get_ipython
from openai import OpenAIError

from .briefing import (
    INTERRUPTED_REASON,
    failed_reason,
    format_mood,
    make_system_prompt,
    make_unanswered_note,
    make_user_message,
    read_current_input,
    read_recent_inputs,
    record_asked_from
)
from .client import AuthorizedClient, describe_error, make_client, request_answer, without_thinking
from .defaults import DEFAULT_MAGIC_NAME, DEFAULT_MODEL, DEFAULT_URL
from .frontend import choose_frontend
from .magic import check_magic_name, register_magic
from .tokenstore import read_token


INTERRUPTED_MESSAGE = "YokAI was interrupted; the conversation is unchanged."


class YokAI:

    def __init__(self, url=DEFAULT_URL, model=DEFAULT_MODEL, *, plugins=(), magic=DEFAULT_MAGIC_NAME, mood=None):
        # checks first, so that a bad name or mood registers nothing and builds no client
        check_magic_name(magic)
        format_mood(mood)
        self.url = url
        self.model = model
        self.plugins = tuple(plugins)
        self.mood = mood
        self.client = make_client(url)
        shell = get_ipython()
        self.shell = shell
        self.frontend = choose_frontend(shell)
        register_magic(shell, self, magic)
        self.conversation = []
        self.last = []
        self.unanswered = []
        # In[0] is always "", so the first question gets the inputs from In[1] on
        self.previous_question_at = 0


    def ask(self, question):
        frontend = self.frontend
        shell = self.shell
        namespace = shell.user_ns
        hidden = shell.user_ns_hidden
        system_prompt = make_system_prompt(namespace, hidden, self.plugins, self.mood)
        inputs = namespace["In"]

        # IPython adds an input to In before running it: the last is this question's
        asked_at = len(inputs) - 1
        record_asked_from(shell, asked_at)
        current_input = read_current_input(shell, asked_at)
        recent_inputs = read_recent_inputs(shell, self.previous_question_at, asked_at)

        # set before the request, so that it holds a failed question, too
        unanswered_note = make_unanswered_note(self.unanswered, question)
        self.last = [make_user_message(question, unanswered_note, current_input, recent_inputs)]
        earlier_messages = [system_prompt, *self.conversation]

        try:
            with frontend.progress():
                answer = self._request_answer(earlier_messages)
        except QuestionFailed as exc:
            description = str(exc)
            reason = failed_reason(description)
            frontend.show_error(description)
            self.unanswered.append((question, reason))
            return
        except KeyboardInterrupt:
            frontend.show_error(INTERRUPTED_MESSAGE)
            self.unanswered.append((question, INTERRUPTED_REASON))
            return

        # the question joins the conversation only once its answer is complete
        self.conversation.extend(without_thinking(self.last))
        self.unanswered = []
        self.previous_question_at = asked_at
        frontend.show_answer(answer["content"])


    def _request_answer(self, earlier_messages):
        """
        Raises QuestionFailed with a description of the request error.
        Describing the error can read the model list, so ctrl-c must be caught around it.
        The token store is read at each question, so that the instance never holds a token
        and storing or removing one takes effect at the next question.
        """
        authorized_client = AuthorizedClient(self.client, read_token(self.url))
        try:
            return request_answer(
                authorized_client,
                self.model,
                earlier_messages,
                self.last,
                self.shell.user_ns,
                self.plugins,
                self.frontend
            )
        except OpenAIError as exc:
            description = describe_error(exc, authorized_client, self.url, self.model)
            raise QuestionFailed(description) from exc


    def reset(self):
        self.conversation = []
        self.unanswered = []



class QuestionFailed(Exception):
    """
    A question whose request failed, described with the cause and the fix.
    """


