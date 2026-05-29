import logging
import os
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name if name else "bot")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(log_format)
    logger.addHandler(ch)

    # File
    log_file = os.path.join(os.getcwd(), "bot.log")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(log_format)
    logger.addHandler(fh)

    logger.propagate = False
    return logger
