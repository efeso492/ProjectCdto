import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-8s] %(name)s: %(message)s"


def configurar_logger(
    name: str = "app",
    log_dir: str | Path | None = None,
    filename: str = "ATlogfile.log",
    level: int = logging.INFO,
    max_bytes: int = 10_000_000,
    backup_count: int = 3,
) -> logging.Logger:
    """
    Configura y devuelve un logger con salida a archivo rotativo y consola.
    Es idempotente: llamarla varias veces con el mismo `name` no duplica handlers.
    No modifica el root logger.
    """
    logger = logging.getLogger(name)

    if logger.handlers:  # ya configurado
        return logger

    base_dir = Path(log_dir) if log_dir else Path(__file__).resolve().parent / "logs"
    base_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        base_dir / filename,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False  # evita duplicados si el root logger tiene handlers

    return logger