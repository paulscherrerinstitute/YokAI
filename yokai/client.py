from openai import APIConnectionError, AuthenticationError, BadRequestError, Omit, OpenAI

from .tool import TOOL_SCHEMAS, format_tool_call, run_tool
from .utils import typename


CONTEXT_FULL_MESSAGE = """
The conversation is too long for the model's context window.
Start a new one with: ai.reset()
""".strip()

# both arrive as BadRequestError, told apart only by these markers in their detail
CONTEXT_FULL_MARKER = "maximum context length"
MODEL_NOT_SERVED_MARKER = "Model not found"

MODEL_NOT_SERVED_FIX = "Choose another model or server with model= or url= when creating YokAI."

# the model list only adds to an error message, so it must not keep one waiting
MODEL_LIST_TIMEOUT = 5 # seconds

TOKEN_MISSING_TEMPL = """
The server at {url} did not accept a request without a token. Store one for it with:
    from yokai import store_token
    store_token("{url}")
""".strip()

TOKEN_REJECTED_TEMPL = """
The server at {url} rejected YokAI's token. Store a valid one with:
    from yokai import store_token
    store_token("{url}")
or, if the server needs no token, remove it with:
    from yokai import remove_token
    remove_token("{url}")
""".strip()


def make_client(url):
    """
    Returns an OpenAI client that holds no (real) key.
    The openai package refuses to build a client without a key.
    The dummy key is never sent as every request sets the proper header or omits it entirely.
    """
    return OpenAI(base_url=url, api_key="dummy")



class AuthorizedClient:
    """
    The client as one question uses it:
    every request carries the question's Authorization header,
    Bearer <token>, or none at all without a token, so that the server decides.
    The header replaces the client's key, also through with_options.
    """

    def __init__(self, client, token):
        self.client = client
        self.has_token = token is not None
        # Omit() drops the header, so the dummy key is not sent
        authorization = Omit() if token is None else f"Bearer {token}"
        self.headers = {"Authorization": authorization}

    def create_completion(self, **request):
        completions = self.client.chat.completions
        return completions.create(**request, extra_headers=self.headers)

    def list_models(self, **options):
        configured_client = self.client.with_options(**options)
        return configured_client.models.list(extra_headers=self.headers)



def request_answer(client, model, earlier_messages, question_messages, namespace, plugins, frontend):
    """
    Runs the tool loop:
    requests again after each response with tool calls,
    running the calls against `namespace` with `plugins` and showing them on `frontend`,
    until the model answers.
    `earlier_messages` are the system prompt and the conversation.
    Appends the raw messages (thinking output included) to `question_messages`,
    so that they hold the tool calls and results even if a request fails,
    and returns the answer.
    """
    while True:
        message = request_message(client, model, earlier_messages + question_messages)
        question_messages.append(message)
        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return message
        for call in tool_calls:
            result = run_tool_call(namespace, plugins, frontend, call)
            question_messages.append(result)


def request_message(client, model, messages):
    """
    Returns the raw assistant message as a dict, thinking output included.
    The thinking output in messages is never sent back to the model.
    """
    messages = without_thinking(messages)
    response = client.create_completion(model=model, messages=messages, tools=TOOL_SCHEMAS)
    message = response.choices[0].message
    return message.model_dump(exclude_none=True)


def run_tool_call(namespace, plugins, frontend, call):
    function = call["function"]
    tool_name = function["name"]
    arguments = function["arguments"]
    frontend.show_tool_call(format_tool_call(tool_name, arguments))
    result = run_tool(namespace, tool_name, arguments, plugins)
    return {"role": "tool", "tool_call_id": call["id"], "content": result}


def without_thinking(messages):
    return [strip_thinking(m) for m in messages]


def strip_thinking(message):
    """
    Keeps only the content and tool calls of an assistant message,
    dropping the thinking output (i.e., vLLM's reasoning field).
    """
    if message["role"] != "assistant":
        return message
    stripped = {"role": "assistant", "content": message.get("content")}
    tool_calls = message.get("tool_calls")
    if tool_calls:
        stripped["tool_calls"] = tool_calls
    return stripped


def describe_error(exc, client, url, model):
    if isinstance(exc, AuthenticationError):
        return describe_authentication_error(client, url)
    if isinstance(exc, APIConnectionError): # includes timeouts (APITimeoutError)
        return f"YokAI cannot reach the server at {url}: {exc}"
    detail = read_error_detail(exc)
    if isinstance(exc, BadRequestError):
        if CONTEXT_FULL_MARKER in detail:
            return CONTEXT_FULL_MESSAGE
        if MODEL_NOT_SERVED_MARKER in detail:
            return describe_model_not_served(client, url, model)
    return f"{typename(exc)}: {detail}"


def describe_authentication_error(client, url):
    templ = TOKEN_REJECTED_TEMPL if client.has_token else TOKEN_MISSING_TEMPL
    return templ.format(url=url)


def read_error_detail(exc):
    """
    The server's gateway answers errors with {"detail": …},
    which the openai package leaves out of str(exc).
    """
    try:
        return str(exc.body["detail"])
    except (AttributeError, KeyError, TypeError):
        return str(exc)


def describe_model_not_served(client, url, model):
    lines = [f'The server at {url} does not serve the model "{model}".']
    served_models = read_served_models(client)
    if served_models:
        lines.append("It serves: " + ", ".join(served_models))
    lines.append(MODEL_NOT_SERVED_FIX)
    return "\n".join(lines)


def read_served_models(client):
    """
    Returns the IDs of the models the server serves or None if the model list cannot be read.
    """
    try:
        models = client.list_models(timeout=MODEL_LIST_TIMEOUT, max_retries=0)
        return [m.id for m in models]
    # the list only adds to the message: no failure may replace the error being reported
    except Exception:
        return None


