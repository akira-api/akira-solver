import logging
import os
from typing import Optional

# Optional Windows ANSI support
try:
    import colorama  # type: ignore
    _HAS_COLORAMA = True
except Exception:
    colorama = None
    _HAS_COLORAMA = False


class ColoredFormatter(logging.Formatter):
    """Custom log formatter to apply distinct ANSI colors to log levels and message bodies."""
    
    # ANSI Color codes for log level labels
    COLOR_LABEL = {
        'DEBUG': '\u001b[90m',      # Bright Black / Gray
        'INFO': '\u001b[34m',       # Blue
        'WARNING': '\u001b[33m',    # Yellow
        'ERROR': '\u001b[31m',      # Red
        'CRITICAL': '\u001b[41m\u001b[97m', # Red Background, Bright White Text
    }
    
    # ANSI Color codes for the remaining message text after the label
    COLOR_MESSAGE = {
        'DEBUG': '\u001b[90m',      # Debug messages will also be gray
        # INFO, WARNING, ERROR, and CRITICAL leave this empty to use terminal default (white)
    }
    
    RESET = '\u001b[0m'

    def __init__(self, fmt: str, use_color: bool = True):
        super().__init__(fmt)
        # Allow colors on Windows only if colorama is available
        if os.name == 'nt':
            self.use_color = use_color and _HAS_COLORAMA
            if self.use_color and _HAS_COLORAMA:
                # Initialize colorama to enable ANSI on Windows
                if _HAS_COLORAMA and colorama is not None:
                    init_fn = getattr(colorama, 'init', None)
                    if callable(init_fn):
                        try:
                            init_fn()
                        except Exception:
                            pass
        else:
            self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        # Get standard formatted message string
        msg = super().format(record)
        
        if not self.use_color:
            # Still add prefix without color if disabled
            if record.name.startswith('core.solver'):
                return '[HTTPS] ' + msg
            return msg

        # Get specific colors for the label and trailing message text
        lbl_color = self.COLOR_LABEL.get(record.levelname, '')
        msg_color = self.COLOR_MESSAGE.get(record.levelname, '')

        # Format label with its color, then reset, and inject the message color right after
        colored_level = f"{lbl_color}{record.levelname}{self.RESET}{msg_color}"

        # Replace first occurrence of the plain level name and append RESET at the very end
        msg = msg.replace(f" {record.levelname} ", f" {colored_level} ", 1) + self.RESET

        # Distinguish https-related logs (from core.solver) with magenta prefix
        if record.name.startswith('core.solver'):
            prefix = '\u001b[35m[HTTPS]\u001b[0m '
            return prefix + msg

        return msg


def configure_logging(level: int = logging.INFO, use_color: Optional[bool] = None) -> None:
    """Configure root logging with colored output.

    - level: numeric logging level
    - use_color: force enabling/disabling colors (None = auto)
    """
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    stream = logging.StreamHandler()

    fmt = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    if use_color is None:
        use_color = True

    # If on Windows, only enable color if colorama is available
    enable_color = use_color and (os.name != 'nt' or _HAS_COLORAMA)
    if os.name == 'nt' and enable_color and _HAS_COLORAMA and colorama is not None:
        init_fn = getattr(colorama, 'init', None)
        if callable(init_fn):
            try:
                init_fn()
            except Exception:
                pass

    stream.setFormatter(ColoredFormatter(fmt, use_color=enable_color))
    root.addHandler(stream)
    root.setLevel(level)

    # Silence pydoll and websockets logs (only CRITICAL messages will appear)
    logging.getLogger('pydoll').setLevel(logging.CRITICAL)
    logging.getLogger('websockets').setLevel(logging.CRITICAL)
    logging.getLogger('websockets.client').setLevel(logging.CRITICAL)
