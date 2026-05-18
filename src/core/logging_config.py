import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "sync_bridge.log"

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    LOG_DIR.mkdir(exist_ok=True)

    formatter = logging.Formatter(fmt=_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",      # rotaciona à meia-noite
        interval=1,           # a cada 1 dia
        backupCount=30,       # mantém os últimos 30 dias
        encoding="utf-8",
        utc=False,
    )
    # suffix "%Y-%m-%d" já é o padrão para when="midnight"
    # ex de arquivo rotacionado: sync_bridge.log.2026-05-16
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
