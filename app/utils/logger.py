import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO

    project_root = Path(__file__).resolve().parents[2]

    log_file = project_root / "app.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%d.%m %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    if not debug:
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("aiogram").setLevel(logging.INFO)
        logging.getLogger("apscheduler").setLevel(logging.INFO)