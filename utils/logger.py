from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from config import APP_NAME, LOG_DIR, LOG_FORMAT


def setup_logger() -> logging.Logger:
    """初始化应用日志，控制台与文件同时输出。"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(APP_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    root_logger = setup_logger()
    if not name:
        return root_logger
    return root_logger.getChild(name)
