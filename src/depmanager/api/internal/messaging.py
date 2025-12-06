"""
Messaging system
"""

import logging

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
    if level == 1:
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


def formatting(
    msg: str,
) -> str:
    """Format a message using rich formatting.

    Args:
        msg (str): message to format.

    Returns:
        str: formatted message.
    """
    # if text contains '[' not followed by ' ' add a space after it to avoid rich misinterpretation
    # e.g. "Package [Linux x86_64 gnu shared]" -> "Package [ Linux x86_64 gnu shared]"
    import re

    msg = re.sub(r"\[(?!\s)", "[ ", msg)
    # if text contains ']' not preceded by ' ' add a space before it to avoid rich misinterpretation
    # e.g. "Package [Linux x86_64 gnu shared]" -> "Package [Linux x86_64 gnu shared ]"
    msg = re.sub(r"(?<!\s)\]", " ]", msg)

    # color keywords ignoring case when searching for replacements but keeping original case in the message
    for keyword, color in keywords.items():
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        msg = pattern.sub(lambda m: f"[{color}]{m.group()}[/]", msg)

    # format 'default' meaning words starting with * and followed by alphanumeric characters
    default_pattern = re.compile(r"\*(\w+)")
    msg = default_pattern.sub(lambda m: f"[bold blue]*{m.group(1)}[/]", msg)

    # formatting date that can appear in the message as iso format to human-readable format
    date_pattern = re.compile(
        r"\b(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([+-]\d{2}:\d{2}|Z)?\b"
    )
    msg = date_pattern.sub(
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
