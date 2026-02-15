"""
Messaging system
"""

import logging
import re

from rich.logging import RichHandler

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()],
)
log.setLevel(logging.INFO)
raw_output = False


def set_logging_level(level: int):
    """Set logging level.

    Args:
        level (int): logging level.
    """
    if level == 0:
        log.setLevel(logging.FATAL)
    elif level == 1:
        log.setLevel(logging.ERROR)
    elif level == 2:
        log.setLevel(logging.WARNING)
    elif level == 3:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.DEBUG)


def set_raw_output(raw: bool):
    """Set raw output.

    Args:
        raw (bool): raw output.
    """
    global raw_output
    raw_output = raw


def align_centered(text: str, width: int) -> str:
    """Center align a text in a given width.

    Args:
        text (str): text to align.
        width (int): total width.

    Returns:
        str: centered text.
    """
    while len(text) < width:
        if (len(text)) % 2 == 0:
            text = " " + text
        else:
            text = text + " "
    return text


keywords = {
    "linux": "light_sea_green",
    "windows": "dark_cyan",
    "macos": "magenta",
    "shared": "dark_orange3",
    "static": "orange3",
    "header": "gold3",
    "gnu": "sandy_brown",
    "msvc": "wheat4",
    "clang": "yellow4",
    "x86_64": "pale_green3",
    "x86": "light_green",
    "aarch64": "sea_green3",
    "arm64": "chartreuse4",
    "armv7": "spring_green4",
    "any": "orange_red1 bold",
    "local": "cyan",
    "online": "green",
    "OFFLINE": "red bold",
    "srvs": "purple",
    "srv": "purple",
}

# Pre-compiled regex patterns
_re_bracket_open = re.compile(r"\[(?!\s)")
_re_bracket_close = re.compile(r"(?<!\s)\]")
_re_keyword_patterns = {
    keyword: (re.compile(re.escape(keyword), re.IGNORECASE), color)
    for keyword, color in keywords.items()
}
_re_default = re.compile(r"\*(\w+)")
_re_date = re.compile(
    r"\b(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([+-]\d{2}:\d{2}|Z)?\b"
)


def formatting(
    msg: str,
) -> str:
    """Format a message using rich formatting.

    Args:
        msg (str): message to format.

    Returns:
        str: formatted message.
    """
    # avoid rich misinterpretation of brackets
    msg = _re_bracket_open.sub("[ ", msg)
    msg = _re_bracket_close.sub(" ]", msg)

    # color keywords ignoring case
    for pattern, color in _re_keyword_patterns.values():
        msg = pattern.sub(lambda m, c=color: f"[{c}]{m.group()}[/]", msg)

    # format 'default' meaning words starting with * and followed by alphanumeric characters
    msg = _re_default.sub(lambda m: f"[bold blue]*{m.group(1)}[/]", msg)

    # formatting date from iso format to human-readable format
    msg = _re_date.sub(
        lambda m: f"[bold yellow]{m.group(1)}-{m.group(2)}-{m.group(3)}[/] "
        f"[bold green]{m.group(4)}:{m.group(5)}:{m.group(6)}[/]",
        msg,
    )

    return msg


def message(msg: str):
    """Log a message.

    Args:
        msg (str): message to log.
    """
    if raw_output:
        print(msg)
        return
    from rich.console import Console

    console = Console()
    console.print(formatting(msg))
