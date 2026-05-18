import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "sync_bridge.log"


def _log_namer(default_name: str) -> str:
    """Renomeia arquivos rotacionados de 'sync_bridge.log.2026-05-17'
    para 'sync_bridge.2026-05-17.log'."""
    p = Path(default_name)
    # p.stem = 'sync_bridge.log', p.suffix = '.2026-05-17'
    date_suffix = p.suffix          # ex: .2026-05-17
    base = Path(p.stem)             # ex: sync_bridge.log -> stem=sync_bridge, suffix=.log
    return str(p.parent / f"{base.stem}{date_suffix}{base.suffix}")

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
    # ex de arquivo rotacionado: sync_bridge.2026-05-17.log
    file_handler.namer = _log_namer
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
