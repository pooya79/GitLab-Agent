import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from colorama import Fore, Style, init as colorama_init
from datetime import datetime

from core.config import settings

# Initialize colorama for Windows compatibility
colorama_init(autoreset=True)

# Create logs directory
LOG_DIR = Path(settings.log_dir)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Dynamic log file name with date
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"

# Color mapping for levels
LEVEL_COLORS = {
    "DEBUG": Fore.CYAN,
    "INFO": Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.MAGENTA,
}


class ColorFormatter(logging.Formatter):
    def format(self, record):
        log_color = LEVEL_COLORS.get(record.levelname, "")
        reset_color = Style.RESET_ALL
        log_fmt = (
            f"{Fore.WHITE}[%(asctime)s]{reset_color} "
            f"{log_color}[%(levelname)s]{reset_color} "
            f"{Fore.CYAN}(%(filename)s:%(lineno)d){reset_color} "
            f"%(message)s"
        )
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = "[%(asctime)s] [%(levelname)s] (%(filename)s:%(lineno)d) %(message)s"
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Log everything, handlers filter levels

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ColorFormatter())

    # File handler (rotates at 5MB, keeps 5 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(FileFormatter())

    # Clear old handlers (avoid duplicate logs if imported twice)
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
