import getpass
import os
from pathlib import Path


STORE_TOKEN_HINT = "from yokai import store_token; store_token()"
TOKEN_PROMPT = "Please enter YokAI's token for the server: "

DIRECTORY_MODE = 0o700
FILE_MODE = 0o600


def store_token():
    """
    Prompts for the token without echoing and stores it in a file only the user can read.
    An empty entry or Ctrl-C stores nothing.
    """
    try:
        token = getpass.getpass(prompt=TOKEN_PROMPT).strip()
    except KeyboardInterrupt:
        print()
        return
    if not token:
        return
    write_token(token)


def write_token(token):
    path = token_path()
    directory = path.parent
    directory.mkdir(mode=DIRECTORY_MODE, parents=True, exist_ok=True)
    # the mode is set again, as the umask or an existing directory can widen it
    directory.chmod(DIRECTORY_MODE)
    # the mode is set before writing, so that the token is never in a file others can read
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, FILE_MODE)
    os.fchmod(fd, FILE_MODE)
    with open(fd, "w", encoding="utf-8") as f:
        f.write(token)


def read_token():
    """
    Returns the stored token or None if there is none.
    """
    try:
        token = token_path().read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    return token or None


def token_path():
    config_home = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    return Path(config_home).expanduser() / "yokai" / "token"


