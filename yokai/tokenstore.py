import getpass
import json
import os
from pathlib import Path

from .defaults import DEFAULT_URL


DIRECTORY_MODE = 0o700
FILE_MODE = 0o600


def read_token(url):
    """
    Returns the token stored for url, exactly as passed to YokAI, or None if there is none.
    """
    return read_tokens().get(url)


def store_token(url=DEFAULT_URL):
    """
    Prompts for the server's token without echoing and stores it for url,
    in a file only the user can read, keeping the other URLs' tokens.
    An empty entry or Ctrl-C stores nothing.
    """
    try:
        token = getpass.getpass(prompt=f"Please enter YokAI's token for {url}: ").strip()
    except KeyboardInterrupt:
        print()
        return
    if not token:
        return
    update_token(url, token)


def update_token(url, token):
    tokens = read_tokens()
    tokens[url] = token
    write_tokens(tokens)


def remove_token(url=DEFAULT_URL):
    """
    Removes the token stored for url, keeping the other URLs' tokens.
    """
    tokens = read_tokens()
    if url not in tokens:
        print(f"YokAI has no token stored for {url}.")
        return
    del tokens[url]
    write_tokens(tokens)


def read_tokens():
    """
    Returns the stored tokens by URL.
    A file not holding a JSON object (e.g. the single token stored before) holds none.
    """
    try:
        tokens = json.loads(token_path().read_bytes())
    # ValueError: neither JSON nor text
    except (FileNotFoundError, ValueError):
        return {}
    if not isinstance(tokens, dict):
        return {}
    return tokens


def write_tokens(tokens):
    path = token_path()
    directory = path.parent
    directory.mkdir(mode=DIRECTORY_MODE, parents=True, exist_ok=True)
    # the mode is set again, as the umask or an existing directory can widen it
    directory.chmod(DIRECTORY_MODE)
    # the mode is set before writing, so that the tokens are never in a file others can read
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, FILE_MODE)
    os.fchmod(fd, FILE_MODE)
    with open(fd, "w", encoding="utf-8") as f:
        json.dump(tokens, f)


def token_path():
    config_home = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    return Path(config_home).expanduser() / "yokai" / "token"


