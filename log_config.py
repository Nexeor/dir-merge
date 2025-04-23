import logging

from pathlib import Path

import utils

BASE_LOG_PATH = "./results/logs/"


def setup_logging():
    log_path = Path(BASE_LOG_PATH) / Path(f"log-{utils.get_timestamp()}.txt")
    file_handler = logging.FileHandler(log_path, mode="w")
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    logging.basicConfig(level=logging.INFO, handlers=[file_handler])
    print(f"Logging to: {log_path}")
