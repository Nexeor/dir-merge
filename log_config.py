import logging

from pathlib import Path

import utils

LOG_PATH = "./results/logs"


def setup_logging(logfile: str = LOG_PATH):
    timestamp = utils.get_timestamp()
    file_handler = logging.FileHandler(Path(f"{logfile}-{timestamp}"), mode="w")
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    logging.basicConfig(level=logging.INFO, handlers=[file_handler])
