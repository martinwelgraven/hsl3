"""Local implementation of the HomeServer's Syslog logger API."""

import logging
from logging.handlers import SysLogHandler


class Hsl3Logger(logging.Logger):
    """Syslog logger with the documented HSL logger level interface."""

    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    DISABLE = 100

    def __init__(self, name, host="127.0.0.1", port=65002, console=True,
                 level=logging.INFO):
        super().__init__(name, level)
        self.propagate = False

        if console:
            output = logging.StreamHandler()
            output.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
            self.addHandler(output)

    def set_level(self, level):
        """Set the minimum severity; NOTSET and DISABLE suppress all messages."""
        self.setLevel(level)

    def debug(self, msg, *args, **kwargs):
        """Log a DEBUG message."""
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        super().debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log an INFO message."""
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        super().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log a WARNING message."""
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        super().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log an ERROR message."""
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        super().error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log a CRITICAL message."""
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        super().critical(msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        """Log an ERROR message with the current exception traceback."""
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        super().exception(msg, *args, exc_info=exc_info, **kwargs)

    def isEnabledFor(self, level):
        return (
            self.level not in (self.NOTSET, self.DISABLE)
            and not self.disabled
            and self.manager.disable < level
            and level >= self.getEffectiveLevel()
        )
